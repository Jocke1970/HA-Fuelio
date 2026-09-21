// Test the actual extension using synthetic mixed-prefix HA entities.
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
