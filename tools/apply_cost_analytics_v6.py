"""One-time synthetic-data-only source patch; runs in CI, never reads a private ZIP."""
from pathlib import Path


def replace(path, old, new):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    assert count == 1, f"Expected one occurrence in {path}, found {count}: {old[:70]!r}"
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


parser = "custom_components/fuelio/parser.py"
sensor = "custom_components/fuelio/sensor.py"
card = "custom_components/fuelio/www/ha-fuelio-card.js"
replace(parser, '    monthly_history_truncated: bool\n', '''    monthly_history_truncated: bool
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
''')
replace(parser, '    odometers: list[Decimal] = []\n', '''    odometers: list[Decimal] = []
    logged_km_by_month: dict[str, Decimal] = {}
    logged_km_total = Decimal(0)
''')
replace(parser, '        estimated_trip_cost += estimate\n', '''        estimated_trip_cost += estimate
        if day <= today:
            month_key = day.strftime("%Y-%m")
            km = distance / 1000
            logged_km_by_month[month_key] = logged_km_by_month.get(month_key, Decimal(0)) + km
            logged_km_total += km
''')
replace(parser, '    fuel_count = 0\n    litres = Decimal(0)\n', '''    fuel_count = 0
    fuel_ups_by_month: dict[str, int] = {}
    litres = Decimal(0)
''')
replace(parser, '''        fuel_count += 1
        if day > today:
            continue
        litres += volume
''', '''        if day > today:
            continue
        fuel_count += 1
        month_key = day.strftime("%Y-%m")
        fuel_ups_by_month[month_key] = fuel_ups_by_month.get(month_key, 0) + 1
        litres += volume
''')
replace(parser, '    expense_count = 0\n    expenses = Decimal(0)\n', '''    # CostCategories maps private internal IDs to display labels. Never expose IDs,
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
''')
replace(parser, '''        expenses += amount
        bucket(day)["other"] += amount
''', '''        expenses += amount
        bucket(day)["other"] += amount
        month_key = day.strftime("%Y-%m")
        label = category_names.get(record.get("CostTypeID", "").strip(), "Okategoriserat")
        categories = expense_categories_by_month.setdefault(month_key, {})
        categories[label] = categories.get(label, Decimal(0)) + amount
''')
start = '''    # Always include the current month in the selector, even if there are no costs.
    bucket(today)
    month_keys = sorted(monthly, reverse=True)
    truncated = len(month_keys) > MAX_MONTHS_IN_ATTRIBUTES
    history = tuple(
        {"month": key, "fuel": rounded(monthly[key]["fuel"]),
         "other": rounded(monthly[key]["other"]),
         "total": rounded(monthly[key]["fuel"] + monthly[key]["other"])}
        for key in month_keys[:MAX_MONTHS_IN_ATTRIBUTES]
    )
'''
repl = '''    # Ratios are per *logged trip km*, not a full-vehicle odometer cost. Match
    # calendar periods of expenses and trips; zero km must NEVER become zero kr/km.
    def per_logged_km(cost: Decimal, km: Decimal) -> float | None:
        return rounded(cost / km, 3) if km > 0 else None

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
    month_keys = sorted(set(monthly) | set(logged_km_by_month) | set(fuel_ups_by_month), reverse=True)
    year_totals: dict[str, dict] = {}
    all_categories: dict[str, Decimal] = {}
    for month in month_keys:
        year = month[:4]
        year_row = year_totals.setdefault(year, {"fuel": Decimal(0), "other": Decimal(0),
                                           "km": Decimal(0), "fuel_ups": 0, "categories": {}})
        values = monthly.get(month, {"fuel": Decimal(0), "other": Decimal(0)})
        year_row["fuel"] += values["fuel"]
        year_row["other"] += values["other"]
        year_row["km"] += logged_km_by_month.get(month, Decimal(0))
        year_row["fuel_ups"] += fuel_ups_by_month.get(month, 0)
        for label, amount in expense_categories_by_month.get(month, {}).items():
            year_row["categories"][label] = year_row["categories"].get(label, Decimal(0)) + amount
            all_categories[label] = all_categories.get(label, Decimal(0)) + amount

    def period_row(month: str) -> dict:
        values = monthly.get(month, {"fuel": Decimal(0), "other": Decimal(0)})
        km = logged_km_by_month.get(month, Decimal(0))
        return {"month": month, "fuel": rounded(values["fuel"]), "other": rounded(values["other"]),
                "total": rounded(values["fuel"] + values["other"]), "km": rounded(km, 3),
                "fuel_ups": fuel_ups_by_month.get(month, 0),
                "fuel_per_logged_km": per_logged_km(values["fuel"], km),
                "total_per_logged_km": per_logged_km(values["fuel"] + values["other"], km),
                "categories": category_rows(expense_categories_by_month.get(month, {}))}

    truncated = len(month_keys) > MAX_MONTHS_IN_ATTRIBUTES
    history = tuple(period_row(key) for key in month_keys[:MAX_MONTHS_IN_ATTRIBUTES])
    year_history = tuple(
        {"year": year, "fuel": rounded(row["fuel"]), "other": rounded(row["other"]),
         "total": rounded(row["fuel"] + row["other"]), "km": rounded(row["km"], 3),
         "fuel_ups": row["fuel_ups"],
         "fuel_per_logged_km": per_logged_km(row["fuel"], row["km"]),
         "total_per_logged_km": per_logged_km(row["fuel"] + row["other"], row["km"]),
         "categories": category_rows(row["categories"])}
        for year, row in sorted(year_totals.items(), reverse=True)[:40]
    )
    current = year_totals.get(str(today.year), {"fuel": Decimal(0), "other": Decimal(0),
                                                "km": Decimal(0), "fuel_ups": 0})
    this_month = today.strftime("%Y-%m")
    month_km = logged_km_by_month.get(this_month, Decimal(0))
'''
replace(parser, start, repl)
replace(parser, '''        monthly_history_truncated=truncated,
''', '''        monthly_history_truncated=truncated,
        yearly_cost_history=year_history,
        all_cost_categories=tuple(category_rows(all_categories)),
        fuel_count_month=fuel_ups_by_month.get(this_month, 0),
        fuel_count_year=current["fuel_ups"],
        fuel_cost_per_km_month=per_logged_km(month_fuel_cost, month_km),
        total_cost_per_km_month=per_logged_km(month_fuel_cost + month_expenses, month_km),
        fuel_cost_per_km_year=per_logged_km(current["fuel"], current["km"]),
        total_cost_per_km_year=per_logged_km(current["fuel"] + current["other"], current["km"]),
        fuel_cost_per_km_all=per_logged_km(fuel_cost, logged_km_total),
        total_cost_per_km_all=per_logged_km(fuel_cost + expenses, logged_km_total),
''')
replace(sensor, '''    # Eight real-observation extremes. Attribute recorded_on is the newest date on ties.
''', '''    # Six explicit calendar/lifetime ratios and two period-specific fill-up counters.
    # Distance denominator: trips actually logged in the same period, not all odometer travel.
    FuelioSensorDescription(key="fuel_count_month", name="Fuel-ups this month", icon="mdi:gas-station"),
    FuelioSensorDescription(key="fuel_count_year", name="Fuel-ups this year", icon="mdi:gas-station"),
    FuelioSensorDescription(key="fuel_cost_per_km_month", name="Fuel cost per logged km this month", native_unit_of_measurement="SEK/km", icon="mdi:cash"),
    FuelioSensorDescription(key="total_cost_per_km_month", name="Total cost per logged km this month", native_unit_of_measurement="SEK/km", icon="mdi:cash-multiple"),
    FuelioSensorDescription(key="fuel_cost_per_km_year", name="Fuel cost per logged km this year", native_unit_of_measurement="SEK/km", icon="mdi:cash"),
    FuelioSensorDescription(key="total_cost_per_km_year", name="Total cost per logged km this year", native_unit_of_measurement="SEK/km", icon="mdi:cash-multiple"),
    FuelioSensorDescription(key="fuel_cost_per_km_all", name="Fuel cost per logged km since import start", native_unit_of_measurement="SEK/km", icon="mdi:cash"),
    FuelioSensorDescription(key="total_cost_per_km_all", name="Total cost per logged km since import start", native_unit_of_measurement="SEK/km", icon="mdi:cash-multiple"),
    # Eight real-observation extremes. Attribute recorded_on is the newest date on ties.
''')
replace(sensor, '''                "months": list(snapshot.monthly_cost_history),
                "history_truncated": snapshot.monthly_history_truncated,
''', '''                "months": list(snapshot.monthly_cost_history),
                "years": list(snapshot.yearly_cost_history),
                "categories_all": list(snapshot.all_cost_categories),
                "distance_basis": "logged_trips_only",
                "history_truncated": snapshot.monthly_history_truncated,
''')

