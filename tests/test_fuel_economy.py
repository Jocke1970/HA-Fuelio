"""Synthetic tests for the privacy-safe full-to-full economy engine."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "custom_components" / "fuelio" / "fuel_economy.py"
spec = importlib.util.spec_from_file_location("fuelio_economy_test", MODULE)
economy = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = economy
spec.loader.exec_module(economy)

FuelEconomyEvent = economy.FuelEconomyEvent
compute_fuel_economy = economy.compute_fuel_economy


def event(
    odo: str,
    litres: str,
    *,
    full: bool,
    day: int,
    missed: bool = False,
    exclude: bool = False,
    fuel_type: str = "201",
) -> FuelEconomyEvent:
    return FuelEconomyEvent(
        day=date(2026, 1, day),
        odometer_km=Decimal(odo),
        litres=Decimal(litres),
        full=full,
        tank="1",
        fuel_type=fuel_type,
        missed=missed,
        exclude_distance=exclude,
    )


class FuelEconomyTests(unittest.TestCase):
    def test_full_partial_full_banks_partial_litres(self):
        result = compute_fuel_economy([
            event("1000", "40", full=True, day=1),
            event("1300", "20", full=False, day=2),
            event("1600", "30", full=True, day=3),
        ], tank_capacity_l=Decimal("60"))
        self.assertEqual(result["measured_windows"], 1)
        self.assertAlmostEqual(result["weighted_consumption_l_per_100km"], 8.333, places=3)
        self.assertEqual(result["latest_window_l_per_100km"], result["weighted_consumption_l_per_100km"])
        self.assertEqual(result["confidence"], "moderate")

    def test_weighted_average_uses_total_fuel_over_total_distance(self):
        result = compute_fuel_economy([
            event("0", "40", full=True, day=1),
            event("500", "25", full=True, day=2),   # 5.0 L/100 km
            event("1500", "100", full=True, day=3), # 10.0 L/100 km
        ], tank_capacity_l=Decimal("120"))
        self.assertEqual(result["measured_windows"], 2)
        self.assertAlmostEqual(
            result["weighted_consumption_l_per_100km"],
            125 / 1500 * 100,
            places=3,
        )
        self.assertNotAlmostEqual(result["weighted_consumption_l_per_100km"], 7.5, places=2)

    def test_missed_and_excluded_distance_invalidate_windows(self):
        missed = compute_fuel_economy([
            event("1000", "40", full=True, day=1),
            event("1300", "20", full=False, day=2, missed=True),
            event("1600", "30", full=True, day=3),
        ])
        self.assertEqual(missed["measured_windows"], 0)
        self.assertEqual(missed["excluded_windows"], 1)

        excluded = compute_fuel_economy([
            event("1000", "40", full=True, day=1),
            event("1600", "50", full=True, day=3, exclude=True),
        ])
        self.assertEqual(excluded["measured_windows"], 0)
        self.assertEqual(excluded["excluded_windows"], 1)

    def test_implausible_window_is_anomaly_not_measurement(self):
        result = compute_fuel_economy([
            event("1000", "40", full=True, day=1),
            event("1100", "50", full=True, day=2),
        ], tank_capacity_l=Decimal("60"))
        self.assertEqual(result["measured_windows"], 0)
        self.assertEqual(result["anomalous_windows"], 1)
        self.assertIsNone(result["weighted_consumption_l_per_100km"])

    def test_three_windows_give_high_confidence_and_trend(self):
        result = compute_fuel_economy([
            event("0", "40", full=True, day=1),
            event("500", "25", full=True, day=2),    # 5
            event("1000", "30", full=True, day=3),   # 6
            event("1500", "35", full=True, day=4),   # 7
        ], tank_capacity_l=Decimal("60"))
        self.assertEqual(result["measured_windows"], 3)
        self.assertEqual(result["confidence"], "high")
        self.assertEqual(result["trend"], "increasing")
        self.assertGreater(result["trend_slope"], 0)


if __name__ == "__main__":
    unittest.main()
