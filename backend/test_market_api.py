"""
Live Integration Test: Market Prices API against running local server.
Opt-in via RUN_LIVE_INTEGRATION_TESTS=1 or direct execution (python test_market_api.py).
Safe for unittest discovery with zero import-time side effects.
"""
import os
import unittest
import requests

LIVE_INTEGRATION_ENABLED = os.getenv("RUN_LIVE_INTEGRATION_TESTS", "").lower() in ("1", "true", "yes")


@unittest.skipUnless(LIVE_INTEGRATION_ENABLED, "Live integration tests disabled by default (set RUN_LIVE_INTEGRATION_TESTS=1)")
class TestLiveMarketAPI(unittest.TestCase):
    """Explicitly opt-in integration tests against a running backend server."""

    def test_tomato_telangana(self):
        try:
            r = requests.post(
                'http://127.0.0.1:5000/api/market-prices',
                json={'crop': 'tomato', 'state': 'Telangana'},
                timeout=10,
            )
            self.assertEqual(r.status_code, 200)
            data = r.json()
            self.assertIn("markets", data)
        except requests.exceptions.RequestException as e:
            self.skipTest(f"Live server at http://127.0.0.1:5000 is not reachable: {e}")

    def test_tomato_hyderabad_district(self):
        try:
            r = requests.post(
                'http://127.0.0.1:5000/api/market-prices',
                json={'crop': 'tomato', 'state': 'Telangana', 'district': 'Hyderabad'},
                timeout=10,
            )
            self.assertEqual(r.status_code, 200)
            data = r.json()
            self.assertIn("markets", data)
        except requests.exceptions.RequestException as e:
            self.skipTest(f"Live server at http://127.0.0.1:5000 is not reachable: {e}")

    def test_cotton_telangana(self):
        try:
            r = requests.post(
                'http://127.0.0.1:5000/api/market-prices',
                json={'crop': 'cotton', 'state': 'Telangana'},
                timeout=10,
            )
            self.assertEqual(r.status_code, 200)
            data = r.json()
            self.assertIn("markets", data)
        except requests.exceptions.RequestException as e:
            self.skipTest(f"Live server at http://127.0.0.1:5000 is not reachable: {e}")


def _run_cli_demo():
    print("=== LIVE INTEGRATION TEST: Market API (http://127.0.0.1:5000) ===")
    for crop, state, district in [
        ('tomato', 'Telangana', None),
        ('tomato', 'Telangana', 'Hyderabad'),
        ('cotton', 'Telangana', None),
    ]:
        payload = {'crop': crop, 'state': state}
        if district:
            payload['district'] = district
        label = f"{crop} in {state}" + (f" ({district})" if district else "")
        print(f"\n--- Testing: {label} ---")
        try:
            r = requests.post('http://127.0.0.1:5000/api/market-prices', json=payload, timeout=10)
            data = r.json()
            print(f"Status: {r.status_code}")
            print(f"Markets returned: {len(data.get('markets', []))}")
            print(f"Avg price/kg: ₹{data.get('avg_price_per_kg')}/kg")
        except Exception as e:
            print(f"Error connecting to backend: {e}")


if __name__ == '__main__':
    _run_cli_demo()
