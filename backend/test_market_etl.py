"""Regression tests for explicit provenance on unavailable market data."""

import unittest
from unittest.mock import patch

from etl import market_etl


class TestUnavailableMarketData(unittest.TestCase):
    def setUp(self):
        market_etl._market_cache.clear()

    def tearDown(self):
        market_etl._market_cache.clear()

    def test_live_api_failure_does_not_return_synthetic_mandi_rows(self):
        with patch.object(market_etl, "_try_live_api", return_value=None):
            result = market_etl.fetch_market_prices("tomato", "Telangana")

        self.assertTrue(result["ok"])
        self.assertTrue(result["fallback"])
        self.assertEqual(result["data_quality"], "unavailable")
        self.assertEqual(result["source_name"], "unavailable")
        self.assertEqual(result["records"], [])
        self.assertEqual(result["total_markets_reporting"], 0)
        self.assertIn("No live prices", result["data_quality_note"])

    def test_unknown_commodity_has_no_fabricated_reference_price(self):
        result = market_etl._bare_fallback("unlisted_crop", "Telangana")
        self.assertEqual(result["data_quality"], "unavailable")
        self.assertEqual(result["avg_price_per_kg"], 0)
        self.assertIsNone(result["best_market"])
        self.assertEqual(result["records"], [])

    def test_state_api_failure_does_not_return_generated_market_rows(self):
        with patch.object(market_etl, "_get_api_keys", return_value=[]):
            result = market_etl.fetch_markets_for_state("Telangana")
        self.assertTrue(result["fallback"])
        self.assertEqual(result["data_quality"], "unavailable")
        self.assertEqual(result["records"], [])
        self.assertEqual(result["total"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
