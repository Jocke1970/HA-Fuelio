// Synthetic mobile-card regression tests.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const source = readFileSync("custom_components/fuelio/www/ha-fuelio-mobile-card.js", "utf8");
const classes = new Map();
class FakeElement {
  attachShadow() {
    const listeners = {};
    this.shadowRoot = { innerHTML: "", listeners, addEventListener: (name, fn) => { listeners[name] = fn; } };
    return this.shadowRoot;
  }
}
const sandbox = vm.createContext({
  HTMLElement: FakeElement,
  customElements: { get: (name) => classes.get(name), define: (name, klass) => classes.set(name, klass) },
  window: { customCards: [] },
});
new vm.Script(source, { filename: "ha-fuelio-mobile-card.js" }).runInContext(sandbox);
assert.ok(classes.has("ha-fuelio-mobile-card"));
assert.equal(sandbox.window.customCards.length, 1);

const card = new (classes.get("ha-fuelio-mobile-card"))();
card.setConfig({ entity: "sensor.car_monthly_cost_breakdown", title: "Caddy" });

const states = {};
const entities = {};
const add = (id, key, value, attrs = {}) => {
  states[id] = { state: String(value), attributes: attrs, last_updated: "2026-11-01T12:00:00+01:00" };
  entities[id] = { entity_id: id, platform: "fuelio", device_id: "carA", unique_id: "entry_" + key };
};
const p = "sensor.car_";
add(p + "monthly_cost_breakdown", "monthly_cost_breakdown", 1500, { months: [
  { month: "2026-11", fuel: 1100, other: 400, total: 1500, km: 420 }
]});
add(p + "latest_odometer", "latest_odometer_km", 180123);
add(p + "last_reported_fuel_consumption", "last_reported_consumption", 5.9);
add(p + "last_fuel_up", "last_fillup_date", "2026-10-31");
add(p + "last_fuel_price", "last_fuel_price", 21.5);
add(p + "distance_since_last_fuel_up", "distance_since_last_fillup_km", 512);
add(p + "estimated_fuel_remaining", "estimated_fuel_remaining_l", 4.1, {
  tank_capacity_l: 60,
  consumption_basis_l_per_100km: 5.8,
  manual_calibration_active: false,
  fuel_available_since_calibration_l: 60,
  distance_since_calibration_km: 512,
  economy: { recent_consumption_l_per_100km: 5.82, trend: "stable" },
});
add(p + "estimated_range_remaining", "estimated_range_remaining_km", 62, {
  tank_capacity_l: 60,
  consumption_basis_l_per_100km: 5.8,
  manual_calibration_active: false,
});
add(p + "estimated_days_to_next_fuel_up", "estimated_days_to_next_fillup", 2);
add(p + "estimated_next_fuel_up", "estimated_next_fillup_date", "2026-11-03");
add(p + "fuel_cost_per_logged_km_this_month", "fuel_cost_per_km_month", 2.62);
add(p + "total_cost_per_logged_km_this_month", "total_cost_per_km_month", 3.57);
add(p + "last_fuelio_app_sync", "last_app_sync", "2026-11-01T11:55:00+01:00");

const calls = [];
card.hass = { states, entities, callService: async (...args) => calls.push(args) };
let html = card.shadowRoot.innerHTML;
assert.match(html, /Caddy/);
assert.match(html, /180\s?123 km/);
assert.match(html, /RESERV/);
assert.match(html, /62 km/);
assert.match(html, /4,1 L/);
assert.match(html, /5,82 L\/100 km/);
assert.match(html, /1\s?500 kr/);
assert.match(html, /3,57 kr\/km/);
assert.doesNotMatch(html, /Årsöversikt/);
assert.doesNotMatch(html, /Pris- &amp; förbrukningsrekord/);

card.shadowRoot.listeners.click({ target: { closest: (selector) => selector === "[data-details-toggle]" ? {} : null } });
html = card.shadowRoot.innerHTML;
assert.match(html, /Senaste tankning/);
assert.match(html, /Kalibrera/);
assert.match(html, /→ stabil/);

const form = {
  id: "fuelio-mobile-calibration",
  querySelector: () => ({ value: "70" }),
};
await card.shadowRoot.listeners.submit({ target: form, preventDefault: () => {} });
assert.equal(calls[0][0], "fuelio");
assert.equal(calls[0][1], "calibrate_range");
assert.equal(calls[0][2].range_km, 70);

states[p + "estimated_range_remaining"].state = "80";
states[p + "estimated_range_remaining"].last_updated = "2026-11-01T12:01:00+01:00";
card.hass = { states, entities };
assert.doesNotMatch(card.shadowRoot.innerHTML, /RESERV/);

states[p + "estimated_range_remaining"].state = "unknown";
states[p + "estimated_range_remaining"].last_updated = "2026-11-01T12:02:00+01:00";
card.hass = { states, entities };
assert.doesNotMatch(card.shadowRoot.innerHTML, /RESERV/);

assert.match(card.shadowRoot.innerHTML, /2026\.11\.1b1/);
console.log("PASS: mobile card compact layout, reserve threshold, details and calibration");
