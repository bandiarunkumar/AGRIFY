"""Regression tests ensuring malformed inputs fail before provider I/O."""

import unittest
from unittest.mock import patch

import api


class TestCoordinateValidation(unittest.TestCase):
    def setUp(self):
        self.client = api.app.test_client()

    def test_all_coordinate_endpoints_reject_invalid_values_without_provider_calls(self):
        cases = [
            ("/api/weather/coords?lat=91&lon=0", "get_weather_by_coords"),
            ("/api/forecast/coords?lat=nan&lon=0", "get_forecast_by_coords"),
            ("/api/soil/coords?lat=0&lon=inf", "get_soil_by_coords"),
            ("/api/geocode/reverse?lat=0&lon=181", "reverse_geocode"),
            ("/api/alerts?lat=-91&lon=0", "get_weather_by_coords"),
        ]
        for path, provider in cases:
            with self.subTest(path=path), patch.object(api, provider) as mock_provider:
                response = self.client.get(path)
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.get_json())
                mock_provider.assert_not_called()

    def test_farm_analysis_rejects_bad_coordinates_area_and_season(self):
        for payload in (
            {"latitude": 91, "longitude": 0},
            {"latitude": 17, "longitude": 78, "area_acres": "large"},
            {"latitude": 17, "longitude": 78, "area_acres": float("inf")},
            {"latitude": 17, "longitude": 78, "season": ["Kharif"]},
            [17, 78],
        ):
            with self.subTest(payload=payload), patch.object(api, "reverse_geocode") as geocode:
                response = self.client.post("/api/farm/analyze", json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.get_json())
                geocode.assert_not_called()

    def test_crop_prediction_wrong_type_is_a_client_error(self):
        response = self.client.post("/api/predict/crop", json={
            "N": [], "P": 20, "K": 20, "temperature": 22,
            "humidity": 60, "ph": 6, "rainfall": 100,
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_market_api_preserves_unavailable_provenance_without_crashing(self):
        unavailable = {
            "ok": True, "fallback": True, "commodity": "Tomato", "records": [],
            "total_markets_reporting": 0, "avg_price_per_kg": 0,
            "min_price_per_kg": 0, "max_price_per_kg": 0,
            "avg_price_per_quintal": 0, "best_market": None,
            "data_quality": "unavailable", "data_quality_note": "No live prices are shown.",
            "source_name": "unavailable", "fetch_timestamp": "2026-10-17T00:00:00+00:00",
        }
        with patch.object(api, "fetch_market_prices", return_value=unavailable):
            response = self.client.post("/api/market-prices", json={"crop": "tomato"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["data_quality"], "unavailable")
        self.assertTrue(data["is_fallback"])
        self.assertEqual(data["markets"], [])
        self.assertEqual(data["best_market"], "")

    def test_market_rejects_wrong_type_filters_before_provider_call(self):
        with patch.object(api, "fetch_market_prices") as fetch:
            response = self.client.post("/api/market-prices", json={"crop": [], "state": "Telangana"})
        self.assertEqual(response.status_code, 400)
        fetch.assert_not_called()

    def test_state_market_rejects_bad_limit_before_provider_call(self):
        for limit in ("bad", "0", "101"):
            with self.subTest(limit=limit), patch.object(api, "fetch_markets_for_state") as fetch:
                response = self.client.get(f"/api/market-prices/state?state=Telangana&limit={limit}")
                self.assertEqual(response.status_code, 400)
                fetch.assert_not_called()

    def test_chat_and_voice_queries_reject_wrong_types_and_oversized_input(self):
        chat_cases = ({"message": []}, {"message": "x" * 4001})
        for payload in chat_cases:
            with self.subTest(payload_type=type(payload.get("message")).__name__, length=len(payload.get("message", ""))):
                response = self.client.post("/api/chat", json=payload)
                self.assertEqual(response.status_code, 400)

        for payload in ({"query": []}, {"query": "x" * 4001}, {"query": "hello", "context": []}):
            with self.subTest(payload=payload):
                response = self.client.post("/api/assistant/query", json=payload)
                self.assertEqual(response.status_code, 400)

    def test_alert_endpoint_does_not_label_provider_failure_as_live_or_all_clear(self):
        with patch.object(api, "get_weather_by_coords", return_value={"ok": False, "error": "unavailable"}), \
             patch.object(api, "get_forecast_by_coords", return_value={"ok": False, "error": "unavailable"}), \
             patch.object(api, "get_soil_by_coords", return_value={"ok": False, "error": "unavailable"}), \
             patch.object(api, "generate_farm_alerts", return_value=[]):
            response = self.client.get("/api/alerts?lat=17.4&lon=78.5")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["alerts"], [])
        self.assertEqual(data["data_quality"], "unavailable")
        self.assertIn("not an all-clear", data["data_quality_note"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
