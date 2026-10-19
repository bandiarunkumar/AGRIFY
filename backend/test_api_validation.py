"""Regression tests ensuring malformed inputs fail before provider I/O."""

import unittest
import os
from unittest.mock import patch

import api
import etl.weather_etl as etl_weather_etl


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

    def test_oversized_payload_rejected_with_413(self):
        # 2.5 MB dummy body exceeding the 2 MB limit
        large_body = "x" * (2500 * 1024)
        response = self.client.post(
            "/api/predict/crop",
            data=large_body,
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 413)
        data = response.get_json()
        self.assertIn("exceeds the maximum permitted limit", data["error"])


class TestRateLimiting(unittest.TestCase):
    """Regression tests for the API rate-limiting layer."""

    def setUp(self):
        self.client = api.app.test_client()
        # Start every test with a clean in-memory quota store so tests
        # are hermetic (the limiter is bound to the shared api.app).
        try:
            api.limiter.storage.reset()
        except Exception:
            pass

    def test_health_check_exempt_from_rate_limit(self):
        # /api/health is @limiter.exempt: rapid traffic must not be throttled.
        for _ in range(150):
            response = self.client.get("/api/health")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()["status"], "healthy")

    def test_rate_limited_handler_returns_consistent_json_429(self):
        with api.app.app_context():
            result = api.rate_limited(None)
        # Flask error handlers return (response, status_code) when invoked directly.
        self.assertEqual(result[1], 429)
        data = result[0].get_json()
        self.assertEqual(data["code"], 429)
        self.assertIn("Too many requests", data["error"])

    def test_rate_limit_key_ignores_spoofed_forwarded_for(self):
        # Quota key must derive from the TCP peer address, never from
        # client-supplied X-Forwarded-For (spoofable bypass vector).
        with api.app.test_request_context(
            "/api/health", headers={"X-Forwarded-For": "1.2.3.4"}
        ):
            key = api._rate_limit_key()
            # The spoofed header must NOT influence the quota key.
            self.assertNotEqual(key, "1.2.3.4")

    def test_env_limit_reads_configuration(self):
        self.assertEqual(
            api._env_limit("RATELIMIT_DEFAULT", "120 per minute"),
            "120 per minute",
        )
        with patch.dict(os.environ, {"RATELIMIT_ASSISTANT": "10 per minute"}):
            self.assertEqual(
                api._env_limit("RATELIMIT_ASSISTANT", "30 per minute"),
                "10 per minute",
            )

    def test_assistant_query_not_rate_limited_under_normal_load(self):
        for _ in range(5):
            response = self.client.post(
                "/api/assistant/query",
                json={"query": "hello", "language": "en"},
            )
            self.assertNotEqual(response.status_code, 429)

    def test_assistant_query_exceeding_limit_returns_429(self):
        # Assistant route is limited to 30/minute; the 31st request is 429.
        seen_429 = False
        for _ in range(32):
            response = self.client.post(
                "/api/assistant/query",
                json={"query": "hello", "language": "en"},
            )
            if response.status_code == 429:
                seen_429 = True
                data = response.get_json()
                self.assertEqual(data["code"], 429)
                self.assertIn("Too many requests", data["error"])
                break
        self.assertTrue(seen_429, "Expected a 429 after exceeding the limit")


