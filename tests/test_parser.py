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


def sample_csv(*, metric: bool = True, malformed: bool = False,
               latest_consumption: str = "6", earlier_consumption: str = "") -> str:
    out = StringIO()
    writer = csv.writer(out)

    def section(name, header, *records):
        writer.writerow([f"## {name}"])
        writer.writerow(header)
        writer.writerows(records)

    section("Vehicle", ["Name", "DistUnit", "FuelUnit", "Tank1Capacity"], ["Test vehicle", "0" if metric else "1", "0", "60"])
    section("Log", ["Data", "Odo (km)", "Fuel (litres)", "Full", "Price (optional)", "VolumePrice", "l/100km (optional)", "TankNumber"],
            ["2026-09-10 11:00", "1000", "50", "1", "1000", "20", latest_consumption, "1"],
            ["2026-08-01 11:00", "900", "40", "1", "800", "20", earlier_consumption, "1"])
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

    def test_private_vehicle_name_is_not_retained(self):
        private_name = "PRIVATE-PLATE-XYZ"
        backup = sample_csv().replace("Test vehicle", private_name)
        snapshot = parse_backup(backup, today=date(2026, 9, 21))
        self.assertEqual(snapshot.vehicle_name, "Fuelio vehicle")
        self.assertNotIn(private_name, repr(snapshot))
        flow_source = (parser_path.parent / "config_flow.py").read_text(encoding="utf-8")
        self.assertIn('title="Fuelio vehicle"', flow_source)
        self.assertNotIn("snapshot.vehicle_name", flow_source)

    def test_consumption_falls_back_to_last_actual_report(self):
        snapshot = parse_backup(sample_csv(latest_consumption="", earlier_consumption="5.7"),
                                today=date(2026, 9, 21))
        self.assertEqual(snapshot.last_reported_consumption, 5.7)
        self.assertEqual(snapshot.last_fillup_date, date(2026, 9, 10))

    def test_consumption_stays_missing_when_no_report_exists(self):
        snapshot = parse_backup(sample_csv(latest_consumption="", earlier_consumption=""),
                                today=date(2026, 9, 21))
        self.assertIsNone(snapshot.last_reported_consumption)

    def test_range_forecast_from_latest_full_tank(self):
        snapshot = parse_backup(
            sample_csv(latest_consumption="6", earlier_consumption="5.8"),
            today=date(2026, 9, 21),
        )
        self.assertEqual(snapshot.distance_since_last_fillup_km, 28)
        self.assertAlmostEqual(snapshot.estimated_fuel_remaining_l, 58.35, places=2)
        self.assertAlmostEqual(snapshot.estimated_range_remaining_km, 988.9, places=1)
        self.assertIsNotNone(snapshot.estimated_days_to_next_fillup)
        self.assertIsNotNone(snapshot.estimated_next_fillup_date)
        self.assertEqual(snapshot.fuel_forecast["confidence"], "normal")
        self.assertEqual(snapshot.fuel_forecast["calibration_full_fillup_date"], "2026-09-10")
        self.assertEqual(snapshot.fuel_forecast["consumption_samples"], 2)

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
            loaded = load_snapshot(str(archive), date(2026, 9, 21))
            self.assertEqual(loaded.trip_count, 2)
            self.assertIsNotNone(loaded.last_app_sync)
            self.assertIsNotNone(loaded.last_app_sync.tzinfo)
            with ZipFile(archive, "a") as z:
                z.writestr("other.csv", sample_csv())
            with self.assertRaisesRegex(ValueError, "one unencrypted"):
                load_snapshot(str(archive))

    def test_replaced_zip_is_reread_and_missing_file_raises(self):
        with TemporaryDirectory() as directory:
            archive = Path(directory) / "synthetic.zip"
            with ZipFile(archive, "w") as z:
                z.writestr("export.csv", sample_csv(latest_consumption="6"))
            self.assertEqual(load_snapshot(str(archive), date(2026, 9, 21)).last_reported_consumption, 6)
            with ZipFile(archive, "w") as z:
                z.writestr("export.csv", sample_csv(latest_consumption="7.1"))
            self.assertEqual(load_snapshot(str(archive), date(2026, 9, 21)).last_reported_consumption, 7.1)
            archive.unlink()
            with self.assertRaises(FileNotFoundError):
                load_snapshot(str(archive), date(2026, 9, 21))

    def test_invalid_row_length(self):
        with self.assertRaisesRegex(ValueError, "incorrect number"):
            parse_backup(sample_csv() + "orphan,row\n")


if __name__ == "__main__":
    unittest.main()
