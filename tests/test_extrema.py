"""New aggregate regression tests using fabricated Fuelio records only."""
from __future__ import annotations

from datetime import date
from pathlib import Path
import re
import unittest

from test_parser import parse_backup, sample_csv


class FuelioExtremaTests(unittest.TestCase):
    def test_price_ties_use_latest_date_and_months_are_aggregated(self):
        snapshot = parse_backup(sample_csv(), today=date(2026, 9, 21))
        self.assertEqual(snapshot.fuel_price_min_year, 20)
        self.assertEqual(snapshot.fuel_price_max_year, 20)
        self.assertEqual(snapshot.fuel_price_min_all, 20)
        self.assertEqual(snapshot.fuel_price_max_all, 20)
        self.assertEqual(snapshot.record_dates["fuel_price_min_year"], "2026-09-10")
        self.assertEqual(snapshot.record_dates["fuel_price_max_all"], "2026-09-10")
        self.assertEqual(snapshot.consumption_min_year, 6)
        self.assertEqual(snapshot.consumption_max_all, 6)
        self.assertEqual({k: snapshot.monthly_cost_history[0][k] for k in ("month", "fuel", "other", "total")}, {"month": "2026-09", "fuel": 1000.0, "other": 200.0, "total": 1200.0})
        self.assertEqual({k: snapshot.monthly_cost_history[1][k] for k in ("month", "fuel", "other", "total")}, {"month": "2026-08", "fuel": 800.0, "other": 0.0, "total": 800.0})
        self.assertFalse(snapshot.monthly_history_truncated)
        self.assertNotIn("5000", str(snapshot.monthly_cost_history))

    def test_calendar_year_and_lifetime_do_not_mix(self):
        csv = sample_csv(latest_consumption="", earlier_consumption="5.7")
        csv = csv.replace("2026-08-01 11:00,900,40,800,20,5.7", "2025-08-01 11:00,900,40,800,19,5.7")
        self.assertIn("2025-08-01", csv)
        snapshot = parse_backup(csv, today=date(2026, 9, 21))
        self.assertEqual(snapshot.fuel_price_min_year, 20)
        self.assertEqual(snapshot.fuel_price_max_year, 20)
        self.assertEqual(snapshot.fuel_price_min_all, 19)
        self.assertEqual(snapshot.fuel_price_max_all, 20)
        self.assertEqual(snapshot.record_dates["fuel_price_min_all"], "2025-08-01")
        self.assertIsNone(snapshot.consumption_min_year)
        self.assertIsNone(snapshot.consumption_max_year)
        self.assertNotIn("consumption_min_year", snapshot.record_dates)
        self.assertEqual(snapshot.consumption_min_all, 5.7)
        self.assertEqual(snapshot.last_reported_consumption, 5.7)

    def test_price_uses_cost_per_litre_if_explicit_price_missing(self):
        csv = sample_csv().replace("2026-09-10 11:00,1000,50,1000,20,6", "2026-09-10 11:00,1000,50,900,,6")
        self.assertIn("900,,6", csv)
        snapshot = parse_backup(csv, today=date(2026, 9, 21))
        self.assertEqual(snapshot.fuel_price_min_year, 18)
        self.assertEqual(snapshot.fuel_price_max_year, 20)
        self.assertEqual(snapshot.fuel_cost, 1700)
        self.assertEqual(snapshot.monthly_cost_history[0]["total"], 1100)

    def test_future_fuel_records_never_influence_extrema(self):
        csv = sample_csv().replace("2026-09-10 11:00,1000,50,1000,20,6", "2026-10-10 11:00,1000,50,1000,99,99")
        snapshot = parse_backup(csv, today=date(2026, 9, 21))
        self.assertEqual(snapshot.fuel_price_min_all, 20)
        self.assertEqual(snapshot.fuel_price_max_all, 20)
        self.assertIsNone(snapshot.consumption_min_all)
        self.assertEqual(snapshot.monthly_cost_history[0]["fuel"], 0)

    def test_no_positive_records_are_unknown(self):
        csv = sample_csv(latest_consumption="", earlier_consumption="")
        csv = csv.replace("1000,50,1000,20,", "1000,50,0,0,")
        csv = csv.replace("900,40,800,20,", "900,40,0,0,")
        snapshot = parse_backup(csv, today=date(2026, 9, 21))
        self.assertIsNone(snapshot.fuel_price_min_year)
        self.assertIsNone(snapshot.fuel_price_max_all)
        self.assertIsNone(snapshot.consumption_min_all)
        self.assertEqual(snapshot.record_dates, {})

    def test_monthly_attributes_are_capped_and_privacy_safe(self):
        lines = []
        for n in range(125):
            year = 2010 + n // 12
            month = n % 12 + 1
            lines.append(f"{year:04d}-{month:02d}-01 12:00,1,0,0")
        csv = sample_csv()
        newline = "\r\n" if "\r\n" in csv else "\n"
        marker = "## TripLog" + newline
        self.assertIn(marker, csv)
        csv = csv.replace(marker, newline.join(lines) + newline + marker)
        snapshot = parse_backup(csv, today=date(2026, 9, 21))
        self.assertTrue(snapshot.monthly_history_truncated)
        self.assertEqual(len(snapshot.monthly_cost_history), 120)
        self.assertEqual(snapshot.monthly_cost_history[0]["month"], "2026-09")
        self.assertEqual(snapshot.monthly_cost_history[-1]["month"], "2010-08")
        self.assertTrue(all({"month", "fuel", "other", "total"}.issubset(month) for month in snapshot.monthly_cost_history))
        self.assertNotIn("Test vehicle", repr(snapshot))

    def test_existing_ids_unchanged_and_nine_new_entities(self):
        path = Path(__file__).resolve().parents[1] / "custom_components" / "fuelio" / "sensor.py"
        source = path.read_text(encoding="utf-8")
        keys = re.findall(r'FuelioSensorDescription\(key="([^"]+)"', source)
        self.assertEqual(len(keys), 42)
        self.assertEqual(len(keys), len(set(keys)))
        self.assertIn('f"{entry.entry_id}_{description.key}"', source)
        self.assertIn('identifiers={(DOMAIN, entry.entry_id)}', source)


if __name__ == "__main__":
    unittest.main()
