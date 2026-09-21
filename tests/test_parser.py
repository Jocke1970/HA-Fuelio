"""Synthetic fixtures only. Never commit real vehicle backups."""
from __future__ import annotations

import csv
from datetime import date
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import sys
import unittest
from zipfile import ZipFile

# Import pure parser directly: package __init__.py requires Home Assistant.
parser_path = Path(__file__).resolve().parents[1] / "custom_components" / "fuelio" / "parser.py"
spec = importlib.util.spec_from_file_location("fuelio_parser_under_test", parser_path)
parser = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parser
spec.loader.exec_module(parser)
load_snapshot, parse_backup = parser.load_snapshot, parser.parse_backup


def sample_csv(*, metric: bool = True, malformed: bool = False) -> str:
    out = StringIO()
    writer = csv.writer(out)

    def section(name, header, *records):
        writer.writerow([f"## {name}"])
        writer.writerow(header)
        writer.writerows(records)

    section("Vehicle", ["Name", "DistUnit", "FuelUnit"], ["Test vehicle", "0" if metric else "1", "0"])
    section("Log", ["Data", "Odo (km)", "Fuel (litres)", "Price (optional)", "VolumePrice", "l/100km (optional)"],
            ["2026-09-10 11:00", "1000", "50", "1000", "20", "6"],
            ["2026-08-01 11:00", "900", "40", "800", "20", ""])
    section("Costs", ["Date", "Cost", "isTemplate", "isIncome"],
            ["2026-09-25 12:00", "500", "0", "0"],
            ["2026-09-15 12:00", "200", "0", "0"],
            ["2026-09-12 12:00", "5000", "1", "0"],
            ["2026-09-12 12:00", "100", "0", "1"])
    section("TripLog", ["EndDate", "TripDist", "TripDuration", "TripCost", "StartOdo", "EndOdo"],
            ["2026-09-18 12:00", "18000" if not malformed else "NaN", "1800", "20", "1010", "1028"],
            ["2026-08-18 12:00", "2000", "360", "5", "900", "902"])
    return out.getvalue()


class FuelioParserTests(unittest.TestCase):
    def test_summary_and_future_cost_exclusion(self):
        s = parse_backup(sample_csv(), today=date(2026, 9, 21))
        self.assertEqual(s.trip_count, 2)
        self.assertEqual(s.trip_distance_km, 20)
        self.assertEqual(s.monthly_trip_distance_km, 18)
        self.assertEqual(s.trip_duration_hours, 0.6)
        self.assertEqual(s.estimated_trip_cost, 25)
        self.assertEqual(s.fuel_count, 2)
        self.assertEqual(s.fuel_litres, 90)
        self.assertEqual(s.fuel_cost, 1800)
        self.assertEqual(s.monthly_fuel_cost, 1000)
        self.assertEqual(s.expense_count, 2)
        self.assertEqual(s.other_expenses, 200)
        self.assertEqual(s.monthly_other_expenses, 200)
        self.assertEqual(s.upcoming_expense_count, 1)
        self.assertEqual(s.total_actual_cost, 2000)
        self.assertEqual(s.latest_odometer_km, 1028)
        self.assertEqual(s.last_reported_consumption, 6)
        self.assertEqual(s.last_trip_date, date(2026, 9, 18))
        self.assertFalse(hasattr(s, "StartLat"))
        self.assertFalse(hasattr(s, "Plate"))

    def test_reject_nonmetric(self):
        with self.assertRaisesRegex(ValueError, "metric"):
            parse_backup(sample_csv(metric=False))

    def test_reject_nan(self):
        with self.assertRaisesRegex(ValueError, "Non-finite"):
            parse_backup(sample_csv(malformed=True))

    def test_zip_loader_and_multiple_csv_rejected(self):
        with TemporaryDirectory() as directory:
            archive = Path(directory) / "synthetic.zip"
            with ZipFile(archive, "w") as z:
                z.writestr("export.csv", sample_csv())
            self.assertEqual(load_snapshot(str(archive), date(2026, 9, 21)).trip_count, 2)
            with ZipFile(archive, "a") as z:
                z.writestr("other.csv", sample_csv())
            with self.assertRaisesRegex(ValueError, "one unencrypted"):
                load_snapshot(str(archive))

    def test_invalid_row_length(self):
        with self.assertRaisesRegex(ValueError, "incorrect number"):
            parse_backup(sample_csv() + "orphan,row\n")


if __name__ == "__main__":
    unittest.main()
