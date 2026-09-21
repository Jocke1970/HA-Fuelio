"""Parse Fuelio's multi-section sync CSV, without publishing raw vehicle records."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

MAX_ZIP_BYTES = 32 * 1024 * 1024
MAX_CSV_BYTES = 64 * 1024 * 1024
MAX_ROWS = 100_000


@dataclass(frozen=True, slots=True)
class FuelioSnapshot:
    """Aggregate values only: no plate, VIN, notes, route or GPS coordinates."""
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


def parse_backup(text: str, *, today: date | None = None) -> FuelioSnapshot:
    """Build a summary from the metric Fuelio export format."""
    today = today or date.today()
    sections = _section_rows(text)
    if len(sections.get("Vehicle", [])) != 1:
        raise ValueError("Expected one vehicle per Fuelio backup")
    if any(key not in sections for key in ("Log", "Costs", "TripLog")):
        raise ValueError("Missing Fuelio data section")
    vehicle = sections["Vehicle"][0]
    # Vehicle.Name may contain the registration number. Never retain it in the snapshot.
    name = "Fuelio vehicle"
    # Zero represents the metric export observed in the supplied sample.
    if vehicle.get("DistUnit") != "0" or vehicle.get("FuelUnit") != "0":
        raise ValueError("This version supports metric Fuelio backups only")

    trip_count = 0
    trip_m = Decimal(0)
    month_trip_m = Decimal(0)
    duration_seconds = Decimal(0)
    estimated_trip_cost = Decimal(0)
    last_trip: date | None = None
    odometers: list[Decimal] = []
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
        if (day.year, day.month) == (today.year, today.month) and day <= today:
            month_trip_m += distance
        if day <= today and (last_trip is None or day > last_trip):
            last_trip = day
        for key in ("StartOdo", "EndOdo"):
            odo = _nonnegative(trip.get(key, ""))
            if odo is not None and odo > 0 and day <= today:
                odometers.append(odo)

    fuel_count = 0
    litres = Decimal(0)
    fuel_cost = Decimal(0)
    month_fuel_cost = Decimal(0)
    last_fillup: date | None = None
    last_price: Decimal | None = None
    last_consumption: Decimal | None = None
    last_consumption_day: date | None = None
    for fillup in sections["Log"]:
        day = _date(fillup["Data"])
        volume = _nonnegative(fillup["Fuel (litres)"], default=Decimal(0))
        cost = _nonnegative(fillup["Price (optional)"], default=Decimal(0))
        assert volume is not None and cost is not None
        fuel_count += 1
        if day > today:
            continue
        litres += volume
        fuel_cost += cost
        if (day.year, day.month) == (today.year, today.month):
            month_fuel_cost += cost
        odo = _nonnegative(fillup.get("Odo (km)", ""))
        if odo is not None and odo > 0:
            odometers.append(odo)
        # A blank reading on the newest fill-up must not erase an older real reading.
        reported = _nonnegative(fillup.get("l/100km (optional)", ""))
        if reported is not None and (last_consumption_day is None or day > last_consumption_day):
            last_consumption_day = day
            last_consumption = reported
        if last_fillup is None or day > last_fillup:
            last_fillup = day
            price = _nonnegative(fillup.get("VolumePrice", ""))
            last_price = price if price is not None and price > 0 else (cost / volume if volume else None)

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
        if (day.year, day.month) == (today.year, today.month):
            month_expenses += amount

    def rounded(value: Decimal, places: int = 2) -> float:
        return round(float(value), places)

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
        latest_odometer_km=rounded(max(odometers), 1) if odometers else None,
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
    return parse_backup(text, today=today)
