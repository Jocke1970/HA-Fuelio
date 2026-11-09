// Synthetic-only regression: four current-period panels must ignore historic month selection.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
const source = readFileSync('custom_components/fuelio/www/ha-fuelio-card.js', 'utf8');
const classes = new Map();
class FakeElement {
  attachShadow() {
    const listeners = {};
    this.shadowRoot = { innerHTML: '', listeners, addEventListener: (name, callback) => { listeners[name] = callback; } };
    return this.shadowRoot;
  }
}
const sandbox = vm.createContext({ HTMLElement: FakeElement, customElements: {
  get: (name) => classes.get(name), define: (name, klass) => classes.set(name, klass),
}, window: { customCards: [] } });
new vm.Script(source).runInContext(sandbox);
const card = new (classes.get('ha-fuelio-card'))();
card.setConfig({ entity: 'sensor.mmk912_monthly_cost_breakdown' });
const states = {}, entities = {};
function add(id, key, value, attributes = {}) {
  states[id] = { state: String(value), attributes, last_updated: '2026-09-21T23:00:00Z' };
  entities[id] = { entity_id: id, platform: 'fuelio', device_id: 'synthetic-car', unique_id: `synthetic-entry_${key}` };
}
add('sensor.mmk912_last_fuel_price', 'last_fuel_price', 22);
add('sensor.mmk912_latest_odometer', 'latest_odometer_km', 178593);
add('sensor.mmk912_last_reported_fuel_consumption', 'last_reported_consumption', 5.8);
add('sensor.externa_sensorer_fuelio_vehicle_monthly_cost_breakdown', 'monthly_cost_breakdown', 1532.21, {
  months: [
    { month: '2026-09', fuel: 1242.26, other: 289.95, total: 1532.21, km: 435, litres: 54.87,
      trip_count: 24, average_trip_km: 17.7, estimated_fuel: 480.23, estimated_total: 770.18,
      estimated_fuel_per_km: 1.104, estimated_total_per_km: 1.77, odo_coverage: 'prior_checkpoint',
      odo_start_on: '2026-08-31', odo_end_on: '2026-09-21', fuel_ups: 1, categories: [] },
    { month: '2026-08', fuel: 1057.94, other: 299, total: 1356.94, km: 1023, litres: 54,
      trip_count: 35, average_trip_km: 25, estimated_fuel: 1100, estimated_total: 1399,
      estimated_total_per_km: 1.368, odo_coverage: 'partial_start',
      odo_start_on: '2026-08-01', odo_end_on: '2026-08-31', fuel_ups: 1, categories: [] },
  ],
  years: [{ year: '2026', fuel: 3352.82, other: 887.95, total: 4240.77,
    km: 2280, litres: 162.47, estimated_total_per_km: 1.55, estimated_fuel: 2700, estimated_total: 3587.95,
    fuel_ups: 3, trip_count: 120, categories: [] }],
  estimated_lifetime: { estimated_fuel: 2700, estimated_total: 3587.95 },
  latest_two_consumption: 5.56, latest_two_consumption_count: 2, lifetime_odometer_km: 2280,
  categories_all: [], history_truncated: false,
});
card.hass = { states, entities };
card._open.costs = true;
card._render();
const before = card.shadowRoot.innerHTML;
const overview = (html) => html.split('<div class="overview">')[1]?.split('<div class="dashboard-grid">')[0];
assert.ok(overview(before), 'four-panel overview must render');
assert.match(overview(before), /Mätarställning/);
assert.match(overview(before), /data-overview-section="odometer"/);
assert.match(overview(before), /Drivmedel/);
assert.match(overview(before), /Bokförda utgifter/);
assert.match(overview(before), /Körkostnad/);
assert.match(overview(before), /Tank & räckvidd/);
assert.ok(overview(before).indexOf("Tank & räckvidd") < overview(before).indexOf("Mätarställning"), "Tank & räckvidd must render before Mätarställning");
assert.match(overview(before), /data-overview-section="fuel"/);
assert.match(overview(before), /data-overview-section="booked"/);
assert.match(overview(before), /data-overview-section="drivecost"/);
assert.match(overview(before), /overview-summary-grid/);
assert.match(overview(before), /overview-summary-label/);
assert.match(overview(before), /overview-summary-unit/);
assert.match(source, /wholeKroner\(nowMonth\?\.total\)/);
assert.match(source, /wholeKroner\(currentYearData\?\.total\)/);




assert.match(before, /@container \(min-width:340px\) \{\s*\.overview-summary-grid \{ grid-template-columns:repeat\(2,minmax\(0,1fr\)\)/);
assert.match(before, /\.overview-expander>button \{[^}]*text-align:center/);
assert.match(before, /\.kpi \{[^}]*text-align:center[^}]*align-items:center/);
assert.match(overview(before), /aria-expanded="false"/);
assert.match(overview(before), /Senaste/);
assert.match(overview(before), /Snitt/);
assert.match(overview(before), /Månad/);
assert.match(overview(before), /År/);
assert.doesNotMatch(overview(before), /Tankat denna månad/);
assert.doesNotMatch(overview(before), /Sedan importstart/);
card.shadowRoot.listeners.click({ target: { closest: (selector) => selector === "[data-overview-section]" ? { dataset: { overviewSection: "odometer" } } : null } });
assert.equal(card._overviewOpen.odometer, true);
assert.match(card.shadowRoot.innerHTML, /overview-expander is-open/);
assert.match(card.shadowRoot.innerHTML, /\.overview-expander\.is-open \{ grid-column:1 \/ -1; \}/);
assert.match(card.shadowRoot.innerHTML, /Sedan importstart/);
card.shadowRoot.listeners.click({ target: { closest: (selector) => selector === "[data-overview-section]" ? { dataset: { overviewSection: "fuel" } } : null } });
assert.equal(card._overviewOpen.fuel, true);
assert.match(card.shadowRoot.innerHTML, /Tankat denna månad/);
assert.match(card.shadowRoot.innerHTML, /54,87 L/);
assert.match(card.shadowRoot.innerHTML, /162,47 L/);
assert.match(overview(before), /1,77 kr\/km/);
assert.match(before, /Genomsnitt\/resa/);
assert.match(before, /17,7 km/);
assert.match(before, /480,23 kr/);
const overviewExpanded = overview(card.shadowRoot.innerHTML);
card.shadowRoot.listeners.change({ target: { id: 'fuelio-month', value: '2026-08' } });
const after = card.shadowRoot.innerHTML;
assert.equal(card._month, '2026-08');
assert.equal(overview(after), overviewExpanded, 'historic month selection must never alter current overview');
assert.match(after, /augusti 2026/);
assert.match(after, /25 km/);
assert.match(after, /1\s?100,00 kr/);
assert.match(after, /1\s?356,94 kr/);
console.log('PASS: current overview, categorized historic-month trip analytics and time-aware estimates');
