// English-locale smoke tests for both bundled Fuelio dashboard cards.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

function loadCard(path, type) {
  const source = readFileSync(path, "utf8");
  const classes = new Map();
  class FakeElement {
    attachShadow() {
      this.shadowRoot = { innerHTML: "", addEventListener: () => {} };
      return this.shadowRoot;
    }
  }
  const sandbox = vm.createContext({
    HTMLElement: FakeElement,
    customElements: {
      get: (name) => classes.get(name),
      define: (name, klass) => classes.set(name, klass),
    },
    window: { customCards: [] },
    document: { documentElement: { lang: "en-US" } },
    navigator: { language: "en-US" },
  });
  new vm.Script(source, { filename: path }).runInContext(sandbox);
  assert.ok(classes.has(type), `Expected custom element ${type}`);
  return new (classes.get(type))();
}

const desktop = loadCard("custom_components/fuelio/www/ha-fuelio-card.js", "ha-fuelio-card");
desktop.setConfig({ entity: "sensor.test_monthly_cost_breakdown", title: "Fuelio" });
assert.match(desktop.shadowRoot.innerHTML, /Loading Fuelio/);
assert.doesNotMatch(desktop.shadowRoot.innerHTML, /Läser Fuelio/);

const mobile = loadCard("custom_components/fuelio/www/ha-fuelio-mobile-card.js", "ha-fuelio-mobile-card");
mobile.setConfig({ entity: "sensor.test_monthly_cost_breakdown", title: "Fuelio" });
assert.match(mobile.shadowRoot.innerHTML, /Loading Fuelio/);
assert.doesNotMatch(mobile.shadowRoot.innerHTML, /Läser Fuelio/);

console.log("PASS: English locale is applied to both Fuelio cards");
