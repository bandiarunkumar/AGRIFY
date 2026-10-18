"""
Crop Doctor Inference and Endpoint Verification Suite
Tests the real TensorFlow model, image decoding, multipart upload,
validation, and localized response generation.
"""

import io
import unittest
import numpy as np
import tensorflow as tf
from app import app, MAX_IMAGE_BYTES, CLASS_NAMES, TREATMENTS


class TestCropDoctorInference(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

        # Generate a valid 224x224 RGB JPEG image using TensorFlow
        # Greenish pattern simulating leaf pixels
        green_leaf = np.zeros((224, 224, 3), dtype=np.uint8)
        green_leaf[:, :, 1] = 160  # Green channel
        green_leaf[:, :, 0] = 40   # Red channel
        green_leaf[:, :, 2] = 30   # Blue channel
        cls.valid_jpeg_bytes = tf.io.encode_jpeg(tf.constant(green_leaf)).numpy()

    def test_missing_file_returns_400(self):
        res = self.client.post("/api/predict", data={})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("Image file is required", data.get("error", ""))

    def test_invalid_extension_returns_400(self):
        data = {
            "file": (io.BytesIO(b"fake executable content"), "malicious.exe")
        }
        res = self.client.post("/api/predict", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 400)
        body = res.get_json()
        self.assertIn("Unsupported image format", body.get("error", ""))

    def test_corrupted_image_bytes_returns_400(self):
        data = {
            "file": (io.BytesIO(b"not a real jpeg but named like one"), "leaf.jpg")
        }
        res = self.client.post("/api/predict", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 400)
        body = res.get_json()
        self.assertIn("not a readable image", body.get("error", ""))

    def test_oversized_upload_rejected(self):
        # 6MB dummy buffer exceeding 5MB limit
        large_bytes = b"0" * (MAX_IMAGE_BYTES + 1024)
        data = {
            "file": (io.BytesIO(large_bytes), "large_leaf.jpg")
        }
        res = self.client.post("/api/predict", data=data, content_type="multipart/form-data")
        self.assertIn(res.status_code, [400, 413])

    def test_valid_image_inference_english(self):
        data = {
            "file": (io.BytesIO(self.valid_jpeg_bytes), "potato_leaf.jpg"),
            "language": "en"
        }
        res = self.client.post("/api/predict", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()

        self.assertEqual(body.get("status"), "success")
        self.assertIn("is_recognized", body)

        if body["is_recognized"]:
            self.assertIn("is_healthy", body)
            self.assertIn("diagnosis", body)
            diag = body["diagnosis"]
            self.assertIn("name", diag)
            self.assertIn("med", diag)
            self.assertIn("plan", diag)
            self.assertIsInstance(body.get("all_scores"), list)
            self.assertEqual(len(body["all_scores"]), 3)
            # Verify probabilities sum close to 100%
            total_conf = sum(score["conf"] for score in body["all_scores"])
            self.assertAlmostEqual(total_conf, 100.0, delta=1.5)
        else:
            self.assertIn("Image not recognized", body.get("error", ""))

    def test_valid_image_inference_telugu(self):
        data = {
            "file": (io.BytesIO(self.valid_jpeg_bytes), "potato_leaf.jpg"),
            "language": "te"
        }
        res = self.client.post("/api/predict", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(body.get("status"), "success")
        if body.get("is_recognized"):
            diag = body["diagnosis"]
            # Diagnosis name in Telugu should contain non-ASCII characters
            self.assertTrue(any(ord(c) > 127 for c in diag["name"]))

    def test_valid_image_inference_hindi(self):
        data = {
            "file": (io.BytesIO(self.valid_jpeg_bytes), "potato_leaf.jpg"),
            "language": "hi"
        }
        res = self.client.post("/api/predict", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(body.get("status"), "success")
        if body.get("is_recognized"):
            diag = body["diagnosis"]
            # Diagnosis name in Hindi should contain Devanagari unicode
            self.assertTrue(any(ord(c) > 127 for c in diag["name"]))

    def test_unsupported_language_falls_back_to_english(self):
        data = {
            "file": (io.BytesIO(self.valid_jpeg_bytes), "potato_leaf.jpg"),
            "language": "es"  # Spanish not supported -> en fallback
        }
        res = self.client.post("/api/predict", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(body.get("status"), "success")
        if body.get("is_recognized"):
            diag = body["diagnosis"]
            en_names = [TREATMENTS[c]["en"]["name"] for c in CLASS_NAMES]
            self.assertIn(diag["name"], en_names)

    def test_unrecognized_leaf_image_returns_false(self):
        # A blended pattern where max confidence is < 0.65 threshold
        raw = tf.io.read_file("../frontend/public/ai-mascot.png")
        img = tf.cast(tf.image.resize(tf.io.decode_image(raw, channels=3, expand_animations=False), (224, 224)), tf.float32)
        blend = tf.cast(0.30 * img + 0.70 * 128.0, tf.uint8)
        blend_jpg = tf.io.encode_jpeg(blend).numpy()

        data = {
            "file": (io.BytesIO(blend_jpg), "unsupported_leaf.jpg"),
            "language": "en"
        }
        res = self.client.post("/api/predict", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(body.get("status"), "success")
        self.assertFalse(body.get("is_recognized"))
        self.assertIn("not recognized", body.get("error", "").lower())


if __name__ == "__main__":
    unittest.main()