# Preserve existing sensor ID lookup; add only the eight new name-derived slugs.
replace(card, '''  monthly_cost_breakdown: "monthly_cost_breakdown",
''', '''  fuel_count_month: "fuel_ups_this_month", fuel_count_year: "fuel_ups_this_year",
  fuel_cost_per_km_month: "fuel_cost_per_logged_km_this_month",
  total_cost_per_km_month: "total_cost_per_logged_km_this_month",
  fuel_cost_per_km_year: "fuel_cost_per_logged_km_this_year",
  total_cost_per_km_year: "total_cost_per_logged_km_this_year",
  fuel_cost_per_km_all: "fuel_cost_per_logged_km_since_import_start",
  total_cost_per_km_all: "total_cost_per_logged_km_since_import_start",
  monthly_cost_breakdown: "monthly_cost_breakdown",
''')
replace(card, '''"fuel_litres", "fuel_cost", "other_expenses", "total_actual_cost", "estimated_trip_cost", "last_trip_date",
''', '''"fuel_litres", "fuel_cost", "other_expenses", "total_actual_cost", "estimated_trip_cost", "last_trip_date",
        "fuel_count_month", "fuel_count_year", "fuel_cost_per_km_month", "total_cost_per_km_month",
        "fuel_cost_per_km_year", "total_cost_per_km_year", "fuel_cost_per_km_all", "total_cost_per_km_all",
''')
replace(card, '''JSON.stringify(entry.attributes?.months || [])''', '''JSON.stringify([entry.attributes?.months || [], entry.attributes?.years || [], entry.attributes?.categories_all || []])''')
replace(card, '''      const currentYear = allMonths[0]?.month?.slice(0, 4) || String(new Date().getFullYear());
      const yearTotal = allMonths.filter((item) => item.month.startsWith(`${currentYear}-`)).reduce((sum, item) => sum + item.total, 0);
''', '''      const currentYear = selected?.month?.slice(0, 4) || allMonths[0]?.month?.slice(0, 4) || String(new Date().getFullYear());
      const allYears = this._state("monthly_cost_breakdown")?.attributes?.years || [];
      const selectedYear = Array.isArray(allYears) ? allYears.find((item) => String(item.year) === currentYear) : null;
      const yearTotal = selectedYear?.total ?? allMonths.filter((item) => item.month.startsWith(`${currentYear}-`)).reduce((sum, item) => sum + item.total, 0);
      const categories = (values, heading) => `<div class="section-title">${esc(heading)}</div>${Array.isArray(values) && values.length ? `<div class="category-list">${values.map((item) => `<div class="category-row"><span>${esc(item.name)}</span><strong>${esc(kroner(item.amount))}</strong></div>`).join("")}</div>` : `<div class="notice">Inga kategoriserade utgifter för perioden.</div>`}`;
''')
replace(card, '''    .small { font-size:.75rem; } .foot { text-align:right; margin-top:12px; }
    @media (min-width:620px) { .shell { padding:20px; } .grid { grid-template-columns:repeat(4,minmax(0,1fr)); } .records { grid-template-columns:repeat(4,minmax(0,1fr)); } }
''', '''    .small { font-size:.75rem; } .foot { text-align:right; margin-top:12px; }
    .category-list { border:1px solid var(--divider-color,#e2e4e8); border-radius:14px; padding:4px 12px; }
    .category-row { display:flex; justify-content:space-between; gap:12px; padding:9px 0; border-bottom:1px solid var(--divider-color,#e2e4e8); font-size:.84rem; }
    .category-row:last-child { border:0; } .category-row strong { white-space:nowrap; font-variant-numeric:tabular-nums; }
    @media (min-width:850px) { .shell { padding:20px; } .grid { grid-template-columns:repeat(4,minmax(0,1fr)); } .records { grid-template-columns:repeat(4,minmax(0,1fr)); } }
''')
replace(card, '''${this._tile("🧾", "Tankningar", decimal(this._value("fuel_count"), "st"))}''', '''${this._tile("💳", "Faktisk kostnad", kroner(this._value("total_actual_cost")))}''')
replace(card, '''      ${historyTruncated ? `<div class="notice">Månadsväljaren visar de senaste 120 månaderna. Livstidssumman inkluderar även äldre data.</div>` : ""}`;
''', '''      ${categories(selected?.categories, "Utgifter per kategori · vald månad")}
      ${categories(selectedYear?.categories, `Utgifter per kategori · år ${currentYear}`)}
      <div class="section-title">Kostnad per registrerad reskilometer</div>
      <div class="grid">
        ${this._tile("⛽", "Bränsle · månad", decimal(selected?.fuel_per_logged_km, "kr/km"))}
        ${this._tile("💳", "Totalt · månad", decimal(selected?.total_per_logged_km, "kr/km"))}
        ${this._tile("⛽", `Bränsle · ${currentYear}`, decimal(selectedYear?.fuel_per_logged_km, "kr/km"))}
        ${this._tile("💳", `Totalt · ${currentYear}`, decimal(selectedYear?.total_per_logged_km, "kr/km"))}
        ${this._tile("⛽", "Bränsle · sedan start", decimal(this._value("fuel_cost_per_km_all"), "kr/km"))}
        ${this._tile("💳", "Totalt · sedan start", decimal(this._value("total_cost_per_km_all"), "kr/km"))}
      </div>
      <div class="notice">Kostnader ÷ registrerade reskilometer under samma kalenderperiod. Ej bilens exakta kr/km om resloggen är ofullständig. Saknas registrerade km visas —. En ny tankning uppdaterar beloppen vid nästa ZIP-inläsning.</div>
      ${historyTruncated ? `<div class="notice">Månadsväljaren visar de senaste 120 månaderna. Livstidssumman inkluderar även äldre data.</div>` : ""}`;
''')
replace(card, '''        ${this._tile("📆", "Senaste tankning", date(this._state("last_fillup_date")?.state))}
      </div>`;
''', '''        ${this._tile("📆", "Senaste tankning", date(this._state("last_fillup_date")?.state))}
      </div><div class="section-title">Antal tankningar</div><div class="grid">
        ${this._tile("📅", "Vald månad", decimal(selected?.fuel_ups, "st"))}
        ${this._tile("🗓️", `År ${currentYear}`, decimal(selectedYear?.fuel_ups, "st"))}
        ${this._tile("⛽", "Sedan importstart", decimal(this._value("fuel_count"), "st"))}
      </div>`;
''')
replace(card, '0.1.0-beta.5', '0.1.0-beta.6')
replace('custom_components/fuelio/manifest.json', '"version": "0.1.0-beta.5"', '"version": "0.1.0-beta.6"')

