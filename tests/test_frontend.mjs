// Synthetic, DOM-free smoke tests for the self-contained read-only card.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import vm from "node:vm";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const source = readFileSync(path.join(root, "custom_components/fuelio/www/ha-fuelio-card.js"), "utf8");
const constructors = new Map();
class FakeHTMLElement {
  attachShadow() {
    const listeners = {};
    this.shadowRoot = { innerHTML: "", addEventListener: (name, fn) => { listeners[name] = fn; }, listeners };
    return this.shadowRoot;
  }
}
const context = vm.createContext({
  HTMLElement: FakeHTMLElement,
  customElements: {
    get: (key) => constructors.get(key),
    define: (key, ctor) => constructors.set(key, ctor),
  },
  window: { customCards: [] },
});
new vm.Script(source, { filename: "ha-fuelio-card.js" }).runInContext(context);
assert.ok(constructors.has("ha-fuelio-card"));
assert.equal(context.window.customCards.length, 1);
const Card = constructors.get("ha-fuelio-card");
const card = new Card();
assert.throws(() => card.setConfig({ entity: "sensor.invalid" }), /monthly_cost_breakdown/);
card.setConfig({ entity: "sensor.synthetic_car_monthly_cost_breakdown", title: "<script>invalid</script>" });
assert.match(card.shadowRoot.innerHTML, /Läser Fuelio/);
const state = (value, attributes = {}) => ({ state: String(value), attributes, last_updated: "2026-09-21T22:00:00+02:00" });
const prefix = "sensor.synthetic_car_";
const states = {
  [prefix + "monthly_cost_breakdown"]: state(1200, { months: [
    { month: "2026-09", fuel: 1000, other: 200, total: 1200 },
    { month: "2026-08", fuel: 800, other: 0, total: 800 },
  ], history_truncated: false }),
  [prefix + "latest_odometer_km"]: state(10001),
  [prefix + "trip_count"]: state(20),
  [prefix + "trip_distance_km"]: state(350),
  [prefix + "last_reported_consumption"]: state(5.8),
  [prefix + "last_fuel_price"]: state(22.64),
  [prefix + "fuel_count"]: state(4),
  [prefix + "fuel_litres"]: state(100),
  [prefix + "fuel_cost"]: state(1800),
  [prefix + "other_expenses"]: state(200),
  [prefix + "total_actual_cost"]: state(2000),
  [prefix + "estimated_trip_cost"]: state(49),
  [prefix + "last_fillup_date"]: state("2026-09-10"),
  [prefix + "fuel_price_min_year"]: state(13.5, { recorded_on: "2026-03-03" }),
  [prefix + "consumption_min_all"]: state("unknown"),
};
card.hass = { states, callService: () => { throw new Error("Card must be read-only"); } };
assert.match(card.shadowRoot.innerHTML, /&lt;script&gt;invalid&lt;\/script&gt;/);
assert.doesNotMatch(card.shadowRoot.innerHTML, /<script>invalid<\/script>/);
assert.match(card.shadowRoot.innerHTML, /1\s?200,00 kr/);
assert.match(card.shadowRoot.innerHTML, /13,5 kr\/L/);
assert.match(card.shadowRoot.innerHTML, /2026-03-03/);
assert.match(card.shadowRoot.innerHTML, /Pris- &amp; förbrukningsrekord/);
assert.equal(card._months().length, 2);
const before = card.shadowRoot.innerHTML;
card.hass = { states };
assert.equal(card.shadowRoot.innerHTML, before, "Unrelated HA setter calls must not redraw the card");
card.shadowRoot.listeners.change({ target: { id: "fuelio-month", value: "2026-08" } });
assert.equal(card._month, "2026-08");
assert.match(card.shadowRoot.innerHTML, /Bokförda utgifter/);
assert.match(card.shadowRoot.innerHTML, /800,00 kr/);
card.shadowRoot.listeners.click({ target: { closest: () => ({ dataset: { section: "records" } }) } });
assert.equal(card._open.records, false);
assert.match(card.shadowRoot.innerHTML, /data-section="records" aria-expanded="false"/);
assert.doesNotMatch(card.shadowRoot.innerHTML, /<script>invalid<\/script>/);
console.log("PASS: Fuelio frontend config, escaping, rendering, month selector, accordion and read-only behavior");