class TestWeatherKeyMissingRegression(unittest.TestCase):
    """Regression tests: missing OPENWEATHERMAP_API_KEY must never fabricate weather."""

    def setUp(self):
        self.client = api.app.test_client()

    def test_weather_by_coords_missing_key_returns_error_not_fake_data(self):
        # Patch OWM_KEY to empty (simulates key absent from env).
        with patch.object(etl_weather_etl, "OWM_KEY", ""):
            result = etl_weather_etl.get_weather_by_coords(17.4, 78.5)
        self.assertNotEqual(result.get("ok"), True)
        self.assertIn("OPENWEATHERMAP_API_KEY not configured", result.get("error", ""))
        # No temperature, humidity, or other fabricated fields present
        self.assertNotIn("temperature", result)
        self.assertNotIn("humidity", result)

    def test_weather_by_city_missing_key_returns_error(self):
        with patch.object(etl_weather_etl, "OWM_KEY", ""):
            result = etl_weather_etl.get_weather_by_city("Hyderabad")
        self.assertNotEqual(result.get("ok"), True)
        self.assertIn("OPENWEATHERMAP_API_KEY not configured", result.get("error", ""))

    def test_weather_endpoint_missing_key_returns_error_response(self):
        # Patch api.get_weather_by_coords (bound at api.py import time).
        # Endpoint returns 400 when weather result contains "error".
        with patch.object(api, "get_weather_by_coords", return_value={"error": "OPENWEATHERMAP_API_KEY not configured in .env"}):
            response = self.client.get("/api/weather/coords?lat=17.4&lon=78.5")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertNotEqual(data.get("ok"), True)
        self.assertIn("OPENWEATHERMAP_API_KEY not configured", data.get("error", ""))


