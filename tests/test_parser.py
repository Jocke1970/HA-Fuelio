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
apply_range_calibration = parser.apply_range_calibration
range_calibration_consumption = parser.range_calibration_consumption


def sample_csv(*, metric: bool = True, malformed: bool = False,
               latest_consumption: str = "6", earlier_consumption: str = "") -> str:
    out = StringIO()
    writer = csv.writer(out)

    def section(name, header, *records):
        writer.writerow([f"## {name}"])
        writer.writerow(header)
        writer.writerows(records)

    section("Vehicle", ["Name", "DistUnit", "FuelUnit"], ["Test vehicle", "0" if metric else "1", "0"])
    section("Log", ["Data", "Odo (km)", "Fuel (litres)", "Price (optional)", "VolumePrice", "l/100km (optional)"],
            ["2026-09-10 11:00", "1000", "50", "1000", "20", latest_consumption],
            ["2026-08-01 11:00", "900", "40", "800", "20", earlier_consumption])
    section("Costs", ["Date", "Cost", "isTemplate", "isIncome"],
            ["2026-09-25 12:00", "500", "0", "0"],
            ["2026-09-15 12:00", "200", "0", "0"],
            ["2026-09-12 12:00", "5000", "1", "0"],
            ["2026-09-12 12:00", "100", "0", "1"])
    section("TripLog", ["EndDate", "TripDist", "TripDuration", "TripCost", "StartOdo", "EndOdo"],
            ["2026-09-18 12:00", "18000" if not malformed else "NaN", "1800", "20", "1010", "1028"],
            ["2026-08-18 12:00", "2000", "360", "5", "900", "902"])
    return out.getvalue()


