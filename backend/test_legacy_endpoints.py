"""
Regression and safety tests for migrated legacy endpoints:
- /api/predict/crop (delegated to ICAR agronomic feasibility engine)
- /api/predict/fertilizer (guarded against chemical dosage hallucination; 503 unavailable)
"""
import unittest
import math
import api


class TestLegacyCropPrediction(unittest.TestCase):
    def setUp(self):
        self.client = api.app.test_client()
        self.valid_payload = {
            "N": 50,
            "P": 40,
            "K": 30,
            "temperature": 27.5,
            "humidity": 65,
            "ph": 6.8,
            "rainfall": 150,
        }

    def test_valid_crop_prediction_returns_200_and_expected_contract(self):
        """Valid inputs return HTTP 200 with best_crop, alternatives, and input_summary."""
        response = self.client.post("/api/predict/crop", json=self.valid_payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertEqual(data.get("status"), "success")
        self.assertIn("best_crop", data)
        self.assertIn("alternatives", data)
        self.assertIn("input_summary", data)
        self.assertIn("crop", data["best_crop"])
        self.assertIn("confidence", data["best_crop"])
        self.assertIn("profit", data["best_crop"])
        self.assertIn("pests", data["best_crop"])
        self.assertEqual(data.get("engine"), "agronomic_feasibility_v3")

    def test_crop_prediction_missing_fields_returns_400(self):
        """Missing required fields return 400 with an informative error."""
        incomplete = dict(self.valid_payload)
        del incomplete["rainfall"]
        response = self.client.post("/api/predict/crop", json=incomplete)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("error", data)
        self.assertIn("rainfall", data["error"])

    def test_crop_prediction_invalid_data_types_returns_400(self):
        """Non-numeric values, booleans, NaN, and Inf return 400."""
        cases = [
            {"N": "not-a-number"},
            {"P": True},
            {"K": None},
            {"temperature": float("nan")},
            {"rainfall": float("inf")},
            {"ph": [6.5]},
        ]
        for override in cases:
            payload = dict(self.valid_payload)
            payload.update(override)
            with self.subTest(override=override):
                response = self.client.post("/api/predict/crop", json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.get_json())

    def test_crop_prediction_empty_payload_returns_400(self):
        """Empty JSON payload returns 400."""
        response = self.client.post("/api/predict/crop", json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())


class TestLegacyFertilizerPrediction(unittest.TestCase):
    def setUp(self):
        self.client = api.app.test_client()
        self.valid_payload = {
            "soil_type": "Clay",
            "soil_ph": 6.8,
            "soil_moisture": 45.0,
            "organic_carbon": 0.8,
            "electrical_conductivity": 0.5,
            "N": 50,
            "P": 40,
            "K": 30,
            "temperature": 28.0,
            "humidity": 65.0,
            "rainfall": 120.0,
            "crop_type": "rice",
            "growth_stage": "Vegetative",
            "season": "Kharif",
            "irrigation": "Canal",
            "previous_crop": "blackgram",
            "region": "South",
            "fertilizer_usage": "Moderate",
            "yield_last": 3000.0,
        }

    def test_valid_fertilizer_request_returns_503_and_safety_advisory(self):
        """
        Valid requests return HTTP 503 without chemical dosage hallucination,
        instructing the farmer to check Farm Analyzer or consult local KVK.
        """
        response = self.client.post("/api/predict/fertilizer", json=self.valid_payload)
        self.assertEqual(response.status_code, 503)
        data = response.get_json()

        self.assertEqual(data.get("status"), "unavailable")
        self.assertEqual(data.get("service"), "predict_fertilizer")
        self.assertIn("error", data)
        self.assertIn("advisory", data)
        # Agronomic Safety Guardrail Verification:
        # Response MUST NOT fabricate chemical quantities or dosages
        self.assertNotIn("kg/ha", str(data))
        self.assertNotIn("dosage", data)
        self.assertIn("KVK", data["advisory"])

    def test_fertilizer_missing_fields_returns_400(self):
        """Missing required fields return 400."""
        incomplete = dict(self.valid_payload)
        del incomplete["soil_type"]
        response = self.client.post("/api/predict/fertilizer", json=incomplete)
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_fertilizer_invalid_types_returns_400(self):
        """Invalid non-numeric types return 400."""
        payload = dict(self.valid_payload)
        payload["soil_ph"] = "acidic"
        response = self.client.post("/api/predict/fertilizer", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())


if __name__ == "__main__":
    unittest.main()
