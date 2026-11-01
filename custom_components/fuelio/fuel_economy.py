"""Measured fuel-economy calculations from aggregate Fuelio fill-up fields.

This module intentionally implements the mathematics independently. It consumes only
fields already present in Fuelio's local ZIP and returns aggregate statistics; no raw
trip, station, GPS, notes, registration or vehicle identifiers leave the parser.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

MAX_WINDOW_DISTANCE_KM = Decimal("3000")
MAX_L_PER_100KM = Decimal("30")
MIN_L_PER_100KM = Decimal("1.5")
OVERFILL_TOLERANCE = Decimal("1.05")
RECENT_WINDOW_COUNT = 5


@dataclass(frozen=True, slots=True)
class FuelEconomyEvent:
    """Minimal privacy-safe fill-up input used by the economy calculator."""

    day: date
    odometer_km: Decimal
    litres: Decimal
    full: bool
    tank: str = "1"
    fuel_type: str = ""
    missed: bool = False
    exclude_distance: bool = False


def _slope(values: list[Decimal]) -> Decimal:
    """Least-squares slope over equally spaced windows."""
    count = len(values)
    if count < 2:
        return Decimal(0)
    mean_x = Decimal(count - 1) / 2
    mean_y = sum(values, Decimal(0)) / count
    numerator = Decimal(0)
    denominator = Decimal(0)
    for index, value in enumerate(values):
        dx = Decimal(index) - mean_x
        numerator += dx * (value - mean_y)
        denominator += dx * dx
    return numerator / denominator if denominator else Decimal(0)


def compute_fuel_economy(
    events: list[FuelEconomyEvent],
    *,
    tank_capacity_l: Decimal | None = None,
    tank: str = "1",
) -> dict:
    """Return measured full-to-full consumption statistics in L/100 km.

    A full fill is an anchor. Partial fills after it are banked and belong to the
    next full fill. A window is excluded if Fuelio marks a missed fill or excluded
    distance anywhere after the opening anchor, or when the observations are
    physically implausible. Aggregates are fuel/distance weighted, never a mean of
    per-window ratios.
    """
    relevant = sorted(
        (event for event in events if event.tank == tank),
        key=lambda event: (event.odometer_km, event.day),
    )

    anchor: FuelEconomyEvent | None = None
    carry_litres = Decimal(0)
    contaminated = False
    fuel_type: str | None = None
    measured: list[tuple[Decimal, Decimal, Decimal]] = []
    anomalous_windows = 0
    excluded_windows = 0

    for event in relevant:
        if event.odometer_km < 0 or event.litres < 0:
            anomalous_windows += 1
            anchor = event if event.full else anchor
            carry_litres = Decimal(0) if event.full else carry_litres
            contaminated = True
            continue

        if anchor is None:
            if event.full:
                anchor = event
                carry_litres = Decimal(0)
                contaminated = False
                fuel_type = event.fuel_type or None
            continue

        if event.missed or event.exclude_distance:
            contaminated = True

        if fuel_type and event.fuel_type and event.fuel_type != fuel_type:
            contaminated = True

        if not event.full:
            carry_litres += event.litres
            continue

        distance = event.odometer_km - anchor.odometer_km
        window_fuel = carry_litres + event.litres

        if contaminated:
            excluded_windows += 1
        else:
            anomaly = (
                distance <= 0
                or distance > MAX_WINDOW_DISTANCE_KM
                or window_fuel <= 0
            )
            if (
                not anomaly
                and tank_capacity_l is not None
                and tank_capacity_l > 0
                and event.litres > tank_capacity_l * OVERFILL_TOLERANCE
            ):
                anomaly = True

            consumption = (
                window_fuel * Decimal(100) / distance
                if not anomaly
                else Decimal(0)
            )
            if (
                not anomaly
                and (
                    consumption < MIN_L_PER_100KM
                    or consumption > MAX_L_PER_100KM
                )
            ):
                anomaly = True

            if anomaly:
                anomalous_windows += 1
            else:
                measured.append((distance, window_fuel, consumption))

        anchor = event
        carry_litres = Decimal(0)
        contaminated = False
        fuel_type = event.fuel_type or None

    total_distance = sum((window[0] for window in measured), Decimal(0))
    total_fuel = sum((window[1] for window in measured), Decimal(0))
    weighted = total_fuel * Decimal(100) / total_distance if total_distance > 0 else None

    recent = measured[-RECENT_WINDOW_COUNT:]
    recent_distance = sum((window[0] for window in recent), Decimal(0))
    recent_fuel = sum((window[1] for window in recent), Decimal(0))
    recent_consumption = (
        recent_fuel * Decimal(100) / recent_distance
        if recent_distance > 0
        else None
    )
    latest = measured[-1][2] if measured else None

    values = [window[2] for window in measured]
    trend_slope = _slope(values)
    if weighted is None or len(values) < 2:
        trend = "unavailable"
    else:
        stable_band = max(Decimal("0.05"), weighted * Decimal("0.01"))
        trend = (
            "increasing"
            if trend_slope > stable_band
            else "decreasing"
            if trend_slope < -stable_band
            else "stable"
        )

    count = len(measured)
    confidence = "high" if count >= 3 else "moderate" if count >= 1 else "unavailable"

    def rounded(value: Decimal | None, places: int = 3):
        return round(float(value), places) if value is not None else None

    return {
        "measured_windows": count,
        "weighted_consumption_l_per_100km": rounded(weighted),
        "recent_consumption_l_per_100km": rounded(recent_consumption),
        "recent_window_count": len(recent),
        "latest_window_l_per_100km": rounded(latest),
        "trend": trend,
        "trend_slope": rounded(trend_slope, 4) if values else None,
        "anomalous_windows": anomalous_windows,
        "excluded_windows": excluded_windows,
        "confidence": confidence,
        "basis": "full_to_full",
    }
