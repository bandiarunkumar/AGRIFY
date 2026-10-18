"""Fast unit tests for Crop Doctor upload validation and path safety."""

import os
import tempfile
import unittest

from upload_validation import validate_image_upload, unique_upload_path


class TestUploadValidation(unittest.TestCase):
    def test_accepts_supported_extensions_case_insensitively(self):
        for filename in ("leaf.jpg", "leaf.JPEG", "leaf.png", "leaf.webp"):
            with self.subTest(filename=filename):
                extension, error = validate_image_upload(filename, 100, 1024)
                self.assertIsNone(error)
                self.assertEqual(extension, os.path.splitext(filename)[1].lower())

    def test_rejects_missing_filename_and_unsupported_extensions(self):
        for filename in (None, "", "leaf.pdf", "leaf.png.exe"):
            with self.subTest(filename=filename):
                extension, error = validate_image_upload(filename, 100, 1024)
                self.assertIsNone(extension)
                self.assertTrue(error)

    def test_rejects_oversized_image(self):
        extension, error = validate_image_upload("leaf.png", 1025, 1024)
        self.assertIsNone(extension)
        self.assertIn("maximum upload", error)

    def test_generated_path_ignores_client_supplied_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            first = unique_upload_path(directory, ".jpg")
            second = unique_upload_path(directory, ".jpg")
        self.assertNotEqual(first, second)
        self.assertEqual(os.path.dirname(first), directory)
        self.assertEqual(os.path.splitext(first)[1], ".jpg")


if __name__ == "__main__":
    unittest.main(verbosity=2)
