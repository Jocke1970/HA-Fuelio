"""One-time source patch for odometer-based analytics; synthetic tests only."""
from pathlib import Path

ROOT = Path('custom_components/fuelio')

def replace(path, old, new, *, count=1):
    file = Path(path)
    text = file.read_text(encoding='utf-8')
    actual = text.count(old)
    if actual != count:
        raise RuntimeError(f'{file}: expected {count} anchor(s), got {actual}: {old[:60]}')
    file.write_text(text.replace(old, new), encoding='utf-8')

p = ROOT / 'parser.py'
replace(p, '    odometers: list[Decimal] = []\n', '''    odometers: list[Decimal] = []
    # Date-stamped odometer checkpoints, from tankings and OBD trip boundaries.
    # No trip coordinates, routes, vehicle identifiers or raw rows are retained.
    odometer_by_day: dict[date, list[Decimal]] = {}

    def observe_odometer(day: date, value: Decimal | None) -> None:
        if value is not None and value > 0 and day <= today:
            odometers.append(value)
            odometer_by_day.setdefault(day, []).append(value)
''')
replace(p, '''        for key in ("StartOdo", "EndOdo"):
            odo = _nonnegative(trip.get(key, ""))
            if odo is not None and odo > 0 and day <= today:
                odometers.append(odo)
''', '''        # Use the actual StartDate when present, otherwise the trip's EndDate.
        # Start/EndOdo may straddle a calendar boundary, unlike TripDist.
        start_day = _date(trip["StartDate"]) if trip.get("StartDate", "").strip() else day
        if start_day <= day and day <= today:
            observe_odometer(start_day, _nonnegative(trip.get("StartOdo", "")))
            observe_odometer(day, _nonnegative(trip.get("EndOdo", "")))
''')
replace(p, '''        odo = _nonnegative(fillup.get("Odo (km)", ""))
        if odo is not None and odo > 0:
            odometers.append(odo)
''', '''        observe_odometer(day, _nonnegative(fillup.get("Odo (km)", "")))
''')
replace(p, '    monthly: dict[str, dict[str, Decimal]] = {}\n', '''    monthly: dict[str, dict[str, Decimal]] = {}
''')
replace(p, '''return monthly.setdefault(day.strftime("%Y-%m"), {"fuel": Decimal(0), "other": Decimal(0)})''', '''return monthly.setdefault(day.strftime("%Y-%m"), {"fuel": Decimal(0), "other": Decimal(0), "litres": Decimal(0)})''')
replace(p, '''        bucket(day)["fuel"] += cost
''', '''        bucket(day)["fuel"] += cost
        bucket(day)["litres"] += volume
''')
start = '    # Ratios are per *logged trip km*, not a full-vehicle odometer cost. Match\n'
end = '    def category_rows(values: dict[str, Decimal]) -> list[dict]:\n'
text = p.read_text(encoding='utf-8')
assert text.count(start) == 1 and text.count(end) == 1
left, tail = text.split(start, 1)
_, right = tail.split(end, 1)
new = '''    # A period uses the most recent ODO checkpoint BEFORE its first day and
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

'''
p.write_text(left + new + end + right, encoding='utf-8')
replace(p, '''    month_keys = sorted(set(monthly) | set(logged_km_by_month) | set(fuel_ups_by_month), reverse=True)
''', '''    odo_months = {day.strftime("%Y-%m") for day in odometer_days}
    month_keys = sorted(set(monthly) | set(logged_km_by_month) | set(fuel_ups_by_month) | odo_months, reverse=True)
    odo_month_data = {}
    for key in month_keys:
        year, month = (int(part) for part in key.split("-"))
        start = date(year, month, 1)
        next_month = date(year + (month == 12), (month % 12) + 1, 1)
        end = min(today, next_month.fromordinal(next_month.toordinal() - 1))
        odo_month_data[key] = odometer_distance(start, end) if end >= start else (None, {"odo_coverage": "unavailable"})
''')
# simplify date prior-month-end expression; date.fromordinal is classmethod but clearer import timedelta
replace(p, 'from datetime import date, datetime', 'from datetime import date, datetime, timedelta')
replace(p, 'next_month.fromordinal(next_month.toordinal() - 1)', 'next_month - timedelta(days=1)')
replace(p, '''        year_row = year_totals.setdefault(year, {"fuel": Decimal(0), "other": Decimal(0),
                                           "km": Decimal(0), "fuel_ups": 0, "categories": {}})
        values = monthly.get(month, {"fuel": Decimal(0), "other": Decimal(0)})
''', '''        year_row = year_totals.setdefault(year, {"fuel": Decimal(0), "other": Decimal(0),
                                           "km": None, "fuel_ups": 0, "litres": Decimal(0), "categories": {}})
        values = monthly.get(month, {"fuel": Decimal(0), "other": Decimal(0), "litres": Decimal(0)})
''')
replace(p, '''        year_row["km"] += logged_km_by_month.get(month, Decimal(0))
''', '''        year_row["litres"] += values["litres"]
''')
replace(p, '''    def period_row(month: str) -> dict:
        values = monthly.get(month, {"fuel": Decimal(0), "other": Decimal(0)})
        km = logged_km_by_month.get(month, Decimal(0))
        return {"month": month, "fuel": rounded(values["fuel"]), "other": rounded(values["other"]),
                "total": rounded(values["fuel"] + values["other"]), "km": rounded(km, 3),
                "fuel_ups": fuel_ups_by_month.get(month, 0),
                "fuel_per_logged_km": per_logged_km(values["fuel"], km),
                "total_per_logged_km": per_logged_km(values["fuel"] + values["other"], km),
                "categories": category_rows(expense_categories_by_month.get(month, {}))}
''', '''    year_odo_data = {}
    for year in year_totals:
        beginning = date(int(year), 1, 1)
        ending = min(today, date(int(year), 12, 31))
        year_odo_data[year] = odometer_distance(beginning, ending)
        year_totals[year]["km"] = year_odo_data[year][0]
    lifetime_km, lifetime_coverage = odometer_distance(None, today)

    def period_row(month: str) -> dict:
        values = monthly.get(month, {"fuel": Decimal(0), "other": Decimal(0), "litres": Decimal(0)})
        km, coverage = odo_month_data[month]
        return {"month": month, "fuel": rounded(values["fuel"]), "other": rounded(values["other"]),
                "total": rounded(values["fuel"] + values["other"]), "km": rounded(km, 3) if km is not None else None,
                "logged_trip_km": rounded(logged_km_by_month.get(month, Decimal(0)), 3),
                "litres": rounded(values["litres"], 3), "fuel_ups": fuel_ups_by_month.get(month, 0),
                "fuel_per_logged_km": per_odometer_km(values["fuel"], km),
                "total_per_logged_km": per_odometer_km(values["fuel"] + values["other"], km),
                "categories": category_rows(expense_categories_by_month.get(month, {})), **coverage}
''')
replace(p, '''         "total": rounded(row["fuel"] + row["other"]), "km": rounded(row["km"], 3),
         "fuel_ups": row["fuel_ups"],
         "fuel_per_logged_km": per_logged_km(row["fuel"], row["km"]),
         "total_per_logged_km": per_logged_km(row["fuel"] + row["other"], row["km"]),
         "categories": category_rows(row["categories"])}
''', '''         "total": rounded(row["fuel"] + row["other"]),
         "km": rounded(row["km"], 3) if row["km"] is not None else None,
         "litres": rounded(row["litres"], 3), "fuel_ups": row["fuel_ups"],
         "fuel_per_logged_km": per_odometer_km(row["fuel"], row["km"]),
         "total_per_logged_km": per_odometer_km(row["fuel"] + row["other"], row["km"]),
         "categories": category_rows(row["categories"]), **year_odo_data[year][1]}
''')
replace(p, '''    current = year_totals.get(str(today.year), {"fuel": Decimal(0), "other": Decimal(0),
                                                "km": Decimal(0), "fuel_ups": 0})
    this_month = today.strftime("%Y-%m")
    month_km = logged_km_by_month.get(this_month, Decimal(0))
''', '''    current = year_totals.get(str(today.year), {"fuel": Decimal(0), "other": Decimal(0),
                                                "km": None, "fuel_ups": 0})
    this_month = today.strftime("%Y-%m")
    month_km = odo_month_data[this_month][0]
''')
replace(p, '''fuel_cost_per_km_month=per_logged_km(month_fuel_cost, month_km),
        total_cost_per_km_month=per_logged_km(month_fuel_cost + month_expenses, month_km),
        fuel_cost_per_km_year=per_logged_km(current["fuel"], current["km"]),
        total_cost_per_km_year=per_logged_km(current["fuel"] + current["other"], current["km"]),
        fuel_cost_per_km_all=per_logged_km(fuel_cost, logged_km_total),
        total_cost_per_km_all=per_logged_km(fuel_cost + expenses, logged_km_total),''', '''fuel_cost_per_km_month=per_odometer_km(month_fuel_cost, month_km),
        total_cost_per_km_month=per_odometer_km(month_fuel_cost + month_expenses, month_km),
        fuel_cost_per_km_year=per_odometer_km(current["fuel"], current["km"]),
        total_cost_per_km_year=per_odometer_km(current["fuel"] + current["other"], current["km"]),
        fuel_cost_per_km_all=per_odometer_km(fuel_cost, lifetime_km),
        total_cost_per_km_all=per_odometer_km(fuel_cost + expenses, lifetime_km),''')