Path('tests/test_cost_analytics.py').write_text('''"""Synthetic test records only; no private Fuelio exports in the repository."""
from datetime import date
from decimal import Decimal
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cost_analytics_parser", ROOT / "custom_components/fuelio/parser.py")
parser = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parser
spec.loader.exec_module(parser)
from test_parser import sample_csv


class CostAnalyticsTests(unittest.TestCase):
    def fixture(self):
        csv = sample_csv()
        self.assertIn("## Costs\\r\\n", csv)
        csv = csv.replace("## Costs\\r\\n", "## CostCategories\\r\\nCostTypeID,Name,priority,color,guid,lastupdated\\r\\n7,Parkering,0,0,,\\r\\n8,Tvätt,0,0,,\\r\\n## Costs\\r\\n", 1)
        csv = csv.replace("Date,Cost,isTemplate,isIncome\\r\\n", "Date,Cost,isTemplate,isIncome,CostTypeID\\r\\n", 1)
        for before, after in (("2026-09-25 12:00,500,0,0", "2026-09-25 12:00,500,0,0,7"),
                              ("2026-09-15 12:00,200,0,0", "2026-09-15 12:00,200,0,0,7"),
                              ("2026-09-12 12:00,5000,1,0", "2026-09-12 12:00,5000,1,0,8"),
                              ("2026-09-12 12:00,100,0,1", "2026-09-12 12:00,100,0,1,8")):
            self.assertIn(before, csv)
            csv = csv.replace(before, after, 1)
        return csv

    def test_month_year_lifetime_and_category_join(self):
        result = parser.parse_backup(self.fixture(), today=date(2026, 9, 21))
        self.assertEqual(result.fuel_count_month, 1)
        self.assertEqual(result.fuel_count_year, 2)
        month = result.monthly_cost_history[0]
        self.assertEqual(month["month"], "2026-09")
        self.assertEqual(month["km"], 18)
        self.assertEqual(month["categories"], [{"name": "Parkering", "amount": 200}])
        self.assertEqual(month["fuel_per_logged_km"], round(1000 / 18, 3))
        self.assertEqual(month["total_per_logged_km"], round(1200 / 18, 3))
        year = result.yearly_cost_history[0]
        self.assertEqual(year["total"], 2000)
        self.assertEqual(year["km"], 20)
        self.assertEqual(result.fuel_cost_per_km_year, 90)
        self.assertEqual(result.total_cost_per_km_all, 100)
        self.assertEqual(list(result.all_cost_categories), [{"name": "Parkering", "amount": 200}])
        self.assertNotIn("CostTypeID", repr(result))

    def test_changed_fuel_price_updates_ratios_without_cached_value(self):
        original = parser.parse_backup(self.fixture(), today=date(2026, 9, 21))
        changed = parser.parse_backup(self.fixture().replace("2026-09-10 11:00,1000,50,1000,20,6", "2026-09-10 11:00,1000,50,1200,20,6"), today=date(2026, 9, 21))
        self.assertGreater(changed.fuel_cost_per_km_month, original.fuel_cost_per_km_month)
        self.assertGreater(changed.total_cost_per_km_all, original.total_cost_per_km_all)

    def test_zero_logged_km_produces_no_ratio(self):
        csv = self.fixture().replace(",18000,1800,20,", ",0,1800,20,").replace(",2000,360,5,", ",0,360,5,")
        result = parser.parse_backup(csv, today=date(2026, 9, 21))
        self.assertIsNone(result.fuel_cost_per_km_month)
        self.assertIsNone(result.total_cost_per_km_all)

    def test_missing_category_table_falls_back_to_uncategorized(self):
        result = parser.parse_backup(sample_csv(), today=date(2026, 9, 21))
        self.assertEqual(list(result.all_cost_categories), [{"name": "Okategoriserat", "amount": 200}])


if __name__ == "__main__":
    unittest.main()
''', encoding='utf-8')