class TestSoilInputsZeroDeficiencyRegression(unittest.TestCase):
    """Regression tests: soil N=0 and K=1 trigger deficiency flags, not defaults."""

    def setUp(self):
        self.client = api.app.test_client()
        self.base_payload = {
            "latitude": 17.4,
            "longitude": 78.5,
            "area_acres": 2.0,
            "season": "Kharif",
            "region": "Telangana",
            "soil_type": "Loamy",
            "soil_ph": 6.5,
            "soil_moisture": 40,
            "organic_carbon": 0.8,
            "irrigation": "Canal",
            "previous_crop": "Wheat",
            "previous_fertilizer": "Moderate",
            "yield_last": 3000.0,
        }

    def test_nitrogen_zero_triggers_deficiency_flag(self):
        payload = dict(self.base_payload)
        payload["N"] = 0
        payload["P"] = 40
        payload["K"] = 30
        with patch.object(api, "reverse_geocode", return_value={"district": "Hyderabad", "state": "Telangana"}), \
             patch.object(api, "get_weather_by_coords", return_value={"ok": True, "temperature": 28, "humidity": 65, "weather_desc": "Clear", "data_quality": "live"}), \
             patch.object(api, "get_forecast_by_coords", return_value={"ok": True, "forecast": [], "advisory": []}), \
             patch.object(api, "get_soil_by_coords", return_value={"ok": True, "N": 0, "P": 40, "K": 30, "ph": 6.5, "moisture_pct": 40, "data_quality": "user_entered"}):
            response = self.client.post("/api/farm/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        fert = data.get("fertilizer_recommendation", {})
        deficiencies = fert.get("nutrient_deficiency_summary", [])
        # Nitrogen=0 must be flagged as low
        n_def = [d for d in deficiencies if d.get("nutrient") == "Nitrogen (N)"]
        self.assertTrue(len(n_def) > 0, "Nitrogen=0 must trigger a deficiency flag")
        self.assertEqual(n_def[0].get("level"), "low")

    def test_potassium_one_triggers_deficiency_flag(self):
        payload = dict(self.base_payload)
        payload["N"] = 50
        payload["P"] = 40
        payload["K"] = 1
        with patch.object(api, "reverse_geocode", return_value={"district": "Hyderabad", "state": "Telangana"}), \
             patch.object(api, "get_weather_by_coords", return_value={"ok": True, "temperature": 28, "humidity": 65, "weather_desc": "Clear", "data_quality": "live"}), \
             patch.object(api, "get_forecast_by_coords", return_value={"ok": True, "forecast": [], "advisory": []}), \
             patch.object(api, "get_soil_by_coords", return_value={"ok": True, "N": 50, "P": 40, "K": 1, "ph": 6.5, "moisture_pct": 40, "data_quality": "user_entered"}):
            response = self.client.post("/api/farm/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        fert = data.get("fertilizer_recommendation", {})
        deficiencies = fert.get("nutrient_deficiency_summary", [])
        # Potassium=1 must be flagged as low
        k_def = [d for d in deficiencies if d.get("nutrient") == "Potassium (K)"]
        self.assertTrue(len(k_def) > 0, "Potassium=1 must trigger a deficiency flag")
        self.assertEqual(k_def[0].get("level"), "low")

    def test_soil_data_quality_marked_estimated_for_user_entered(self):
        """User-entered soil values must be marked as estimated, not live."""
        payload = dict(self.base_payload)
        payload["N"] = 90
        payload["P"] = 42
        payload["K"] = 43
        with patch.object(api, "reverse_geocode", return_value={"district": "Hyderabad", "state": "Telangana"}), \
             patch.object(api, "get_weather_by_coords", return_value={"ok": True, "temperature": 28, "humidity": 65, "weather_desc": "Clear", "data_quality": "live"}), \
             patch.object(api, "get_forecast_by_coords", return_value={"ok": True, "forecast": [], "advisory": []}), \
             patch.object(api, "get_soil_by_coords", return_value={"ok": True, "N": 90, "P": 42, "K": 43, "ph": 6.5, "moisture_pct": 40, "data_quality": "user_entered"}):
            response = self.client.post("/api/farm/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        crop_rec = data.get("crop_recommendation", {})
        self.assertEqual(crop_rec.get("data_quality"), "estimated")
        self.assertIn("modeled or farmer-entered", crop_rec.get("data_quality_note", ""))


class TestProfitCalculationIllustrativeRegression(unittest.TestCase):
    """Regression tests: profit calculation uses illustrative base yield, not soil-adjusted values."""

    def setUp(self):
        self.client = api.app.test_client()
        self.base_payload = {
            "latitude": 17.4,
            "longitude": 78.5,
            "area_acres": 1.0,
            "season": "Kharif",
            "region": "Telangana",
            "soil_type": "Loamy",
            "soil_ph": 6.5,
            "soil_moisture": 40,
            "organic_carbon": 0.8,
            "irrigation": "Canal",
            "previous_crop": "Wheat",
            "previous_fertilizer": "Moderate",
            "yield_last": 3000.0,
        }

    def test_profit_independent_of_nitrogen_level(self):
        """Net profit estimate must not change when soil nitrogen changes (illustrative calc)."""
        payload_low_n = dict(self.base_payload)
        payload_low_n["N"] = 0
        payload_low_n["P"] = 40
        payload_low_n["K"] = 30

        payload_high_n = dict(self.base_payload)
        payload_high_n["N"] = 100
        payload_high_n["P"] = 40
        payload_high_n["K"] = 30

        with patch.object(api, "reverse_geocode", return_value={"district": "Hyderabad", "state": "Telangana"}), \
             patch.object(api, "get_weather_by_coords", return_value={"ok": True, "temperature": 28, "humidity": 65, "weather_desc": "Clear", "data_quality": "live"}), \
             patch.object(api, "get_forecast_by_coords", return_value={"ok": True, "forecast": [], "advisory": []}), \
             patch.object(api, "get_soil_by_coords", return_value={"ok": True, "N": 90, "P": 42, "K": 43, "ph": 6.5, "moisture_pct": 40, "data_quality": "user_entered"}):
            resp_low = self.client.post("/api/farm/analyze", json=payload_low_n)
            resp_high = self.client.post("/api/farm/analyze", json=payload_high_n)

        self.assertEqual(resp_low.status_code, 200)
        self.assertEqual(resp_high.status_code, 200)
        data_low = resp_low.get_json()
        data_high = resp_high.get_json()
        # Top crop profit estimate must be identical (same crop, same base_yield, same area)
        profit_low = data_low["crop_recommendation"]["top_3"][0]["net_profit_estimated"]
        profit_high = data_high["crop_recommendation"]["top_3"][0]["net_profit_estimated"]
        self.assertEqual(profit_low, profit_high, "Profit estimate must not vary with soil nitrogen (illustrative calc)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
