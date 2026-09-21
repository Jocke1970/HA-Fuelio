"""Synthetic test records only; no private Fuelio exports in the repository."""
from datetime import date
from decimal import Decimal
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cost_analytics_parser", ROOT / "custom_components/fuelio/parser.py")
parser = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parser
spec.loader.exec_module(parser)
from test_parser import sample_csv


class CostAnalyticsTests(unittest.TestCase):
    def fixture(self):
        csv = sample_csv()
        self.assertIn("## Costs\r\n", csv)
        csv = csv.replace("## Costs\r\n", "## CostCategories\r\nCostTypeID,Name,priority,color,guid,lastupdated\r\n7,Parkering,0,0,,\r\n8,Tvätt,0,0,,\r\n## Costs\r\n", 1)
        csv = csv.replace("Date,Cost,isTemplate,isIncome\r\n", "Date,Cost,isTemplate,isIncome,CostTypeID\r\n", 1)
        for before, after in (("2026-09-25 12:00,500,0,0", "2026-09-25 12:00,500,0,0,7"),
                              ("2026-09-15 12:00,200,0,0", "2026-09-15 12:00,200,0,0,7"),
                              ("2026-09-12 12:00,5000,1,0", "2026-09-12 12:00,5000,1,0,8"),
                              ("2026-09-12 12:00,100,0,1", "2026-09-12 12:00,100,0,1,8")):
            self.assertIn(before, csv)
            csv = csv.replace(before, after, 1)
        return csv

    def test_month_year_lifetime_and_category_join(self):
        result = parser.parse_backup(self.fixture(), today=date(2026, 9, 21))
        self.assertEqual(result.fuel_count_month, 1)
        self.assertEqual(result.fuel_count_year, 2)
        month = result.monthly_cost_history[0]
        self.assertEqual(month["month"], "2026-09")
        self.assertEqual(month["km"], 18)
        self.assertEqual(month["categories"], [{"name": "Parkering", "amount": 200}])
        self.assertEqual(month["fuel_per_logged_km"], round(1000 / 18, 3))
        self.assertEqual(month["total_per_logged_km"], round(1200 / 18, 3))
        year = result.yearly_cost_history[0]
        self.assertEqual(year["total"], 2000)
        self.assertEqual(year["km"], 20)
        self.assertEqual(result.fuel_cost_per_km_year, 90)
        self.assertEqual(result.total_cost_per_km_all, 100)
        self.assertEqual(list(result.all_cost_categories), [{"name": "Parkering", "amount": 200}])
        self.assertNotIn("CostTypeID", repr(result))

    def test_changed_fuel_price_updates_ratios_without_cached_value(self):
        original = parser.parse_backup(self.fixture(), today=date(2026, 9, 21))
        changed = parser.parse_backup(self.fixture().replace("2026-09-10 11:00,1000,50,1000,20,6", "2026-09-10 11:00,1000,50,1200,20,6"), today=date(2026, 9, 21))
        self.assertGreater(changed.fuel_cost_per_km_month, original.fuel_cost_per_km_month)
        self.assertGreater(changed.total_cost_per_km_all, original.total_cost_per_km_all)

    def test_zero_logged_km_produces_no_ratio(self):
        csv = self.fixture().replace(",18000,1800,20,", ",0,1800,20,").replace(",2000,360,5,", ",0,360,5,")
        result = parser.parse_backup(csv, today=date(2026, 9, 21))
        self.assertIsNone(result.fuel_cost_per_km_month)
        self.assertIsNone(result.total_cost_per_km_all)

    def test_missing_category_table_falls_back_to_uncategorized(self):
        result = parser.parse_backup(sample_csv(), today=date(2026, 9, 21))
        self.assertEqual(list(result.all_cost_categories), [{"name": "Okategoriserat", "amount": 200}])


if __name__ == "__main__":
    unittest.main()
