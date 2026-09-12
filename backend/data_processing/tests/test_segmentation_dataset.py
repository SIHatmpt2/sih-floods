"""Tests for preparing paired flood-segmentation training data."""

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from data_processing.segmentation_dataset import DatasetValidationError, prepare_dataset


class SegmentationDatasetTests(unittest.TestCase):
    @staticmethod
    def _write_image(path, value):
        Image.fromarray(np.full((8, 10, 3), value, dtype=np.uint8), mode="RGB").save(path)

    @staticmethod
    def _write_mask(path, values):
        Image.fromarray(np.asarray(values, dtype=np.uint8), mode="L").save(path)

    def test_prepare_dataset_pairs_normalizes_masks_and_splits_without_duplicate_leakage(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            images = root / "images"
            masks = root / "masks"
            output = root / "processed"
            images.mkdir()
            masks.mkdir()

            for index in range(4):
                self._write_image(images / f"scene-{index}.jpg", 40 + index)
                self._write_mask(masks / f"scene-{index}_mask.png", [[0, 1, 127, 255] * 2] * 8)

            (images / "scene-0-duplicate.jpg").write_bytes((images / "scene-0.jpg").read_bytes())
            self._write_mask(masks / "scene-0-duplicate_mask.png", [[0] * 8] * 8)

            summary = prepare_dataset(images, masks, output, seed=7)

            self.assertEqual(summary["samples"], 4)
            self.assertEqual(summary["duplicates_removed"], 1)
            self.assertEqual(summary["splits"], {"train": 2, "val": 1, "test": 1})

            processed_masks = list(output.glob("**/masks/*.png"))
            self.assertEqual(len(processed_masks), 4)
            self.assertTrue(set(np.unique(np.asarray(Image.open(processed_masks[0])))).issubset({0, 255}))

            metadata = [json.loads(line) for line in (output / "metadata.jsonl").read_text().splitlines()]
            self.assertEqual(len(metadata), 4)
            self.assertTrue(all(item["width"] == 10 and item["height"] == 8 for item in metadata))
            self.assertEqual({item["split"] for item in metadata}, {"train", "val", "test"})

    def test_prepare_dataset_fails_when_a_unique_image_has_no_mask(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            images = root / "images"
            masks = root / "masks"
            output = root / "processed"
            images.mkdir()
            masks.mkdir()

            self._write_image(images / "covered.jpg", 10)
            self._write_image(images / "missing.jpg", 20)
            self._write_mask(masks / "covered_mask.png", [[0] * 10] * 8)

            with self.assertRaisesRegex(DatasetValidationError, "missing.jpg"):
                prepare_dataset(images, masks, output)


if __name__ == "__main__":
    unittest.main()
