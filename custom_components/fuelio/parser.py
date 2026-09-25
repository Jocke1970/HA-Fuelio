"""Parse Fuelio's multi-section sync CSV without exposing raw vehicle records."""
from __future__ import annotations

import csv
from bisect import bisect_left, bisect_right
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from io import StringIO
from math import ceil
from pathlib import Path
from zipfile import BadZipFile, ZipFile

MAX_ZIP_BYTES = 32 * 1024 * 1024
MAX_CSV_BYTES = 64 * 1024 * 1024
MAX_ROWS = 100_000
MAX_MONTHS_IN_ATTRIBUTES = 120  # Bound recorder/state attribute size; newest ten years.


@dataclass(frozen=True, slots=True)
class FuelioSnapshot:
    """Aggregate values only: no plate, VIN, notes, trip details or GPS."""
    vehicle_name: str
    trip_count: int
    trip_distance_km: float
    trip_duration_hours: float
    monthly_trip_distance_km: float
    estimated_trip_cost: float
    fuel_count: int
    fuel_litres: float
    fuel_cost: float
    monthly_fuel_cost: float
    last_fuel_price: float | None
    last_reported_consumption: float | None
    last_fillup_date: date | None
    expense_count: int
    other_expenses: float
    monthly_other_expenses: float
    upcoming_expense_count: int
    total_actual_cost: float
    last_trip_date: date | None
    latest_odometer_km: float | None
    fuel_price_min_year: float | None
    fuel_price_max_year: float | None
    fuel_price_min_all: float | None
    fuel_price_max_all: float | None
    consumption_min_year: float | None
    consumption_max_year: float | None
    consumption_min_all: float | None
    consumption_max_all: float | None
    record_dates: dict[str, str]
    monthly_cost_history: tuple[dict[str, float | str], ...]
    monthly_history_truncated: bool
    odometer_lifetime_km: float | None
    odometer_lifetime_coverage: dict
    estimated_lifetime: dict
    latest_two_consumption: float | None
    latest_two_consumption_count: int
    yearly_cost_history: tuple[dict, ...]
    all_cost_categories: tuple[dict, ...]
    fuel_count_month: int
    fuel_count_year: int
    fuel_cost_per_km_month: float | None
    total_cost_per_km_month: float | None
    fuel_cost_per_km_year: float | None
    total_cost_per_km_year: float | None
    fuel_cost_per_km_all: float | None
    total_cost_per_km_all: float | None
    distance_since_last_fillup_km: float | None
    estimated_fuel_remaining_l: float | None
    estimated_range_remaining_km: float | None
    estimated_days_to_next_fillup: int | None
    estimated_next_fillup_date: date | None
    last_app_sync: datetime | None
    fuel_forecast: dict


def _number(raw: str, *, default: Decimal | None = None) -> Decimal | None:
    if not raw.strip():
        return default
    try:
        value = Decimal(raw.strip())
    except InvalidOperation as exc:
        raise ValueError("Invalid numeric field in Fuelio backup") from exc
    if not value.is_finite():
        raise ValueError("Non-finite numeric field in Fuelio backup")
    return value


def _nonnegative(raw: str, *, default: Decimal | None = None) -> Decimal | None:
    value = _number(raw, default=default)
    if value is not None and value < 0:
        raise ValueError("Negative field in Fuelio backup")
    return value


def _date(raw: str) -> date:
    for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw.strip(), pattern).date()
        except ValueError:
            pass
    raise ValueError("Invalid date in Fuelio backup")


def _section_rows(text: str) -> dict[str, list[dict[str, str]]]:
    reader = csv.reader(StringIO(text, newline=""), strict=True)
    sections: dict[str, list[dict[str, str]]] = {}
    section: str | None = None
    header: list[str] | None = None
    try:
        for index, row in enumerate(reader):
            if index > MAX_ROWS:
                raise ValueError("Too many rows in Fuelio backup")
            if not row or not any(cell.strip() for cell in row):
                continue
            if len(row) == 1 and row[0].strip().startswith("## "):
                section = row[0].strip()[3:]
                if section in sections:
                    raise ValueError("Duplicate section in Fuelio backup")
                sections[section] = []
                header = None
                continue
            if section is None:
                raise ValueError("Fuelio section header missing")
            if header is None:
                header = [cell.strip() for cell in row]
                if len(set(header)) != len(header) or not all(header):
                    raise ValueError("Invalid Fuelio column headers")
                continue
            if len(row) != len(header):
                raise ValueError("Fuelio row has incorrect number of columns")
            sections[section].append(dict(zip(header, row, strict=True)))
    except csv.Error as exc:
        raise ValueError("Invalid Fuelio CSV") from exc
    return sections


