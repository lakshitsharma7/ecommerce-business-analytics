"""Focused tests for database-backed dashboard measures and slicers."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard"))

import server


class DashboardDataTests(unittest.TestCase):
    def test_repeat_customer_definition_matches_warehouse(self) -> None:
        data = server.get_dashboard_data()
        metrics = data["metrics"]
        self.assertEqual(metrics["customers_with_orders"], 7986)
        self.assertEqual(metrics["one_time_customers"], 95)
        self.assertEqual(metrics["repeat_customers"], 7891)
        self.assertAlmostEqual(metrics["repeat_customer_rate_pct"], 98.8104, places=3)

    def test_financial_totals_match_warehouse(self) -> None:
        metrics = server.get_dashboard_data()["metrics"]
        self.assertAlmostEqual(metrics["gross_sales"], 77_161_511.63, places=2)
        self.assertAlmostEqual(metrics["net_sales"], 71_564_192.67, places=2)
        self.assertAlmostEqual(metrics["line_profit"], 18_531_707.01, places=2)

    def test_year_and_region_filters_reduce_scope(self) -> None:
        all_data = server.get_dashboard_data()
        filtered = server.get_dashboard_data({"year": "2025", "region": "Europe"})
        self.assertLess(filtered["metrics"]["net_sales"], all_data["metrics"]["net_sales"])
        self.assertAlmostEqual(
            sum(row["net_sales"] for row in filtered["monthly"]),
            filtered["metrics"]["net_sales"],
            places=2,
        )

    def test_bad_filter_value_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            server.get_dashboard_data({"region": "' OR 1=1 --"})


if __name__ == "__main__":
    unittest.main()
