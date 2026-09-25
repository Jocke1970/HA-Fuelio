import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
const source = readFileSync('custom_components/fuelio/www/ha-fuelio-card.js', 'utf8');
const types = new Map();
class FakeElement {
  attachShadow() {
    this.shadowRoot = { innerHTML: '', addEventListener: () => {} };
    return this.shadowRoot;
  }
}
const context = vm.createContext({ HTMLElement: FakeElement, customElements: {
  get: (type) => types.get(type), define: (type, klass) => types.set(type, klass),
}, window: { customCards: [] } });
new vm.Script(source).runInContext(context);
const Card = types.get('ha-fuelio-card');
const card = new Card();
// The beta.4 documentation supplied this plausible but absent monthly entity.
card.setConfig({ entity: 'sensor.mmk912_monthly_cost_breakdown' });
const states = {};
const entities = {};
const add = (id, key, value, attrs = {}, device = 'carA') => {
  states[id] = { state: String(value), attributes: attrs, last_updated: '2026-09-21T23:00:00+02:00' };
  entities[id] = { entity_id: id, device_id: device, platform: 'fuelio', unique_id: `entry-${device}_${key}` };
};
const legacy = 'sensor.mmk912_';
add(legacy + 'last_fuel_price', 'last_fuel_price', 22.64);
add(legacy + 'latest_odometer', 'latest_odometer_km', 178593);
add(legacy + 'last_reported_fuel_consumption', 'last_reported_consumption', 5.8);
add(legacy + 'fuel_ups', 'fuel_count', 3);
add(legacy + 'fuel_volume', 'fuel_litres', 162.47);
add(legacy + 'last_fuel_up', 'last_fillup_date', '2026-09-12');
add(legacy + 'trips', 'trip_count', 120);
add(legacy + 'trip_distance', 'trip_distance_km', 2195.507);
add(legacy + 'travel_time', 'trip_duration_hours', 39.61);
add(legacy + 'last_trip', 'last_trip_date', '2026-09-21');
add(legacy + 'fuel_expenditure', 'fuel_cost', 3352.82);
add(legacy + 'other_expenditure', 'other_expenses', 598);
add(legacy + 'total_actual_expenditure', 'total_actual_cost', 3950.82);
add(legacy + 'estimated_trip_costs_not_actual_spend', 'estimated_trip_cost', 1330.91);
const generic = 'sensor.fuelio_vehicle_';
add(generic + 'monthly_cost_breakdown', 'monthly_cost_breakdown', 1242.26, { months: [
  { month: '2026-09', fuel: 1242.26, other: 0, total: 1242.26 },
  { month: '2026-08', fuel: 500, other: 598, total: 1098 },
], history_truncated: false });
add(generic + 'lowest_fuel_price_this_year', 'fuel_price_min_year', 19.91, { recorded_on: '2026-04-01' });
add(generic + 'highest_fuel_price_since_import_start', 'fuel_price_max_all', 24.45, { recorded_on: '2025-01-02' });
add(generic + 'lowest_reported_consumption_this_year', 'consumption_min_year', 5.8, { recorded_on: '2026-09-12' });
// A different vehicle MUST NOT fill in our missing highest year reading.
add('sensor.other_car_highest_fuel_price_this_year', 'fuel_price_max_year', 99.99, { recorded_on: '2026-01-01' }, 'carB');
card.hass = { states, entities };
card._open.records = true;
card._render();
let html = card.shadowRoot.innerHTML;
assert.match(html, /Data tillgänglig/);
assert.match(html, /178\s?593 km/);
assert.match(html, /5,8 L\/100 km/);
assert.match(html, /3 st/);
assert.match(html, /1\s?242,26 kr/);
assert.match(html, /2026-04-01/);
assert.match(html, /19,91 kr\/L/);
assert.match(html, /24,45 kr\/L/);
assert.doesNotMatch(html, /99,99/);
assert.equal(card._months().length, 2);
assert.equal(card._state('fuel_price_max_year'), undefined);
assert.equal(card._state('monthly_cost_breakdown').state, '1242.26');
// User-renamed ID should still resolve by stable registry unique_id.
const before = generic + 'lowest_fuel_price_this_year';
const after = 'sensor.user_custom_price_record';
states[after] = states[before]; entities[after] = { ...entities[before], entity_id: after };
delete states[before]; delete entities[before];
card.hass = { states, entities };
assert.equal(card._state('fuel_price_min_year').entity_id, undefined);
assert.match(card.shadowRoot.innerHTML, /19,91 kr\/L/);
console.log('PASS: real name-derived and cross-prefix entity IDs; same-device registry resolution and vehicle isolation');