def _record(records: list[tuple[Decimal, date]], *, lowest: bool) -> tuple[Decimal | None, str | None]:
    """Pick a real positive observation; on ties use its newest date."""
    if not records:
        return None, None
    boundary = (min if lowest else max)(value for value, _ in records)
    day = max(day for value, day in records if value == boundary)
    return boundary, day.isoformat()


def parse_backup(text: str, *, today: date | None = None) -> FuelioSnapshot:
    """Build aggregates from a metric Fuelio export; never preserve source rows."""
    today = today or date.today()
    sections = _section_rows(text)
    if len(sections.get("Vehicle", [])) != 1:
        raise ValueError("Expected one vehicle per Fuelio backup")
    if any(key not in sections for key in ("Log", "Costs", "TripLog")):
        raise ValueError("Missing Fuelio data section")
    vehicle = sections["Vehicle"][0]
    name = "Fuelio vehicle"  # Vehicle.Name could contain a registration; discard it.
    if vehicle.get("DistUnit") != "0" or vehicle.get("FuelUnit") != "0":
        raise ValueError("This version supports metric Fuelio backups only")

    trip_count = 0
    trip_m = Decimal(0)
    month_trip_m = Decimal(0)
    duration_seconds = Decimal(0)
    estimated_trip_cost = Decimal(0)
    last_trip: date | None = None
    odometers: list[Decimal] = []
    # Date-stamped odometer checkpoints, from tankings and OBD trip boundaries.
    # No trip coordinates, routes, vehicle identifiers or raw rows are retained.
    odometer_by_day: dict[date, list[Decimal]] = {}

    def observe_odometer(day: date, value: Decimal | None) -> None:
        if value is not None and value > 0 and day <= today:
            odometers.append(value)
            odometer_by_day.setdefault(day, []).append(value)
    logged_km_by_month: dict[str, Decimal] = {}
    trip_count_by_month: dict[str, int] = {}
    logged_km_total = Decimal(0)
    logged_km_by_day: dict[date, Decimal] = {}
    for trip in sections["TripLog"]:
        day = _date(trip["EndDate"])
        distance = _nonnegative(trip["TripDist"], default=Decimal(0))
        duration = _nonnegative(trip["TripDuration"], default=Decimal(0))
        estimate = _nonnegative(trip["TripCost"], default=Decimal(0))
        assert distance is not None and duration is not None and estimate is not None
        trip_count += 1
        trip_m += distance
        duration_seconds += duration
        estimated_trip_cost += estimate
        if day <= today:
            month_key = day.strftime("%Y-%m")
            km = distance / 1000
            logged_km_by_month[month_key] = logged_km_by_month.get(month_key, Decimal(0)) + km
            trip_count_by_month[month_key] = trip_count_by_month.get(month_key, 0) + 1
            logged_km_total += km
            logged_km_by_day[day] = logged_km_by_day.get(day, Decimal(0)) + km
        if (day.year, day.month) == (today.year, today.month) and day <= today:
            month_trip_m += distance
        if day <= today and (last_trip is None or day > last_trip):
            last_trip = day
        # Use the actual StartDate when present, otherwise the trip's EndDate.
        # Start/EndOdo may straddle a calendar boundary, unlike TripDist.
        start_day = _date(trip["StartDate"]) if trip.get("StartDate", "").strip() else day
        if start_day <= day and day <= today:
            observe_odometer(start_day, _nonnegative(trip.get("StartOdo", "")))
            observe_odometer(day, _nonnegative(trip.get("EndOdo", "")))

    # Monthly values are aggregate-only and capped before exposing as HA attributes.
    monthly: dict[str, dict[str, Decimal]] = {}

    def bucket(day: date) -> dict[str, Decimal]:
        return monthly.setdefault(day.strftime("%Y-%m"), {"fuel": Decimal(0), "other": Decimal(0), "litres": Decimal(0)})

    fuel_count = 0
    fuel_ups_by_month: dict[str, int] = {}
    litres = Decimal(0)
    fuel_cost = Decimal(0)
    month_fuel_cost = Decimal(0)
    last_fillup: date | None = None
    last_price: Decimal | None = None
    last_consumption: Decimal | None = None
    last_consumption_day: date | None = None
    valid_prices: list[tuple[Decimal, date]] = []
    valid_consumptions: list[tuple[Decimal, date]] = []
    tank_capacity = _nonnegative(vehicle.get("Tank1Capacity", ""))
    fuel_events: list[dict] = []
    for fillup in sections["Log"]:
        day = _date(fillup["Data"])
        volume = _nonnegative(fillup["Fuel (litres)"], default=Decimal(0))
        cost = _nonnegative(fillup["Price (optional)"], default=Decimal(0))
        assert volume is not None and cost is not None
        if day > today:
            continue
        fuel_count += 1
        month_key = day.strftime("%Y-%m")
        fuel_ups_by_month[month_key] = fuel_ups_by_month.get(month_key, 0) + 1
        litres += volume
        fuel_cost += cost
        bucket(day)["fuel"] += cost
        bucket(day)["litres"] += volume
        if (day.year, day.month) == (today.year, today.month):
            month_fuel_cost += cost
        fill_odo = _nonnegative(fillup.get("Odo (km)", ""))
        observe_odometer(day, fill_odo)
        fuel_events.append({
            "day": day,
            "odo": fill_odo,
            "volume": volume,
            "full": fillup.get("Full", "").strip() == "1",
            "tank": fillup.get("TankNumber", "1").strip() or "1",
        })
        reported = _nonnegative(fillup.get("l/100km (optional)", ""))
        if reported is not None and (last_consumption_day is None or day > last_consumption_day):
            last_consumption_day = day
            last_consumption = reported
        # Zero, empty or otherwise missing measurements are not fuel-price/consumption records.
        if reported is not None and reported > 0:
            valid_consumptions.append((reported, day))
        price = _nonnegative(fillup.get("VolumePrice", ""))
        effective_price = price if price is not None and price > 0 else (cost / volume if volume and cost else None)
        if volume > 0 and effective_price is not None and effective_price > 0:
            valid_prices.append((effective_price, day))
        if last_fillup is None or day > last_fillup:
            last_fillup = day
            last_price = price if price is not None and price > 0 else (cost / volume if volume else None)

    # CostCategories maps private internal IDs to display labels. Never expose IDs,
    # individual expense titles, notes or other source records as HA attributes.
    category_names: dict[str, str] = {}
    for category in sections.get("CostCategories", []):
        identifier = category.get("CostTypeID", "").strip()
        if not identifier:
            continue
        if identifier in category_names:
            raise ValueError("Duplicate Fuelio cost category ID")
        label = " ".join(category.get("Name", "").split())[:64]
        category_names[identifier] = label or "Okategoriserat"
    expense_categories_by_month: dict[str, dict[str, Decimal]] = {}
    expense_count = 0
    expenses = Decimal(0)
    month_expenses = Decimal(0)
    upcoming = 0
    for record in sections["Costs"]:
        if record.get("isTemplate", "0").strip() == "1" or record.get("isIncome", "0").strip() == "1":
            continue
        day = _date(record["Date"])
        amount = _nonnegative(record["Cost"], default=Decimal(0))
        assert amount is not None
        expense_count += 1
        if day > today:
            upcoming += 1
            continue
        expenses += amount
        bucket(day)["other"] += amount
        month_key = day.strftime("%Y-%m")
        label = category_names.get(record.get("CostTypeID", "").strip(), "Okategoriserat")
        categories = expense_categories_by_month.setdefault(month_key, {})
        categories[label] = categories.get(label, Decimal(0)) + amount
        if (day.year, day.month) == (today.year, today.month):
            month_expenses += amount

    def rounded(value: Decimal, places: int = 2) -> float:
        return round(float(value), places)

    extrema: dict[str, float | None] = {}
    record_dates: dict[str, str] = {}
    for prefix, records in (("fuel_price", valid_prices), ("consumption", valid_consumptions)):
        this_year = [(value, day) for value, day in records if day.year == today.year]
        for suffix, subset in (("year", this_year), ("all", records)):
            for label, lowest in (("min", True), ("max", False)):
                key = f"{prefix}_{label}_{suffix}"
                value, recorded_on = _record(subset, lowest=lowest)
                extrema[key] = rounded(value, 3) if value is not None and prefix == "fuel_price" else (rounded(value) if value is not None else None)
                if recorded_on is not None:
                    record_dates[key] = recorded_on

    # A period uses the most recent ODO checkpoint BEFORE its first day and
    # the latest checkpoint inside that period. Thus missing a reading on the
    # month's last day does not invalidate a month, and successive months share
    # a consistent boundary checkpoint. This is observed, not exact-midnight km.
    # First imported period has no earlier checkpoint: measure from its first
    # in-period reading and explicitly mark incomplete coverage.
    odometer_days = sorted(odometer_by_day)

    def odometer_distance(start: date | None, end: date) -> tuple[Decimal | None, dict]:
        in_period = [day for day in odometer_days if (start is None or day >= start) and day <= end]
        if not in_period:
            return None, {"odo_coverage": "unavailable"}
        last_day = in_period[-1]
        last = max(odometer_by_day[last_day])
        prior = [day for day in odometer_days if start is not None and day < start]
        if prior:
            first_day = prior[-1]
            first = max(odometer_by_day[first_day])
            coverage = "prior_checkpoint"
        else:
            first_day = in_period[0]
            first = min(odometer_by_day[first_day])
            coverage = "partial_start" if start is not None else "import_start"
        if last < first:
            return None, {"odo_coverage": "invalid_rollback"}
        # A single reading cannot establish distance. Two checkpoints with the
        # same value legitimately establish zero distance, not a cost/km value.
        if first_day == last_day and len(odometer_by_day[first_day]) < 2:
            return None, {"odo_coverage": "insufficient_readings"}
        return last - first, {"odo_coverage": coverage,
                              "odo_start_on": first_day.isoformat(),
                              "odo_end_on": last_day.isoformat()}

    def per_odometer_km(cost: Decimal, km: Decimal | None) -> float | None:
        return rounded(cost / km, 3) if km is not None and km > 0 else None

    consumption_history = sorted(valid_consumptions, key=lambda item: item[1])
    price_history = sorted(valid_prices, key=lambda item: item[1])
    consumption_days = [day for _, day in consumption_history]
    price_days = [day for _, day in price_history]
    all_consumptions = [value for value, _ in consumption_history]

    def estimate_rate(as_of: date) -> tuple[Decimal | None, int]:
        """Fuel SEK/km as known at interval start; never look into the future."""
        ci = bisect_right(consumption_days, as_of)
        pi = bisect_right(price_days, as_of)
        if ci == 0 or pi == 0:
            return None, 0
        recent = [value for value, _ in consumption_history[max(0, ci - 2):ci]]
        return sum(recent, Decimal(0)) / len(recent) * price_history[pi - 1][0] / 100, len(recent)

    def estimate_period(start: date | None, end: date, km: Decimal | None,
                        odo_coverage: dict) -> dict:
        """Integrate observed ODO intervals without repricing earlier driving.

        Same-day ordering is unknown in the CSV; daily odometer maxima are the
        observation boundaries, with the first daily minimum as import baseline.
        Missing rate for ANY positive distance leaves whole-period estimate unknown.
        """
        result = {"estimated_fuel": None, "estimated_total": None,
                  "estimated_fuel_per_km": None, "estimated_total_per_km": None,
                  "estimate_coverage": odo_coverage.get("odo_coverage", "unavailable"),
                  "estimate_rate_samples": 0}
        if km is None or km <= 0:
            return result
        first_index = 0 if start is None else bisect_left(odometer_days, start)
        last_index = bisect_right(odometer_days, end)
        days = odometer_days[first_index:last_index]
        if not days:
            return result
        prior_index = first_index - 1 if start is not None else -1
        if prior_index >= 0:
            cursor_day = odometer_days[prior_index]
            cursor_odo = max(odometer_by_day[cursor_day])
        else:
            cursor_day = days[0]
            cursor_odo = min(odometer_by_day[cursor_day])
        estimated = Decimal(0)
        samples = 2
        observed = Decimal(0)
        missing = False
        for day in days:
            reading = max(odometer_by_day[day])
            if reading < cursor_odo:
                result["estimate_coverage"] = "invalid_rollback"
                return result
            delta = reading - cursor_odo
            if delta:
                observed += delta
                rate, count = estimate_rate(cursor_day)
                if rate is None:
                    missing = True
                else:
                    estimated += delta * rate
                    samples = min(samples, count)
            cursor_day, cursor_odo = day, reading
        if observed != km or missing:
            result["estimate_coverage"] = "missing_rate" if missing else "inconsistent_distance"
            return result
        result["estimated_fuel"] = rounded(estimated)
        result["estimated_fuel_per_km"] = per_odometer_km(estimated, km)
        result["estimate_rate_samples"] = samples
        if samples == 1:
            result["estimate_coverage"] = "one_consumption_value" if start is None else (
                "partial_start_one_value" if odo_coverage.get("odo_coverage") == "partial_start" else "one_consumption_value")
        return result

    latest_values = all_consumptions[-2:]
    latest_two_consumption = (sum(latest_values, Decimal(0)) / len(latest_values)) if latest_values else None

    # Range forecast. A full primary-tank fill is a calibration point. Later
    # partial fills add their recorded litres; driven distance consumes fuel at
    # the rolling mean of the latest two valid reported consumption values.
    # This deliberately stays aggregate-only and never exposes individual trips.
    latest_odometer_value = max(odometers) if odometers else None
    primary_events = sorted(
        (event for event in fuel_events if event["tank"] == "1" and event["odo"] is not None),
        key=lambda event: (event["day"], event["odo"]),
    )
    last_fill_event = primary_events[-1] if primary_events else None
    distance_since_last_fillup: Decimal | None = None
    if last_fill_event is not None and latest_odometer_value is not None:
        if latest_odometer_value >= last_fill_event["odo"]:
            distance_since_last_fillup = latest_odometer_value - last_fill_event["odo"]

    estimated_fuel_remaining: Decimal | None = None
    estimated_range_remaining: Decimal | None = None
    estimated_days_to_next_fillup: int | None = None
    estimated_next_fillup_date: date | None = None
    forecast_meta: dict = {
        "confidence": "unavailable",
        "consumption_basis_l_per_100km": rounded(latest_two_consumption, 3) if latest_two_consumption is not None else None,
        "consumption_samples": len(latest_values),
        "tank_capacity_l": rounded(tank_capacity, 3) if tank_capacity is not None else None,
        "calibration_full_fillup_date": None,
        "partial_fillups_since_calibration": 0,
        "average_daily_distance_30d_km": None,
        "daily_distance_window_days": 0,
        "prediction_basis": "theoretical_empty_tank",
    }
    full_indexes = [index for index, event in enumerate(primary_events) if event["full"]]
    if (
        full_indexes
        and tank_capacity is not None and tank_capacity > 0
        and latest_two_consumption is not None and latest_two_consumption > 0
        and latest_odometer_value is not None
    ):
        calibration_index = full_indexes[-1]
        calibration = primary_events[calibration_index]
        calibration_odo = calibration["odo"]
        if calibration_odo is not None and latest_odometer_value >= calibration_odo:
            later = primary_events[calibration_index + 1:]
            added_litres = sum((event["volume"] for event in later), Decimal(0))
            consumed_litres = (latest_odometer_value - calibration_odo) * latest_two_consumption / 100
            raw_remaining = tank_capacity + added_litres - consumed_litres
            estimated_fuel_remaining = min(tank_capacity, max(Decimal(0), raw_remaining))
            estimated_range_remaining = estimated_fuel_remaining / latest_two_consumption * 100

            window_start = today - timedelta(days=29)
            window_km = sum(
                (km for day, km in logged_km_by_day.items() if window_start <= day <= today),
                Decimal(0),
            )
            eligible_days = [day for day in logged_km_by_day if day <= today]
            coverage_start = max(window_start, min(eligible_days)) if eligible_days else today
            coverage_days = max(1, (today - coverage_start).days + 1)
            average_daily = window_km / coverage_days
            if average_daily > 0:
                estimated_days_to_next_fillup = ceil(float(estimated_range_remaining / average_daily))
                estimated_next_fillup_date = today + timedelta(days=estimated_days_to_next_fillup)

            calibration_age = (today - calibration["day"]).days
            forecast_meta.update({
                "confidence": "normal" if len(latest_values) >= 2 and calibration_age <= 90 else "limited",
                "calibration_full_fillup_date": calibration["day"].isoformat(),
                "partial_fillups_since_calibration": len(later),
                "average_daily_distance_30d_km": rounded(average_daily, 3),
                "daily_distance_window_days": coverage_days,
            })

    def category_rows(values: dict[str, Decimal]) -> list[dict]:
        # Cap attributes while preserving sums when many user categories exist.
        ordered = sorted(values.items(), key=lambda item: (-item[1], item[0]))
        visible = ordered[:19]
        remainder = sum((amount for _, amount in ordered[19:]), Decimal(0))
        rows = [{"name": label, "amount": rounded(amount)} for label, amount in visible]
        if remainder:
            rows.append({"name": "Övriga kategorier", "amount": rounded(remainder)})
        return rows

    # Always include the current month, even if it has neither trips nor costs.
    bucket(today)
    odo_months = {day.strftime("%Y-%m") for day in odometer_days}
    month_keys = sorted(set(monthly) | set(logged_km_by_month) | set(fuel_ups_by_month) | odo_months, reverse=True)
    odo_month_data = {}
    month_estimates = {}
    for key in month_keys:
        year, month = (int(part) for part in key.split("-"))
        start = date(year, month, 1)
        next_month = date(year + (month == 12), (month % 12) + 1, 1)
        end = min(today, next_month - timedelta(days=1))
        odo_month_data[key] = odometer_distance(start, end) if end >= start else (None, {"odo_coverage": "unavailable"})
        km, coverage = odo_month_data[key]
        month_estimates[key] = estimate_period(start, end, km, coverage)
    year_totals: dict[str, dict] = {}
    all_categories: dict[str, Decimal] = {}
    for month in month_keys:
        year = month[:4]
        year_row = year_totals.setdefault(year, {"fuel": Decimal(0), "other": Decimal(0),
                                           "km": None, "fuel_ups": 0, "litres": Decimal(0), "trip_count": 0, "logged_trip_km": Decimal(0), "categories": {}})
        values = monthly.get(month, {"fuel": Decimal(0), "other": Decimal(0), "litres": Decimal(0)})
        year_row["fuel"] += values["fuel"]
        year_row["other"] += values["other"]
        year_row["litres"] += values["litres"]
        year_row["fuel_ups"] += fuel_ups_by_month.get(month, 0)
        year_row["trip_count"] += trip_count_by_month.get(month, 0)
        year_row["logged_trip_km"] += logged_km_by_month.get(month, Decimal(0))
        for label, amount in expense_categories_by_month.get(month, {}).items():
            year_row["categories"][label] = year_row["categories"].get(label, Decimal(0)) + amount
            all_categories[label] = all_categories.get(label, Decimal(0)) + amount

    year_odo_data = {}
    year_estimates = {}
    for year in year_totals:
        beginning = date(int(year), 1, 1)
        ending = min(today, date(int(year), 12, 31))
        year_odo_data[year] = odometer_distance(beginning, ending)
        year_totals[year]["km"] = year_odo_data[year][0]
        year_estimates[year] = estimate_period(beginning, ending, *year_odo_data[year])
    lifetime_km, lifetime_coverage = odometer_distance(None, today)
    lifetime_estimate = estimate_period(None, today, lifetime_km, lifetime_coverage)

    def period_row(month: str) -> dict:
        values = monthly.get(month, {"fuel": Decimal(0), "other": Decimal(0), "litres": Decimal(0)})
        km, coverage = odo_month_data[month]
        estimate = dict(month_estimates[month])
        if estimate["estimated_fuel"] is not None:
            estimate["estimated_total"] = rounded(Decimal(str(estimate["estimated_fuel"])) + values["other"])
            estimate["estimated_total_per_km"] = per_odometer_km(Decimal(str(estimate["estimated_total"])), km)
        trip_count_period = trip_count_by_month.get(month, 0)
        return {"month": month, "fuel": rounded(values["fuel"]), "other": rounded(values["other"]),
                "total": rounded(values["fuel"] + values["other"]), "km": rounded(km, 3) if km is not None else None,
                "logged_trip_km": rounded(logged_km_by_month.get(month, Decimal(0)), 3),
                "trip_count": trip_count_period,
                "average_trip_km": rounded(logged_km_by_month.get(month, Decimal(0)) / trip_count_period, 3) if trip_count_period else None,
                "litres": rounded(values["litres"], 3), "fuel_ups": fuel_ups_by_month.get(month, 0),
                "fuel_per_logged_km": per_odometer_km(values["fuel"], km),
                "total_per_logged_km": per_odometer_km(values["fuel"] + values["other"], km),
                "categories": category_rows(expense_categories_by_month.get(month, {})), **coverage, **estimate}

    truncated = len(month_keys) > MAX_MONTHS_IN_ATTRIBUTES
    history = tuple(period_row(key) for key in month_keys[:MAX_MONTHS_IN_ATTRIBUTES])
    for year, row in year_totals.items():
        estimate = year_estimates[year]
        if estimate["estimated_fuel"] is not None:
            estimate["estimated_total"] = rounded(Decimal(str(estimate["estimated_fuel"])) + row["other"])
            estimate["estimated_total_per_km"] = per_odometer_km(Decimal(str(estimate["estimated_total"])), row["km"])
    if lifetime_estimate["estimated_fuel"] is not None:
        lifetime_estimate["estimated_total"] = rounded(Decimal(str(lifetime_estimate["estimated_fuel"])) + expenses)
        lifetime_estimate["estimated_total_per_km"] = per_odometer_km(Decimal(str(lifetime_estimate["estimated_total"])), lifetime_km)
    year_history = tuple(
        {"year": year, "fuel": rounded(row["fuel"]), "other": rounded(row["other"]),
         "total": rounded(row["fuel"] + row["other"]),
         "km": rounded(row["km"], 3) if row["km"] is not None else None,
         "litres": rounded(row["litres"], 3), "fuel_ups": row["fuel_ups"],
         "trip_count": row["trip_count"], "logged_trip_km": rounded(row["logged_trip_km"], 3),
         "average_trip_km": rounded(row["logged_trip_km"] / row["trip_count"], 3) if row["trip_count"] else None,
         "fuel_per_logged_km": per_odometer_km(row["fuel"], row["km"]),
         "total_per_logged_km": per_odometer_km(row["fuel"] + row["other"], row["km"]),
         "categories": category_rows(row["categories"]), **year_odo_data[year][1], **year_estimates[year]}
        for year, row in sorted(year_totals.items(), reverse=True)[:40]
    )
    current = year_totals.get(str(today.year), {"fuel": Decimal(0), "other": Decimal(0),
                                                "km": None, "fuel_ups": 0})
    this_month = today.strftime("%Y-%m")
    month_km = odo_month_data[this_month][0]

    return FuelioSnapshot(
        vehicle_name=name,
        trip_count=trip_count,
        trip_distance_km=rounded(trip_m / 1000, 3),
        trip_duration_hours=rounded(duration_seconds / 3600),
        monthly_trip_distance_km=rounded(month_trip_m / 1000, 3),
        estimated_trip_cost=rounded(estimated_trip_cost),
        fuel_count=fuel_count,
        fuel_litres=rounded(litres, 3),
        fuel_cost=rounded(fuel_cost),
        monthly_fuel_cost=rounded(month_fuel_cost),
        last_fuel_price=rounded(last_price, 3) if last_price is not None else None,
        last_reported_consumption=rounded(last_consumption) if last_consumption is not None else None,
        last_fillup_date=last_fillup,
        expense_count=expense_count,
        other_expenses=rounded(expenses),
        monthly_other_expenses=rounded(month_expenses),
        upcoming_expense_count=upcoming,
        total_actual_cost=rounded(fuel_cost + expenses),
        last_trip_date=last_trip,
        latest_odometer_km=rounded(latest_odometer_value, 1) if latest_odometer_value is not None else None,
        fuel_price_min_year=extrema["fuel_price_min_year"],
        fuel_price_max_year=extrema["fuel_price_max_year"],
        fuel_price_min_all=extrema["fuel_price_min_all"],
        fuel_price_max_all=extrema["fuel_price_max_all"],
        consumption_min_year=extrema["consumption_min_year"],
        consumption_max_year=extrema["consumption_max_year"],
        consumption_min_all=extrema["consumption_min_all"],
        consumption_max_all=extrema["consumption_max_all"],
        record_dates=record_dates,
        monthly_cost_history=history,
        monthly_history_truncated=truncated,
        odometer_lifetime_km=rounded(lifetime_km, 3) if lifetime_km is not None else None,
        odometer_lifetime_coverage=lifetime_coverage,
        estimated_lifetime=lifetime_estimate,
        latest_two_consumption=rounded(latest_two_consumption, 3) if latest_two_consumption is not None else None,
        latest_two_consumption_count=len(latest_values),
        yearly_cost_history=year_history,
        all_cost_categories=tuple(category_rows(all_categories)),
        fuel_count_month=fuel_ups_by_month.get(this_month, 0),
        fuel_count_year=current["fuel_ups"],
        fuel_cost_per_km_month=per_odometer_km(month_fuel_cost, month_km),
        total_cost_per_km_month=per_odometer_km(month_fuel_cost + month_expenses, month_km),
        fuel_cost_per_km_year=per_odometer_km(current["fuel"], current["km"]),
        total_cost_per_km_year=per_odometer_km(current["fuel"] + current["other"], current["km"]),
        fuel_cost_per_km_all=per_odometer_km(fuel_cost, lifetime_km),
        total_cost_per_km_all=per_odometer_km(fuel_cost + expenses, lifetime_km),
        distance_since_last_fillup_km=rounded(distance_since_last_fillup, 1) if distance_since_last_fillup is not None else None,
        estimated_fuel_remaining_l=rounded(estimated_fuel_remaining, 2) if estimated_fuel_remaining is not None else None,
        estimated_range_remaining_km=rounded(estimated_range_remaining, 1) if estimated_range_remaining is not None else None,
        estimated_days_to_next_fillup=estimated_days_to_next_fillup,
        estimated_next_fillup_date=estimated_next_fillup_date,
        last_app_sync=None,
        fuel_forecast=forecast_meta,
    )