Path('tests/test_cost_frontend.mjs').write_text('''// Test the actual extension using synthetic mixed-prefix HA entities.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
const source = readFileSync('custom_components/fuelio/www/ha-fuelio-card.js', 'utf8');
const classes = new Map();
class E { attachShadow() { this.shadowRoot = { innerHTML: '', addEventListener: () => {} }; return this.shadowRoot; } }
const sandbox = vm.createContext({ HTMLElement: E, customElements: { get: (key) => classes.get(key), define: (key, c) => classes.set(key, c) }, window: { customCards: [] } });
new vm.Script(source).runInContext(sandbox);
const card = new (classes.get('ha-fuelio-card'))();
card.setConfig({ entity: 'sensor.mmk912_monthly_cost_breakdown' });
const states = {}, entities = {};
const add = (id, key, value, attributes = {}) => {
  states[id] = { state: String(value), attributes, last_updated: '2026-09-21T21:00:00Z' };
  entities[id] = { entity_id: id, platform: 'fuelio', device_id: 'test-device', unique_id: `test-entry_${key}` };
};
add('sensor.mmk912_last_fuel_price', 'last_fuel_price', 20);
add('sensor.mmk912_fuel_ups', 'fuel_count', 3);
add('sensor.externa_sensorer_fuelio_vehicle_monthly_cost_breakdown', 'monthly_cost_breakdown', 1200, {
  months: [{ month: '2026-09', fuel: 1000, other: 200, total: 1200, km: 100, fuel_ups: 1,
    fuel_per_logged_km: 10, total_per_logged_km: 12, categories: [{ name: 'Parkering', amount: 200 }] }],
  years: [{ year: '2026', fuel: 2000, other: 200, total: 2200, km: 200, fuel_ups: 2,
    fuel_per_logged_km: 10, total_per_logged_km: 11, categories: [{ name: 'Parkering', amount: 200 }] }],
  categories_all: [{ name: 'Parkering', amount: 200 }]
});
add('sensor.externa_sensorer_fuelio_vehicle_fuel_cost_per_logged_km_since_import_start', 'fuel_cost_per_km_all', 9);
add('sensor.externa_sensorer_fuelio_vehicle_total_cost_per_logged_km_since_import_start', 'total_cost_per_km_all', 12);
card.hass = { states, entities };
const html = card.shadowRoot.innerHTML;
assert.match(html, /Parkering/);
assert.match(html, /Bränsle · månad/);
assert.match(html, /10 kr\/km/);
assert.match(html, /12 kr\/km/);
assert.match(html, /Antal tankningar/);
assert.match(html, /0\.1\.0-beta\.6/);
console.log('PASS: categorized costs, period-specific kr/km and fuel-ups render with mixed entity IDs');
''', encoding='utf-8')

