"""One-time migration to time-aware estimates; synthetic sources only. Remove after applying."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def edit(path, old, new):
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{path}: expected exactly one patch anchor, found {count}: {old[:100]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")

P = 'custom_components/fuelio/parser.py'
C = 'custom_components/fuelio/www/ha-fuelio-card.js'
S = 'custom_components/fuelio/sensor.py'

edit(P, 'import csv\n', 'import csv\nfrom bisect import bisect_left, bisect_right\n')
edit(P, '    odometer_lifetime_coverage: dict\n',
     '    odometer_lifetime_coverage: dict\n    estimated_lifetime: dict\n    latest_two_consumption: float | None\n    latest_two_consumption_count: int\n')
edit(P, '    logged_km_by_month: dict[str, Decimal] = {}\n',
     '    logged_km_by_month: dict[str, Decimal] = {}\n    trip_count_by_month: dict[str, int] = {}\n')
edit(P, '            logged_km_by_month[month_key] = logged_km_by_month.get(month_key, Decimal(0)) + km\n',
     '            logged_km_by_month[month_key] = logged_km_by_month.get(month_key, Decimal(0)) + km\n            trip_count_by_month[month_key] = trip_count_by_month.get(month_key, 0) + 1\n')

# Only values known at the START of each ODO interval can price that interval.
# Fuelio-reported consumption at fill-up describes the previous tank interval,
# but is used here as an estimate for the FOLLOWING observed travel.
anchor = '    def category_rows(values: dict[str, Decimal]) -> list[dict]:\n'
helper = '''    consumption_history = sorted(valid_consumptions, key=lambda item: item[1])
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

'''
edit(P, anchor, helper + anchor)
edit(P, '    odo_month_data = {}\n', '    odo_month_data = {}\n    month_estimates = {}\n')
edit(P, '        odo_month_data[key] = odometer_distance(start, end) if end >= start else (None, {"odo_coverage": "unavailable"})\n',
     '        odo_month_data[key] = odometer_distance(start, end) if end >= start else (None, {"odo_coverage": "unavailable"})\n        km, coverage = odo_month_data[key]\n        month_estimates[key] = estimate_period(start, end, km, coverage)\n')
edit(P, '"km": None, "fuel_ups": 0, "litres": Decimal(0), "categories": {}})',
     '"km": None, "fuel_ups": 0, "litres": Decimal(0), "trip_count": 0, "logged_trip_km": Decimal(0), "categories": {}})')
edit(P, '        year_row["fuel_ups"] += fuel_ups_by_month.get(month, 0)\n',
     '        year_row["fuel_ups"] += fuel_ups_by_month.get(month, 0)\n        year_row["trip_count"] += trip_count_by_month.get(month, 0)\n        year_row["logged_trip_km"] += logged_km_by_month.get(month, Decimal(0))\n')
edit(P, '    year_odo_data = {}\n', '    year_odo_data = {}\n    year_estimates = {}\n')
edit(P, '        year_totals[year]["km"] = year_odo_data[year][0]\n    lifetime_km, lifetime_coverage = odometer_distance(None, today)\n',
     '        year_totals[year]["km"] = year_odo_data[year][0]\n        year_estimates[year] = estimate_period(beginning, ending, *year_odo_data[year])\n    lifetime_km, lifetime_coverage = odometer_distance(None, today)\n    lifetime_estimate = estimate_period(None, today, lifetime_km, lifetime_coverage)\n')
edit(P, '        return {"month": month, "fuel": rounded(values["fuel"]), "other": rounded(values["other"]),\n',
     '        estimate = dict(month_estimates[month])\n        if estimate["estimated_fuel"] is not None:\n            estimate["estimated_total"] = rounded(Decimal(str(estimate["estimated_fuel"])) + values["other"])\n            estimate["estimated_total_per_km"] = per_odometer_km(Decimal(str(estimate["estimated_total"])), km)\n        trip_count_period = trip_count_by_month.get(month, 0)\n        return {"month": month, "fuel": rounded(values["fuel"]), "other": rounded(values["other"]),\n')
edit(P, '                "logged_trip_km": rounded(logged_km_by_month.get(month, Decimal(0)), 3),\n',
     '                "logged_trip_km": rounded(logged_km_by_month.get(month, Decimal(0)), 3),\n                "trip_count": trip_count_period,\n                "average_trip_km": rounded(logged_km_by_month.get(month, Decimal(0)) / trip_count_period, 3) if trip_count_period else None,\n')
edit(P, '                "categories": category_rows(expense_categories_by_month.get(month, {})), **coverage}\n',
     '                "categories": category_rows(expense_categories_by_month.get(month, {})), **coverage, **estimate}\n')
edit(P, '    year_history = tuple(\n',
     '    for year, row in year_totals.items():\n        estimate = year_estimates[year]\n        if estimate["estimated_fuel"] is not None:\n            estimate["estimated_total"] = rounded(Decimal(str(estimate["estimated_fuel"])) + row["other"])\n            estimate["estimated_total_per_km"] = per_odometer_km(Decimal(str(estimate["estimated_total"])), row["km"])\n    if lifetime_estimate["estimated_fuel"] is not None:\n        lifetime_estimate["estimated_total"] = rounded(Decimal(str(lifetime_estimate["estimated_fuel"])) + expenses)\n        lifetime_estimate["estimated_total_per_km"] = per_odometer_km(Decimal(str(lifetime_estimate["estimated_total"])), lifetime_km)\n    year_history = tuple(\n')
edit(P, '         "litres": rounded(row["litres"], 3), "fuel_ups": row["fuel_ups"],\n',
     '         "litres": rounded(row["litres"], 3), "fuel_ups": row["fuel_ups"],\n         "trip_count": row["trip_count"], "logged_trip_km": rounded(row["logged_trip_km"], 3),\n         "average_trip_km": rounded(row["logged_trip_km"] / row["trip_count"], 3) if row["trip_count"] else None,\n')
edit(P, '         "categories": category_rows(row["categories"]), **year_odo_data[year][1]}\n',
     '         "categories": category_rows(row["categories"]), **year_odo_data[year][1], **year_estimates[year]}\n')
edit(P, '        odometer_lifetime_coverage=lifetime_coverage,\n',
     '        odometer_lifetime_coverage=lifetime_coverage,\n        estimated_lifetime=lifetime_estimate,\n        latest_two_consumption=rounded(latest_two_consumption, 3) if latest_two_consumption is not None else None,\n        latest_two_consumption_count=len(latest_values),\n')
edit(S, '                "lifetime_odo_coverage": snapshot.odometer_lifetime_coverage,\n',
     '                "lifetime_odo_coverage": snapshot.odometer_lifetime_coverage,\n                "estimated_lifetime": snapshot.estimated_lifetime,\n                "latest_two_consumption": snapshot.latest_two_consumption,\n                "latest_two_consumption_count": snapshot.latest_two_consumption_count,\n')

# Four grouping panels, readable at narrow card widths, no access to private data.
edit(C, '    :host { display:block; color:', '    :host { display:block; container-type:inline-size; color:')
edit(C, '    .grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }\n',
     '''    .grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }
    .overview { display:grid; grid-template-columns:1fr; gap:12px; }
    .overview-panel { border:1px solid var(--divider-color,#e2e4e8); border-radius:18px; padding:15px; min-width:0; }
    .overview-panel h3 { font-size:1rem; margin:0 0 10px; }
    .overview-row { display:flex; justify-content:space-between; align-items:baseline; flex-wrap:wrap; gap:5px 10px; padding:8px 0; border-top:1px solid var(--divider-color,#e2e4e8); }
    .overview-row:first-of-type { border-top:0; }
    .overview-row .name { color:var(--secondary-text-color,#68727d); font-size:.78rem; }
    .overview-row strong { text-align:right; font-size:.98rem; font-variant-numeric:tabular-nums; overflow-wrap:anywhere; }
    .overview-row .note { width:100%; text-align:right; font-size:.7rem; color:var(--secondary-text-color,#68727d); }
    @container (min-width:540px) { .overview { grid-template-columns:repeat(2,minmax(0,1fr)); } }
''')
edit(C, '    _section(id, icon, title, inner) {\n',
     '''    _panel(icon, title, rows) {
      return `<section class="overview-panel"><h3>${icon} ${esc(title)}</h3>${rows.map(([label, value, note]) =>
        `<div class="overview-row"><span class="name">${esc(label)}</span><strong>${esc(value)}</strong>${note ? `<span class="note">${esc(note)}</span>` : ""}</div>`).join("")}</section>`;
    }
    _section(id, icon, title, inner) {
''')
old_overview = '''      const overview = `<div class="grid">
        ${this._tile("🛣️", "Mätarställning / denna månads körsträcka", decimal(this._value("latest_odometer_km"), "km"), `${decimal(nowMonth?.km, "km denna månad")} · ${odoNote}`)}
        ${this._tile("⛽", "Tankat denna månad", decimal(nowMonth?.litres, "L"))}
        ${this._tile("💳", "Kostnader denna månad", kroner(nowMonth?.total))}
        ${this._tile("📏", "Kostnad/km denna månad", decimal(nowMonth?.total_per_logged_km, "kr/km"), "Avläst ODO, ej resloggens summa")}
      </div>`;'''
new_overview = '''      const currentYearData = allYears.find((item) => String(item.year) === String(nowMonth?.month?.slice(0, 4)));
      const aggregate = this._state("monthly_cost_breakdown")?.attributes || {};
      const lifetime = aggregate.estimated_lifetime || {};
      const coverageText = (row) => row?.estimate_coverage === "missing_rate" ? "Pris-/förbrukningsunderlag saknas" :
        row?.estimate_coverage?.includes?.("one_consumption_value") ? "En förbrukningsavläsning – begränsat underlag" :
        row?.odo_coverage === "partial_start" ? "Delperiod från första mätningen" : "Uppskattning";
      const overview = `<div class="overview">
        ${this._panel("🛣️", "Mätarställning", [
          ["Aktuell", decimal(this._value("latest_odometer_km"), "km")],
          ["Körsträcka denna månad", decimal(nowMonth?.km, "km"), odoNote],
          ["Körsträcka i år", decimal(currentYearData?.km, "km"), currentYearData?.odo_coverage === "partial_start" ? "Delperiod" : ""],
          ["Sedan importstart", decimal(aggregate.lifetime_odometer_km, "km")]
        ])}
        ${this._panel("⛽", "Drivmedel", [
          ["Senaste förbrukning", decimal(this._value("last_reported_consumption"), "L/100 km")],
          ["Tankat denna månad", decimal(nowMonth?.litres, "L")],
          ["Tankat i år", decimal(currentYearData?.litres, "L")],
          ["Löpande snitt", decimal(aggregate.latest_two_consumption, "L/100 km"), `${aggregate.latest_two_consumption_count || 0} giltiga tankningar`]
        ])}
        ${this._panel("💳", "Bokförda utgifter", [
          ["Denna månad", kroner(nowMonth?.total)],
          ["Innevarande år", kroner(currentYearData?.total)]
        ])}
        ${this._panel("📏", "Beräknad körkostnad/km", [
          ["Denna månad", decimal(nowMonth?.estimated_total_per_km, "kr/km"), coverageText(nowMonth)],
          ["Innevarande år", decimal(currentYearData?.estimated_total_per_km, "kr/km"), coverageText(currentYearData)]
        ])}
      </div>`;'''
edit(C, old_overview, new_overview)
edit(C, '      </div><div class="summary"><span><strong>Totalt sedan importstart</strong>',
     '''      </div><div class="section-title">Månadsstatistik · ${esc(selected ? monthName(selected.month) : "Ingen historik")}</div>
      <div class="grid">
        ${this._tile("🛣️", "Avläst körsträcka", decimal(selected?.km, "km"), selected?.odo_coverage === "partial_start" ? "Delperiod" : "ODO-differens")}
        ${this._tile("🚙", "Loggade resor", decimal(selected?.trip_count, "st"))}
        ${this._tile("📏", "Genomsnitt/resa", decimal(selected?.average_trip_km, "km"), "Loggade reskilometer ÷ antal resor")}
      </div><div class="summary"><span><strong>Totalt sedan importstart</strong>''')
edit(C, '      <div class="section-title">Kostnad per avläst ODO-kilometer</div>\n',
     '''      <div class="section-title">Beräknad körkostnad · förbrukat bränsle</div>
      <div class="grid">
        ${this._tile("⛽", "Bränsle · vald månad", kroner(selected?.estimated_fuel))}
        ${this._tile("💳", "Totalt · vald månad", kroner(selected?.estimated_total))}
        ${this._tile("⛽", `Bränsle · ${currentYear}`, kroner(selectedYear?.estimated_fuel))}
        ${this._tile("💳", `Totalt · ${currentYear}`, kroner(selectedYear?.estimated_total))}
        ${this._tile("⛽", "Bränsle · sedan start", kroner(lifetime.estimated_fuel))}
        ${this._tile("💳", "Totalt · sedan start", kroner(lifetime.estimated_total))}
      </div>
      <div class="notice">Beräknad förbrukning med de två senaste giltiga tankningsvärdena tillgängliga vid varje ODO-intervalls början och då senast kända literpris. Ny tankning påverkar bara efterföljande körning. Om underlag saknas för en del av sträckan visas —. En giltig tankning ger begränsat underlag. Övriga utgifter räknas på betalningsdatum. Beräknat, inte bokfört bränsle.</div>
      <div class="section-title">Bokförda utgifter per avläst ODO-kilometer</div>
''')
edit(C, '      <div class="notice">Kostnader ÷ ODO-differens,',
     '      <div class="notice">Bokförda utgifter ÷ ODO-differens,')
edit(C, '      const lifetime = aggregate.estimated_lifetime || {};\n', '      const lifetime = aggregate.estimated_lifetime || {};\n')
# Avoid an unused data value being accidentally rendered as authoritative.
print('Applied time-aware estimation, selected-month trip statistics and responsive overview patch.')