def load_snapshot(path: str, today: date | None = None) -> FuelioSnapshot:
    """Load one bounded UTF-8 CSV from ZIP in memory; never extract files."""
    archive = Path(path)
    if archive.suffix.lower() != ".zip":
        raise ValueError("Expected a Fuelio ZIP backup")
    if archive.stat().st_size > MAX_ZIP_BYTES:
        raise ValueError("Fuelio ZIP too large")
    try:
        with ZipFile(archive) as zip_file:
            members = [item for item in zip_file.infolist() if not item.is_dir() and item.filename.lower().endswith(".csv")]
            if len(members) != 1 or members[0].file_size > MAX_CSV_BYTES or members[0].flag_bits & 0x1:
                raise ValueError("Expected one unencrypted CSV within ZIP")
            with zip_file.open(members[0]) as source:
                raw = source.read(MAX_CSV_BYTES + 1)
            if len(raw) > MAX_CSV_BYTES:
                raise ValueError("Fuelio CSV too large")
    except (BadZipFile, EOFError) as exc:
        raise ValueError("Invalid Fuelio ZIP") from exc
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise ValueError("Fuelio CSV must use UTF-8") from exc
    snapshot = parse_backup(text, today=today)
    source_modified = datetime.fromtimestamp(archive.stat().st_mtime).astimezone()
    return replace(snapshot, last_app_sync=source_modified)