# Expose aggregate lifetime range only, and document period data basis.
replace(p, '''    monthly_history_truncated: bool
''', '''    monthly_history_truncated: bool
    odometer_lifetime_km: float | None
    odometer_lifetime_coverage: dict
''')
replace(p, '''        monthly_history_truncated=truncated,
''', '''        monthly_history_truncated=truncated,
        odometer_lifetime_km=rounded(lifetime_km, 3) if lifetime_km is not None else None,
        odometer_lifetime_coverage=lifetime_coverage,
''')

p = ROOT / 'sensor.py'
replace(p, '''    # Distance denominator: trips actually logged in the same period, not all odometer travel.
''', '''    # Keep stable unique keys/legacy entity IDs, but use OBD/tanking ODO deltas as denominator.
''')
replace(p, '''name="Fuel cost per logged km''', '''name="Fuel cost per odometer km''', count=3)
replace(p, '''name="Total cost per logged km''', '''name="Total cost per odometer km''', count=3)
replace(p, '''                "distance_basis": "logged_trips_only",
''', '''                "distance_basis": "odometer_checkpoints",
                "lifetime_odometer_km": snapshot.odometer_lifetime_km,
                "lifetime_odo_coverage": snapshot.odometer_lifetime_coverage,
''')

p = ROOT / 'www/ha-fuelio-card.js'
replace(p, '0.1.0-beta.6', '0.1.0-beta.7', count=2)
replace(p, '''      const overview = `<div class="grid">
        ${this._tile("🛣️", "Mätarställning", decimal(this._value("latest_odometer_km"), "km"))}
        ${this._tile("⛽", "Senaste förbrukning", decimal(this._value("last_reported_consumption"), "L/100 km"))}
        ${this._tile("💰", "Literpris", decimal(this._value("last_fuel_price"), "kr/L"))}
        ${this._tile("💳", "Faktisk kostnad", kroner(this._value("total_actual_cost")))}
      </div>`;
''', '''      // The overview is always the CURRENT calendar month, independent of the
      // user's separate historical month selector in the Costs section.
      const nowMonth = allMonths[0];
      const odoNote = nowMonth?.odo_coverage === "partial_start" ? "Delmånad: första tillgängliga avläsning" :
        nowMonth?.odo_start_on && nowMonth?.odo_end_on ? `${nowMonth.odo_start_on} → ${nowMonth.odo_end_on}` : "Avläsningar saknas";
      const overview = `<div class="grid">
        ${this._tile("🛣️", "Mätarställning / denna månads körsträcka", decimal(this._value("latest_odometer_km"), "km"), `${decimal(nowMonth?.km, "km denna månad")} · ${odoNote}`)}
        ${this._tile("⛽", "Tankat denna månad", decimal(nowMonth?.litres, "L"))}
        ${this._tile("💳", "Kostnader denna månad", kroner(nowMonth?.total))}
        ${this._tile("📏", "Kostnad/km denna månad", decimal(nowMonth?.total_per_logged_km, "kr/km"), "Avläst ODO, ej resloggens summa")}
      </div>`;
''')
replace(p, '''        ${this._tile("📉", "Uppskattad körkostnad", kroner(this._value("estimated_trip_cost")), "Hela exporten · ej faktisk utgift")}
''', '')
replace(p, '''      </div><div class="summary"><span><strong>Totalt sedan importstart</strong>''', '''      </div><div class="summary"><span><strong>Totalt sedan importstart</strong>''')
replace(p, '''      <div class="section-title">Kostnad per registrerad reskilometer</div>
''', '''      <div class="summary"><span>Uppskattad resekostnad · hela importen (inte faktisk utgift)</span><strong>${esc(kroner(this._value("estimated_trip_cost")))}</strong></div>
      <div class="section-title">Kostnad per avläst ODO-kilometer</div>
''')
replace(p, '''      <div class="notice">Kostnader ÷ registrerade reskilometer under samma kalenderperiod. Ej bilens exakta kr/km om resloggen är ofullständig. Saknas registrerade km visas —. En ny tankning uppdaterar beloppen vid nästa ZIP-inläsning.</div>
''', '''      <div class="notice">Kostnader ÷ ODO-differens, från senaste avläsning före periodstart till senaste inom perioden. Saknas tidigare avläsning räknas bara körning efter första avläsningen och perioden markeras som ofullständig. Saknas användbar differens visas —. Tankningar uppdaterar belopp och mätarställning vid nästa ZIP-inläsning.</div>
''')
# Frontend already displays fuel and price in the Fuel section.

