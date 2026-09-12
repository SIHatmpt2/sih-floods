"""Tests for preparing paired flood-segmentation training data."""

import json

import numpy as np
from PIL import Image
import pytest

from data_processing.segmentation_dataset import (
    DatasetValidationError,
    prepare_dataset,
)


def _write_image(path, value):
    Image.fromarray(np.full((8, 10, 3), value, dtype=np.uint8), mode="RGB").save(path)


def _write_mask(path, values):
    Image.fromarray(np.asarray(values, dtype=np.uint8), mode="L").save(path)


def test_prepare_dataset_pairs_normalizes_masks_and_splits_without_duplicate_leakage(tmp_path):
    images = tmp_path / "images"
    masks = tmp_path / "masks"
    output = tmp_path / "processed"
    images.mkdir()
    masks.mkdir()

    for index in range(4):
        _write_image(images / f"scene-{index}.jpg", 40 + index)
        _write_mask(masks / f"scene-{index}_mask.png", [[0, 1, 127, 255] * 2] * 8)

    # Same bytes as scene-0: it must not become a second training sample.
    (images / "scene-0-duplicate.jpg").write_bytes((images / "scene-0.jpg").read_bytes())
    _write_mask(masks / "scene-0-duplicate_mask.png", [[0] * 8] * 8)

    summary = prepare_dataset(images, masks, output, seed=7)

    assert summary["samples"] == 4
    assert summary["duplicates_removed"] == 1
    assert summary["splits"] == {"train": 2, "val": 1, "test": 1}

    processed_masks = list(output.glob("**/masks/*.png"))
    assert len(processed_masks) == 4
    assert set(np.unique(np.asarray(Image.open(processed_masks[0])))).issubset({0, 255})

    metadata = [json.loads(line) for line in (output / "metadata.jsonl").read_text().splitlines()]
    assert len(metadata) == 4
    assert all(item["width"] == 10 and item["height"] == 8 for item in metadata)
    assert {item["split"] for item in metadata} == {"train", "val", "test"}


def test_prepare_dataset_fails_when_a_unique_image_has_no_mask(tmp_path):
    images = tmp_path / "images"
    masks = tmp_path / "masks"
    output = tmp_path / "processed"
    images.mkdir()
    masks.mkdir()

    _write_image(images / "covered.jpg", 10)
    _write_image(images / "missing.jpg", 20)
    _write_mask(masks / "covered_mask.png", [[0] * 10] * 8)

    with pytest.raises(DatasetValidationError, match="missing.jpg"):
        prepare_dataset(images, masks, output)
