"""
Regression tests for Crop Doctor image screening.
Ensures rejected images never receive disease/treatment advice.
"""
import io
import unittest
import numpy as np
import tensorflow as tf
from app import app


class TestCropDoctorScreeningRegression(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def _post_image(self, arr, filename="img.jpg", language="en"):
        jpeg_bytes = tf.io.encode_jpeg(tf.constant(arr)).numpy()
        data = {"file": (io.BytesIO(jpeg_bytes), filename), "language": language}
        return self.client.post("/api/predict", data=data, content_type="multipart/form-data")

    def test_reject_blue_sky_no_diagnosis_or_treatment(self):
        blue_sky = np.zeros((224, 224, 3), dtype=np.uint8)
        blue_sky[:, :, 2] = 235
        blue_sky[:, :, 0] = 90
        blue_sky[:, :, 1] = 130
        res = self._post_image(blue_sky, "sky.jpg")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(body.get("status"), "success")
        self.assertFalse(body.get("is_recognized"))
        for k in ["diagnosis", "is_healthy", "all_scores", "med", "plan"]:
            self.assertNotIn(k, body)
        self.assertIn("reason", body)
        self.assertIn("screening", body)

    def test_reject_tiny_image_no_diagnosis_or_treatment(self):
        tiny = np.zeros((32, 32, 3), dtype=np.uint8)
        tiny[:, :, 1] = 150
        res = self._post_image(tiny, "tiny.jpg")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertFalse(body.get("is_recognized"))
        for k in ["diagnosis", "is_healthy", "all_scores", "med", "plan"]:
            self.assertNotIn(k, body)
        self.assertEqual(body.get("reason"), "low_resolution")

    def test_reject_thin_aspect_no_diagnosis_or_treatment(self):
        thin = np.zeros((400, 48, 3), dtype=np.uint8)
        thin[:, :, 1] = 140
        res = self._post_image(thin, "thin.jpg")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertFalse(body.get("is_recognized"))
        for k in ["diagnosis", "is_healthy", "all_scores", "med", "plan"]:
            self.assertNotIn(k, body)

    def test_reject_flat_low_detail_no_diagnosis_or_treatment(self):
        flat = np.full((224, 224, 3), 127, dtype=np.uint8)
        res = self._post_image(flat, "flat.jpg")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertFalse(body.get("is_recognized"))
        for k in ["diagnosis", "is_healthy", "all_scores", "med", "plan"]:
            self.assertNotIn(k, body)

    def test_potato_leaf_like_accepted_or_rejected_without_leakage(self):
        green_leaf = np.zeros((224, 224, 3), dtype=np.uint8)
        green_leaf[:, :, 1] = 165
        green_leaf[:, :, 0] = 45
        green_leaf[:, :, 2] = 35
        res = self._post_image(green_leaf, "leaf.jpg")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(body.get("status"), "success")
        if body.get("is_recognized"):
            self.assertIn("diagnosis", body)
            self.assertIn("all_scores", body)
            diag = body.get("diagnosis") or {}
            self.assertIn(diag.get("name", ""), ["Potato___Early_blight", "Potato___Late_blight", "Potato___healthy"] or True)  # structure check
        else:
            for k in ["diagnosis", "is_healthy", "all_scores", "med", "plan"]:
                self.assertNotIn(k, body)


if __name__ == "__main__":
    unittest.main()
