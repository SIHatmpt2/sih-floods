"""Prepare paired flood images and masks for segmentation training.

The raw dataset stays untouched. The processor validates image/mask pairs,
rejects conflicting labels for byte-identical images, optionally rejects empty
masks, removes byte-identical duplicate images, converts images to RGB PNGs
and masks to binary PNGs, then creates deterministic train/validation/test
splits.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Iterable

from PIL import Image

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
SPLIT_RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}
BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE_DIR = BACKEND_ROOT / "apps/risk/data/raw/images"
DEFAULT_MASK_DIR = BACKEND_ROOT / "apps/risk/data/raw/masks"
DEFAULT_OUTPUT_DIR = BACKEND_ROOT / "apps/risk/data/processed/segmentation"


class DatasetValidationError(ValueError):
    """Raised when the raw segmentation dataset cannot be prepared safely."""


def _content_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalized_key(filename: str) -> str:
    stem = Path(filename).stem.lower()
    stem = re.sub(r"(?:\s*\(\d+\))+$", "", stem)
    return stem


def _iter_images(directory: Path) -> Iterable[Path]:
    if not directory.exists():
        raise DatasetValidationError(f"Image directory does not exist: {directory}")
    return sorted(
        path for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    )


def _load_manifest(mask_dir: Path) -> dict[str, Path]:
    manifest_path = mask_dir / "manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        records = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DatasetValidationError(f"Invalid mask manifest: {manifest_path}") from exc
    if not isinstance(records, list):
        raise DatasetValidationError("Mask manifest must contain a list of records")

    mapping: dict[str, Path] = {}
    for record in records:
        if not isinstance(record, dict):
            raise DatasetValidationError("Mask manifest contains an invalid record")
        source = record.get("source_image")
        mask = record.get("mask")
        if not source or not mask:
            raise DatasetValidationError("Mask manifest contains an incomplete record")
        mask_path = mask_dir / mask
        if not mask_path.is_file():
            raise DatasetValidationError(f"Manifest references missing mask: {mask}")
        key = _normalized_key(source)
        previous = mapping.get(key)
        if previous is not None and previous.name != mask_path.name:
            raise DatasetValidationError(
                f"Ambiguous masks for normalized image key '{key}': "
                f"{previous.name} and {mask_path.name}"
            )
        mapping[key] = mask_path
    return mapping


def _build_mask_lookup(mask_dir: Path) -> tuple[dict[str, Path], dict[str, Path]]:
    if not mask_dir.exists():
        raise DatasetValidationError(f"Mask directory does not exist: {mask_dir}")
    exact: dict[str, Path] = {}
    normalized: dict[str, Path] = {}
    for path in mask_dir.iterdir():
        if not path.is_file() or path.suffix.lower() != ".png" or not path.name.endswith("_mask.png"):
            continue
        exact_key = path.stem[:-5].lower()
        previous_exact = exact.get(exact_key)
        if previous_exact is not None and previous_exact.name != path.name:
            raise DatasetValidationError(
                f"Ambiguous exact masks for image key '{exact_key}': "
                f"{previous_exact.name} and {path.name}"
            )
        exact[exact_key] = path

        key = _normalized_key(path.name[:-9])
        previous = normalized.get(key)
        if previous is not None and previous.name != path.name:
            raise DatasetValidationError(
                f"Ambiguous masks for normalized image key '{key}': "
                f"{previous.name} and {path.name}"
            )
        normalized[key] = path

    manifest_mapping = _load_manifest(mask_dir)
    for key, manifest_mask in manifest_mapping.items():
        previous = normalized.get(key)
        if previous is not None and previous.name != manifest_mask.name:
            raise DatasetValidationError(
                f"Mask manifest conflicts with mask files for normalized image key '{key}': "
                f"{previous.name} and {manifest_mask.name}"
            )
        normalized[key] = manifest_mask
    return exact, normalized


def _find_mask(image: Path, exact: dict[str, Path], normalized: dict[str, Path]) -> Path | None:
    return exact.get(image.stem.lower()) or normalized.get(_normalized_key(image.name))


def _mask_signature(path: Path) -> tuple[tuple[int, int], str, bool]:
    """Return dimensions, pixel hash and whether the mask is completely empty."""
    try:
        with Image.open(path) as source:
            mask = source.convert("L")
            pixels = mask.tobytes()
            return mask.size, hashlib.sha256(pixels).hexdigest(), not any(pixels)
    except OSError as exc:
        raise DatasetValidationError(f"Could not read mask: {path.name}") from exc


def _validate_duplicate_masks(pairs: list[tuple[Path, Path]]) -> None:
    """Reject byte-identical images whose labels disagree."""
    by_image_hash: dict[str, list[tuple[Path, Path]]] = {}
    for image, mask in pairs:
        image_hash = _content_hash(image)
        by_image_hash.setdefault(image_hash, []).append((image, mask))

    for image_hash, duplicate_pairs in by_image_hash.items():
        if len(duplicate_pairs) < 2:
            continue
        signatures = {
            _mask_signature(mask)[1]
            for _, mask in duplicate_pairs
        }
        if len(signatures) > 1:
            names = ", ".join(image.name for image, _ in duplicate_pairs)
            raise DatasetValidationError(
                f"Found conflicting masks for byte-identical images: {names}"
            )


def _deduplicate(images: list[Path]) -> tuple[list[Path], dict[str, list[str]]]:
    by_hash: dict[str, Path] = {}
    duplicates: dict[str, list[str]] = {}
    unique: list[Path] = []
    for image in images:
        digest = _content_hash(image)
        if digest in by_hash:
            duplicates.setdefault(digest, [by_hash[digest].name]).append(image.name)
            continue
        by_hash[digest] = image
        unique.append(image)
    return unique, duplicates


def _split_samples(images: list[Path], seed: int) -> dict[str, list[Path]]:
    ordered = sorted(
        images,
        key=lambda path: hashlib.sha256(f"{seed}:{_content_hash(path)}".encode()).hexdigest(),
    )
    n = len(ordered)
    if n == 1:
        counts = {"train": 1, "val": 0, "test": 0}
    elif n == 2:
        counts = {"train": 1, "val": 1, "test": 0}
    else:
        val_count = max(1, round(n * SPLIT_RATIOS["val"]))
        test_count = max(1, round(n * SPLIT_RATIOS["test"]))
        counts = {
            "train": n - val_count - test_count,
            "val": val_count,
            "test": test_count,
        }

    train_end = counts["train"]
    val_end = train_end + counts["val"]
    return {
        "train": ordered[:train_end],
        "val": ordered[train_end:val_end],
        "test": ordered[val_end:],
    }


def _prepare_one(image: Path, mask: Path, split_dir: Path, output_root: Path) -> dict:
    try:
        with Image.open(image) as source:
            source_rgb = source.convert("RGB")
            width, height = source_rgb.size
            image_dir = split_dir / "images"
            mask_dir = split_dir / "masks"
            image_dir.mkdir(parents=True, exist_ok=True)
            mask_dir.mkdir(parents=True, exist_ok=True)
            output_image = image_dir / f"{image.stem}.png"
            source_rgb.save(output_image, format="PNG", optimize=True)

        with Image.open(mask) as source_mask:
            mask_gray = source_mask.convert("L")
            if mask_gray.size != (width, height):
                raise DatasetValidationError(
                    f"Dimension mismatch for {image.name}: image={width}x{height}, "
                    f"mask={mask_gray.width}x{mask_gray.height}"
                )
            binary = mask_gray.point(lambda value: 255 if value > 0 else 0, mode="1").convert("L")
            output_mask = mask_dir / f"{image.stem}.png"
            binary.save(output_mask, format="PNG", optimize=True)
    except OSError as exc:
        raise DatasetValidationError(f"Could not read {image.name} or {mask.name}") from exc

    return {
        "image": str(output_image.relative_to(output_root)).replace("\\", "/"),
        "mask": str(output_mask.relative_to(output_root)).replace("\\", "/"),
        "source_image": image.name,
        "source_mask": mask.name,
        "width": width,
        "height": height,
        "image_sha256": _content_hash(image),
        "mask_sha256": _content_hash(mask),
    }


def prepare_dataset(
    image_dir: str | Path,
    mask_dir: str | Path,
    output_dir: str | Path,
    *,
    seed: int = 42,
    allow_empty_masks: bool = False,
) -> dict:
    """Validate, pair, deduplicate and split a flood segmentation dataset."""
    image_dir = Path(image_dir)
    mask_dir = Path(mask_dir)
    output_dir = Path(output_dir)

    images = list(_iter_images(image_dir))
    if not images:
        raise DatasetValidationError(f"No supported images found in {image_dir}")

    exact_masks, normalized_masks = _build_mask_lookup(mask_dir)

    pairs: list[tuple[Path, Path]] = []
    missing: list[str] = []
    for image in images:
        mask = _find_mask(image, exact_masks, normalized_masks)
        if mask is None:
            missing.append(image.name)
        else:
            pairs.append((image, mask))
    if missing:
        raise DatasetValidationError(
            "Missing masks for images: " + ", ".join(sorted(missing))
        )

    _validate_duplicate_masks(pairs)

    unique_images, duplicates = _deduplicate(images)
    pair_by_image = {image: mask for image, mask in pairs}

    empty_masks: list[str] = []
    for image in unique_images:
        mask = pair_by_image[image]
        _, _, is_empty = _mask_signature(mask)
        if is_empty:
            empty_masks.append(mask.name)

    if empty_masks and not allow_empty_masks:
        raise DatasetValidationError(
            "Found empty masks; review annotations before training: "
            + ", ".join(sorted(empty_masks))
        )

    split_paths = _split_samples(unique_images, seed)

    if output_dir.exists():
        shutil.rmtree(output_dir)
    for split in SPLIT_RATIOS:
        (output_dir / split / "images").mkdir(parents=True, exist_ok=True)
        (output_dir / split / "masks").mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    for split, split_images in split_paths.items():
        for image in split_images:
            record = _prepare_one(
                image, pair_by_image[image], output_dir / split, output_dir
            )
            record["split"] = split
            records.append(record)

    records.sort(key=lambda record: record["source_image"])
    (output_dir / "metadata.jsonl").write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    summary = {
        "samples": len(records),
        "source_images": len(images),
        "duplicates_removed": len(images) - len(unique_images),
        "empty_masks": sorted(empty_masks),
        "splits": {split: len(items) for split, items in split_paths.items()},
        "seed": seed,
        "image_format": "PNG/RGB",
        "mask_format": "PNG/L/0-or-255",
        "duplicates": duplicates,
    }
    (output_dir / "dataset_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", type=Path, default=DEFAULT_IMAGE_DIR)
    parser.add_argument("--masks", type=Path, default=DEFAULT_MASK_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--allow-empty-masks",
        action="store_true",
        help="Allow completely black masks, but report them in dataset_summary.json.",
    )
    args = parser.parse_args()
    summary = prepare_dataset(
        args.images,
        args.masks,
        args.output,
        seed=args.seed,
        allow_empty_masks=args.allow_empty_masks,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