def forecast_csv(*, extra_log_rows: tuple[tuple[str, ...], ...] = ()) -> str:
    out = StringIO()
    writer = csv.writer(out)

    def section(name, header, *records):
        writer.writerow([f"## {name}"])
        writer.writerow(header)
        writer.writerows(records)

    section("Vehicle", ["Name", "DistUnit", "FuelUnit", "Tank1Capacity"],
            ["Test vehicle", "0", "0", "60"])
    section("Log",
            ["Data", "Odo (km)", "Fuel (litres)", "Full", "Price (optional)",
             "VolumePrice", "l/100km (optional)", "TankNumber"],
            ["2026-09-10 11:00", "1000", "50", "1", "1000", "20", "6", "1"],
            ["2026-08-01 11:00", "900", "40", "1", "800", "20", "5.8", "1"],
            *extra_log_rows)
    section("Costs", ["Date", "Cost", "isTemplate", "isIncome"])
    section("TripLog",
            ["EndDate", "TripDist", "TripDuration", "TripCost", "StartOdo", "EndOdo"],
            ["2026-09-18 12:00", "18000", "1800", "20", "1010", "1028"],
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
        self.assertIn('title="Fuelio"', flow_source)
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
        snapshot = parse_backup(forecast_csv(), today=date(2026, 9, 21))
        self.assertEqual(snapshot.distance_since_last_fillup_km, 28)
        self.assertAlmostEqual(snapshot.estimated_fuel_remaining_l, 58.35, places=2)
        self.assertAlmostEqual(snapshot.estimated_range_remaining_km, 988.9, places=1)
        self.assertIsNotNone(snapshot.estimated_days_to_next_fillup)
        self.assertIsNotNone(snapshot.estimated_next_fillup_date)
        self.assertEqual(snapshot.fuel_forecast["confidence"], "normal")
        self.assertEqual(snapshot.fuel_forecast["calibration_full_fillup_date"], "2026-09-10")
        self.assertEqual(snapshot.fuel_forecast["consumption_samples"], 2)

    def test_latest_primary_fillup_marker_ignores_historical_additions_but_changes_on_new_fillup(self):
        base = parse_backup(forecast_csv(), today=date(2026, 9, 21))
        base_marker = base.fuel_forecast["latest_primary_fillup_marker"]
        self.assertIsInstance(base_marker, str)
        self.assertTrue(base_marker)

        historical = parse_backup(
            forecast_csv(extra_log_rows=(
                ("2026-07-01 11:00", "800", "35", "1", "700", "20", "5.7", "1"),
            )),
            today=date(2026, 9, 21),
        )
        self.assertEqual(
            historical.fuel_forecast["latest_primary_fillup_marker"],
            base_marker,
        )

        newer = parse_backup(
            forecast_csv(extra_log_rows=(
                ("2026-09-20 11:00", "1035", "20", "0", "400", "20", "", "1"),
            )),
            today=date(2026, 9, 21),
        )
        self.assertNotEqual(
            newer.fuel_forecast["latest_primary_fillup_marker"],
            base_marker,
        )

    def test_manual_range_calibration_matches_dashboard_and_then_counts_down(self):
        snapshot = parse_backup(forecast_csv(), today=date(2026, 9, 21))
        self.assertEqual(snapshot.fuel_forecast["primary_fillup_count"], 2)
        self.assertEqual(snapshot.fuel_forecast["distance_since_calibration_km"], 28)
        self.assertEqual(snapshot.fuel_forecast["fuel_available_since_calibration_l"], 60)

        consumption = range_calibration_consumption(snapshot, 900)
        self.assertAlmostEqual(consumption, 6.4655, places=4)

        calibrated = apply_range_calibration(
            snapshot,
            consumption,
            target_range_km=900,
            calibrated_at="2026-09-21T12:00:00+02:00",
            today=date(2026, 9, 21),
        )
        self.assertAlmostEqual(calibrated.estimated_range_remaining_km, 900, places=1)
        self.assertEqual(calibrated.fuel_forecast["confidence"], "manual")
        self.assertTrue(calibrated.fuel_forecast["manual_calibration_active"])
        self.assertEqual(calibrated.fuel_forecast["consumption_basis_source"], "manual_range_calibration")
        self.assertAlmostEqual(
            calibrated.fuel_forecast["automatic_consumption_basis_l_per_100km"],
            5.9,
            places=3,
        )

        moved_meta = dict(snapshot.fuel_forecast)
        moved_meta["distance_since_calibration_km"] = 38
        moved = parser.replace(snapshot, fuel_forecast=moved_meta)
        moved_calibrated = apply_range_calibration(
            moved,
            consumption,
            target_range_km=900,
            today=date(2026, 9, 22),
        )
        self.assertAlmostEqual(moved_calibrated.estimated_range_remaining_km, 890, places=1)

    def test_measured_full_to_full_becomes_automatic_range_basis(self):
        csv = forecast_csv().replace(
            "2026-08-01 11:00,900,40,1",
            "2026-08-01 11:00,200,40,1",
        )
        snapshot = parse_backup(csv, today=date(2026, 9, 21))
        economy = snapshot.fuel_forecast["economy"]
        self.assertEqual(economy["measured_windows"], 1)
        self.assertAlmostEqual(economy["weighted_consumption_l_per_100km"], 6.25, places=2)
        self.assertEqual(
            snapshot.fuel_forecast["consumption_basis_source"],
            "measured_full_to_full_recent",
        )
        self.assertAlmostEqual(
            snapshot.fuel_forecast["consumption_basis_l_per_100km"],
            6.25,
            places=2,
        )

    def test_implausible_full_to_full_falls_back_to_fuelio_reports(self):
        snapshot = parse_backup(forecast_csv(), today=date(2026, 9, 21))
        economy = snapshot.fuel_forecast["economy"]
        self.assertEqual(economy["measured_windows"], 0)
        self.assertGreaterEqual(economy["anomalous_windows"], 1)
        self.assertEqual(snapshot.fuel_forecast["consumption_basis_source"], "fuelio_latest_two")
        self.assertAlmostEqual(snapshot.fuel_forecast["consumption_basis_l_per_100km"], 5.9, places=2)


    def test_future_costs_project_to_privacy_safe_calendar_events(self):
        out = StringIO()
        writer = csv.writer(out)

        def section(name, header, *records):
            writer.writerow([f"## {name}"])
            writer.writerow(header)
            writer.writerows(records)

        section(
            "Vehicle",
            ["Name", "DistUnit", "FuelUnit", "Tank1Capacity"],
            ["PRIVATE-REG", "0", "0", "60"],
        )
        section(
            "Log",
            ["Data", "Odo (km)", "Fuel (litres)", "Full", "Price (optional)",
             "VolumePrice", "l/100km (optional)", "TankNumber"],
            ["2026-10-20 11:00", "1000", "50", "1", "1000", "20", "6", "1"],
        )
        section(
            "CostCategories",
            ["CostTypeID", "Name"],
            ["10", "Service"],
            ["20", "Försäkring"],
        )
        section(
            "Costs",
            ["Date", "Cost", "isTemplate", "isIncome", "CostTypeID", "Title", "Notes"],
            ["2026-11-01 08:00", "1200", "0", "0", "10", "SECRET TITLE", "PRIVATE NOTE"],
            ["2026-11-05 08:00", "2400", "0", "0", "20", "ANOTHER SECRET", "PRIVATE NOTE 2"],
            ["2026-11-06 08:00", "999", "1", "0", "10", "TEMPLATE SECRET", "PRIVATE"],
            ["2026-11-07 08:00", "500", "0", "1", "20", "INCOME SECRET", "PRIVATE"],
            ["2026-10-31 08:00", "300", "0", "0", "10", "PAST SECRET", "PRIVATE"],
        )
        section(
            "TripLog",
            ["EndDate", "TripDist", "TripDuration", "TripCost", "StartOdo", "EndOdo"],
        )

        snapshot = parse_backup(out.getvalue(), today=date(2026, 11, 1))
        self.assertEqual(snapshot.upcoming_expense_count, 1)
        self.assertEqual(
            snapshot.upcoming_calendar_events,
            (
                {
                    "date": "2026-11-01",
                    "category": "Service",
                    "amount": 1200.0,
                    "kind": "maintenance",
                    "title": "SECRET TITLE",
                    "note": "PRIVATE NOTE",
                },
                {
                    "date": "2026-11-05",
                    "category": "Försäkring",
                    "amount": 2400.0,
                    "kind": "expense",
                    "title": "ANOTHER SECRET",
                    "note": "PRIVATE NOTE 2",
                },
            ),
        )
        projected = repr(snapshot.upcoming_calendar_events)
        self.assertIn("SECRET TITLE", projected)
        self.assertIn("PRIVATE NOTE", projected)
        self.assertNotIn("PRIVATE-REG", repr(snapshot))

    def test_trip_calendar_projection_uses_tripdist_and_end_odo_without_gps(self):
        out = StringIO()
        writer = csv.writer(out)

        def section(name, header, *records):
            writer.writerow([f"## {name}"])
            writer.writerow(header)
            writer.writerows(records)

        section(
            "Vehicle",
            ["Name", "DistUnit", "FuelUnit", "Tank1Capacity"],
            ["PRIVATE-REG", "0", "0", "60"],
        )
        section(
            "Log",
            ["Data", "Odo (km)", "Fuel (litres)", "Full", "Price (optional)",
             "VolumePrice", "l/100km (optional)", "TankNumber"],
        )
        section("Costs", ["Date", "Cost", "isTemplate", "isIncome"])
        section(
            "TripLog",
            ["title", "StartDate", "EndDate", "TripDist", "TripDuration", "TripCost",
             "StartOdo", "EndOdo", "TripCategory", "TripNote", "StartLat", "StartLon",
             "EndLat", "EndLon", "StartName", "EndName"],
            ["Jobbet", "2026-11-01 07:42:00", "2026-11-01 08:06:00",
             "18123", "1440", "0", "0", "180277", "Arbete", "Kundbesök",
             "59.123", "18.456", "59.789", "18.999", "PRIVATE START", "PRIVATE END"],
        )

        snapshot = parse_backup(out.getvalue(), today=date(2026, 11, 1))
        self.assertEqual(len(snapshot.upcoming_calendar_events), 1)
        event = snapshot.upcoming_calendar_events[0]
        self.assertEqual(event["kind"], "trip")
        self.assertEqual(event["title"], "Jobbet")
        self.assertNotIn("category", event)
        self.assertEqual(event["start"], "2026-11-01T07:42:00")
        self.assertEqual(event["end"], "2026-11-01T08:06:00")
        self.assertAlmostEqual(event["distance_km"], 18.123, places=3)
        self.assertEqual(event["duration_minutes"], 24.0)
        self.assertEqual(event["end_odometer_km"], 180277.0)
        self.assertEqual(event["note"], "Kundbesök")
        projected = repr(event)
        self.assertNotIn("59.123", projected)
        self.assertNotIn("PRIVATE START", projected)
        self.assertNotIn("PRIVATE END", projected)
        self.assertNotIn("StartOdo", projected)

    def test_hierarchical_trip_statistics_keep_tripdist_and_odo_separate(self):
        out = StringIO()
        writer = csv.writer(out)

        def section(name, header, *records):
            writer.writerow([f"## {name}"])
            writer.writerow(header)
            writer.writerows(records)

        section(
            "Vehicle",
            ["Name", "DistUnit", "FuelUnit", "Tank1Capacity"],
            ["Test vehicle", "0", "0", "60"],
        )
        section(
            "Log",
            ["Data", "Odo (km)", "Fuel (litres)", "Full", "Price (optional)",
             "VolumePrice", "l/100km (optional)", "TankNumber"],
            ["2026-10-31 18:00", "1000", "50", "1", "1000", "20", "6", "1"],
        )
        section("Costs", ["Date", "Cost", "isTemplate", "isIncome"])
        section(
            "TripLog",
            ["title", "StartDate", "EndDate", "TripDist", "TripDuration", "TripCost",
             "StartOdo", "EndOdo", "TripCategory", "TripNote"],
            ["A", "2026-11-01 08:00:00", "2026-11-01 08:20:00",
             "10100", "1200", "0", "0", "1010", "1", ""],
            ["B", "2026-11-01 17:00:00", "2026-11-01 17:30:00",
             "12400", "1800", "0", "0", "1023", "1", ""],
        )

        snapshot = parse_backup(out.getvalue(), today=date(2026, 11, 1))
        stats = snapshot.trip_statistics
        self.assertEqual(stats["distance_semantics"]["trip_km"], "Fuelio TripDist")
        self.assertEqual(stats["distance_semantics"]["odo_km"], "odometer checkpoints")

        year = stats["years"][0]
        month = stats["months"][0]
        week = stats["weeks"][0]
        day = stats["days"][0]
        for row in (year, month, week, day):
            self.assertAlmostEqual(row["trip_km"], 22.5, places=3)
            self.assertEqual(row["trip_count"], 2)
            self.assertAlmostEqual(row["duration_hours"], 50 / 60, places=3)
            self.assertAlmostEqual(row["average_trip_km"], 11.25, places=3)
            self.assertEqual(row["odo_km"], 23.0)

        self.assertEqual(year["year"], "2026")
        self.assertEqual(month["month"], "2026-11")
        self.assertEqual(week["week"], "2026-W44")
        self.assertEqual(day["date"], "2026-11-01")

    def test_cost_month_end_overflow_is_clamped_but_trip_dates_stay_strict(self):
        overflow = sample_csv().replace("2026-09-25 12:00", "2026-09-31 05:00", 1)
        snapshot = parse_backup(overflow, today=date(2026, 10, 1))
        september = next(row for row in snapshot.monthly_cost_history if row["month"] == "2026-09")
        self.assertEqual(september["other"], 700)
        self.assertEqual(snapshot.other_expenses, 700)

        invalid_trip = sample_csv().replace("2026-09-18 12:00", "2026-09-31 12:00", 1)
        with self.assertRaisesRegex(ValueError, "Invalid date"):
            parse_backup(invalid_trip, today=date(2026, 10, 1))

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