p = ROOT / 'manifest.json'
replace(p, '"version": "0.1.0-beta.6"', '"version": "0.1.0-beta.7"')

p = Path('tests/test_cost_analytics.py')
replace(p, '''        self.assertEqual(month["km"], 18)
''', '''        self.assertEqual(month["km"], 126)  # Last August ODO 902 to September 1028.
        self.assertEqual(month["logged_trip_km"], 18)  # Sanity check only.
        self.assertEqual(month["litres"], 50)
        self.assertEqual(month["odo_coverage"], "prior_checkpoint")
        self.assertEqual(month["odo_start_on"], "2026-08-18")
        self.assertEqual(month["odo_end_on"], "2026-09-18")
''')
replace(p, '''round(1000 / 18, 3)''', '''round(1000 / 126, 3)''')
replace(p, '''round(1200 / 18, 3)''', '''round(1200 / 126, 3)''')
replace(p, '''        self.assertEqual(year["km"], 20)
        self.assertEqual(result.fuel_cost_per_km_year, 90)
        self.assertEqual(result.total_cost_per_km_all, 100)
''', '''        self.assertEqual(year["km"], 128)  # First imported 900 to latest 1028.
        self.assertEqual(year["odo_coverage"], "partial_start")
        self.assertEqual(result.fuel_cost_per_km_year, round(1800 / 128, 3))
        self.assertEqual(result.total_cost_per_km_all, round(2000 / 128, 3))
''')
replace(p, '''    def test_zero_logged_km_produces_no_ratio(self):
        csv = self.fixture().replace(",18000,1800,20,", ",0,1800,20,").replace(",2000,360,5,", ",0,360,5,")
        result = parser.parse_backup(csv, today=date(2026, 9, 21))
        self.assertIsNone(result.fuel_cost_per_km_month)
        self.assertIsNone(result.total_cost_per_km_all)
''', '''    def test_missing_odometer_readings_produce_no_ratio(self):
        csv = self.fixture().replace(",1010,1028", ",,").replace(",900,902", ",,")
        csv = csv.replace("11:00,1000,50", "11:00,,50").replace("11:00,900,40", "11:00,,40")
        result = parser.parse_backup(csv, today=date(2026, 9, 21))
        self.assertIsNone(result.fuel_cost_per_km_month)
        self.assertIsNone(result.total_cost_per_km_all)
        self.assertIsNone(result.monthly_cost_history[0]["km"])

    def test_odometer_includes_unlogged_miles_and_uses_prior_boundary(self):
        # TripDist intentionally disagrees with ODO. Never use sum(TripDist).
        csv = self.fixture().replace("18000,1800,20", "1000,1800,20")
        result = parser.parse_backup(csv, today=date(2026, 9, 21))
        self.assertEqual(result.monthly_cost_history[0]["km"], 126)
        self.assertEqual(result.monthly_cost_history[0]["logged_trip_km"], 1)
        self.assertEqual(result.fuel_cost_per_km_month, round(1000 / 126, 3))

    def test_first_imported_month_is_marked_partial_not_fabricated(self):
        result = parser.parse_backup(self.fixture(), today=date(2026, 9, 21))
        august = next(row for row in result.monthly_cost_history if row["month"] == "2026-08")
        self.assertEqual(august["km"], 2)
        self.assertEqual(august["odo_coverage"], "partial_start")
        self.assertEqual(result.odometer_lifetime_km, 128)

    def test_new_fuel_up_changes_litres_and_odo_ratio(self):
        csv = self.fixture()
        before = parser.parse_backup(csv, today=date(2026, 9, 21))
        updated = csv.replace("2026-09-10 11:00,1000,50,1000,20,6", "2026-09-10 11:00,1015,55,1200,20,6")
        after = parser.parse_backup(updated, today=date(2026, 9, 21))
        self.assertEqual(before.monthly_cost_history[0]["litres"], 50)
        self.assertEqual(after.monthly_cost_history[0]["litres"], 55)
        self.assertGreater(after.fuel_cost_per_km_month, before.fuel_cost_per_km_month)
''')
# Refuel ODO=1015 does not change latest 1028; price change increases ratio. Fine.

