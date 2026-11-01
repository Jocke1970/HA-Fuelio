"""Synthetic-only time-aware consumed-fuel estimate tests. No private backups."""
from datetime import date
import unittest

from test_parser import parse_backup, sample_csv


class TimeAwareCostTests(unittest.TestCase):
    @staticmethod
    def fixture():
        return sample_csv(earlier_consumption="5", latest_consumption="6")

    def test_sequential_odometer_intervals_use_only_previously_known_prices(self):
        result = parse_backup(self.fixture(), today=date(2026, 9, 21))
        september = next(row for row in result.monthly_cost_history if row["month"] == "2026-09")
        august = next(row for row in result.monthly_cost_history if row["month"] == "2026-08")
        # August 18: 900 -> 902 at 5 L/100 km * 20 SEK/L = 1 SEK/km.
        self.assertEqual(august["estimated_fuel"], 2)
        # Sept: 902 -> 1000 at preceding 5/20; 1000 -> 1028 at mean(5,6)/20.
        self.assertAlmostEqual(september["estimated_fuel"], 98 + 28 * 1.1, places=2)
        self.assertAlmostEqual(september["estimated_total"], 98 + 28 * 1.1 + 200, places=2)
        self.assertEqual(september["trip_count"], 1)
        self.assertEqual(september["average_trip_km"], 18)
        self.assertEqual(september["km"], 126)
        self.assertEqual(result.latest_two_consumption, 5.5)
        self.assertEqual(result.latest_two_consumption_count, 2)
        self.assertEqual(result.yearly_cost_history[0]["litres"], 90)
        self.assertEqual(result.yearly_cost_history[0]["trip_count"], 2)
        self.assertAlmostEqual(result.estimated_lifetime["estimated_fuel"], 2 + 98 + 28 * 1.1, places=2)

    def test_later_fuel_price_never_reprices_earlier_driving(self):
        original = self.fixture()
        self.assertIn("2026-09-10 11:00,1000,50,1000,20,6", original)
        changed = original.replace("2026-09-10 11:00,1000,50,1000,20,6",
                                   "2026-09-10 11:00,1000,50,1250,25,6")
        before = parse_backup(original, today=date(2026, 9, 21))
        after = parse_backup(changed, today=date(2026, 9, 21))
        aug_before = next(row for row in before.monthly_cost_history if row["month"] == "2026-08")
        aug_after = next(row for row in after.monthly_cost_history if row["month"] == "2026-08")
        self.assertEqual(aug_before["estimated_fuel"], aug_after["estimated_fuel"])
        sept_before = before.monthly_cost_history[0]
        sept_after = after.monthly_cost_history[0]
        self.assertAlmostEqual(sept_after["estimated_fuel"] - sept_before["estimated_fuel"],
                               28 * 5.5 * 5 / 100, places=2)

    def test_fillup_after_driving_does_not_reprice_earlier_segments(self):
        original = self.fixture()
        self.assertIn("## Costs\r\n", original)
        with_late_fillup = original.replace("## Costs\r\n",
            "2026-09-20 11:00,1028,20,2000,100,10\r\n## Costs\r\n", 1)
        before = parse_backup(original, today=date(2026, 9, 21))
        after = parse_backup(with_late_fillup, today=date(2026, 9, 21))
        self.assertEqual(before.monthly_cost_history[0]["estimated_fuel"],
                         after.monthly_cost_history[0]["estimated_fuel"])
        self.assertEqual(after.monthly_cost_history[0]["fuel_ups"], 2)
        self.assertEqual(after.monthly_cost_history[0]["km"], 126)

    def test_no_previous_consumption_does_not_invent_full_month_estimate(self):
        result = parse_backup(sample_csv(), today=date(2026, 9, 21))
        self.assertIsNone(result.monthly_cost_history[0]["estimated_fuel"])
        self.assertEqual(result.monthly_cost_history[0]["estimate_coverage"], "missing_rate")
        self.assertIsNone(result.estimated_lifetime["estimated_total"])

    def test_only_one_valid_consumption_uses_explicit_limited_fallback(self):
        result = parse_backup(sample_csv(latest_consumption="", earlier_consumption="5"),
                              today=date(2026, 9, 21))
        september = result.monthly_cost_history[0]
        self.assertEqual(september["estimated_fuel"], 126)
        self.assertEqual(september["estimate_rate_samples"], 1)
        self.assertEqual(september["estimate_coverage"], "one_consumption_value")
        self.assertEqual(result.latest_two_consumption_count, 1)

    def test_no_odometer_distance_does_not_calculate_ratio(self):
        csv = self.fixture().replace(",1010,1028", ",,").replace(",900,902", ",,")
        csv = csv.replace("11:00,1000,50", "11:00,,50").replace("11:00,900,40", "11:00,,40")
        result = parse_backup(csv, today=date(2026, 9, 21))
        self.assertIsNone(result.monthly_cost_history[0]["estimated_total_per_km"])


if __name__ == "__main__":
    unittest.main()
