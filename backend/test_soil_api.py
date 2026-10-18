"""
Live Integration Test: Soil API against running local server.
Opt-in via RUN_LIVE_INTEGRATION_TESTS=1 or direct execution (python test_soil_api.py).
Safe for unittest discovery with zero import-time side effects.
"""
import os
import unittest
import requests

LIVE_INTEGRATION_ENABLED = os.getenv("RUN_LIVE_INTEGRATION_TESTS", "").lower() in ("1", "true", "yes")


@unittest.skipUnless(LIVE_INTEGRATION_ENABLED, "Live integration tests disabled by default (set RUN_LIVE_INTEGRATION_TESTS=1)")
class TestLiveSoilAPI(unittest.TestCase):
    """Explicitly opt-in integration tests against a running backend server."""

    def test_soil_coordinates(self):
        try:
            r = requests.get(
                'http://127.0.0.1:5000/api/soil/coords',
                params={'lat': '17.3850', 'lon': '78.4867'},
                timeout=10,
            )
            self.assertEqual(r.status_code, 200)
            data = r.json()
            self.assertTrue(data.get("ok"))
            self.assertIn("nitrogen", data)
        except requests.exceptions.RequestException as e:
            self.skipTest(f"Live server at http://127.0.0.1:5000 is not reachable: {e}")


def _run_cli_demo():
    print("=== LIVE INTEGRATION TEST: Soil API (http://127.0.0.1:5000) ===")
    try:
        r = requests.get(
            'http://127.0.0.1:5000/api/soil/coords',
            params={'lat': '17.3850', 'lon': '78.4867'},
            timeout=10,
        )
        data = r.json()
        print(f"Status: {r.status_code}")
        print(f"ok: {data.get('ok')}")
        print(f"fallback: {data.get('fallback')}")
        print(f"source_name: {data.get('source_name')}")
        print(f"Nitrogen: {data.get('nitrogen')}")
    except Exception as e:
        print(f"Error connecting to backend: {e}")


if __name__ == '__main__':
    _run_cli_demo()