p = Path('tests/test_extrema.py')
replace(p, '''self.assertEqual(len(keys), 36)''', '''self.assertEqual(len(keys), 36)''') if False else None

p = Path('RELEASE_NOTES.md')
s = p.read_text(encoding='utf-8')
s = '''# HA-Fuelio v0.1.0-beta.7 🚙

Odometer semantics and overview fix for real-HA testing.

- Calculate month/year/import-lifetime fuel and actual-total SEK/km using ODO checkpoints from Fuelio fuel-ups and OBD trip StartOdo/EndOdo, not sum of TripDist. For each calendar period, last observation before period start is the baseline; end is latest observation inside period. If no pre-period checkpoint exists, start at the earliest in-period reading and mark `odo_coverage: partial_start`. No usable readings or rollback yields `unknown` rather than invented distance.
- Monthly breakdown attributes include `km` (observed odometer difference), `litres`, `logged_trip_km` (sanity check), and checkpoint dates/coverage. Category amounts and bounded aggregates remain. 36 unique sensor keys and IDs retained, including legacy `_logged_km` entity IDs; human-facing names clarify odometer basis.
- Header shows odometer plus current-month ODO delta, current-month litres, current-month actual expenditure and total SEK/ODO-km. It never follows the historical cost month selector. Fuel consumption/price remain in the Fuel section. Move whole-export estimated trip cost to its own explicitly non-actual summary.
- No automatic Drive download or stable main promotion. A nearest checkpoint can lie before the calendar boundary; these are observed-distance period allocations, not exact midnight readings. Validate against private Fuelio and real HA.

Upgrade HACS, reboot HA, re-copy card JS into `/config/www/ha-fuelio-card.js`, change the EXISTING sole module resource to `/local/ha-fuelio-card.js?v=0.1.0-beta.7` and hard refresh. Keep YAML and local ZIP unchanged. Verify 36 sensors and test monthly transitions.
'''+s
p.write_text(s, encoding='utf-8')

print('Patched odometer aggregation, overview, and synthetic regression tests.')