Path('RELEASE_NOTES.md').write_text('''# HA-Fuelio v0.1.0-beta.6 🚙

Experimental period analytics release based on the beta.5 dashboard tests.

- Add six read-only SEK/km sensors: fuel and all actual spending for current calendar month, calendar year, and full imported history. Denominator is **logged trip km in the SAME period**, not total vehicle mileage. No logged km yields `unknown`, not zero. A new valid ZIP updates ratios on the existing five-minute polling cycle.
- Add current month and year fill-up count sensors; lifetime fill-up count remains existing stable sensor. Future-dated fill-ups are not counted.
- Parse optional `CostCategories` (`CostTypeID` → `Name`) and join actual `Costs.CostTypeID`; exclude templates, incomes and future expenses. Unknown category ID or missing section is `Okategoriserat`. Expose only aggregated name/amount, never private cost titles, notes, category internal IDs or raw rows.
- Monthly cost breakdown attributes now include logged km, fuel-ups, both cost/km ratios and category totals; add year aggregates and lifetime category totals. Attribute summaries are capped (120 months, 40 years, 20 category rows per group), with excess names combined under `Övriga kategorier`.
- The card shows per-category expenses, six period cost/km tiles, and a separate month/year/lifetime fill-up section; no false whole-vehicle cost/km claim. Four-column mode now requires >=850px.
- Preserve the existing 28 sensor IDs and unique IDs; eight new sensors bring the integration to **36 sensors**. Existing ZIP paths remain unchanged.

Upgrade the integration in HACS and restart. Re-copy `custom_components/fuelio/www/ha-fuelio-card.js` to `/config/www/ha-fuelio-card.js`, update the SINGLE Lovelace resource to `/local/ha-fuelio-card.js?v=0.1.0-beta.6`, then hard refresh. Keep existing card YAML. Compare categories and cost/km with your private Fuelio backup in real HA before stable promotion. `main` remains unchanged.
''', encoding='utf-8')
readme = Path('README.md')
r = readme.read_text(encoding='utf-8')
r = r.replace('**Beta.5 card hotfix:**', '**Beta.6 period analytics:** Six read-only kr/loggad km sensors (fuel + total, month/year/lifetime), two tanking counters, expense category join through CostCategories.CostTypeID, and per-month/year/lifetime category summaries. Current 28 sensor IDs preserved; 36 sensors total. Refresh dashboard JS and resource cache-buster to beta.6. Full vehicle odometer kr/km is not established by this export.\n\n**Beta.5 card hotfix:**', 1)
r = r.replace('v0.1.0-beta.5', 'v0.1.0-beta.6').replace('0.1.0-beta.5', '0.1.0-beta.6')
readme.write_text(r, encoding='utf-8')
print('Cost analytics beta.6 source patch completed; no private backup opened.')
