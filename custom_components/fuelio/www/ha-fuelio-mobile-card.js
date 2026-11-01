/* HA-Fuelio Mobile Card 2026.11.1b1 — compact Fuelio overview for phones. */
(() => {
  "use strict";
  const UI_LANGUAGE = globalThis.document?.documentElement?.lang || globalThis.navigator?.language || "sv-SE";

  const CARD_VERSION = "2026.11.1b1";
  const RESERVE_RANGE_KM = 75;
  const fmt = new Intl.NumberFormat(UI_LANGUAGE, { maximumFractionDigits: 2 });
  const money = new Intl.NumberFormat(UI_LANGUAGE, { minimumFractionDigits: 0, maximumFractionDigits: 0 });

  const ENTITY_SLUGS = Object.freeze({
    monthly_cost_breakdown: "monthly_cost_breakdown",
    latest_odometer_km: "latest_odometer",
    last_reported_consumption: "last_reported_fuel_consumption",
    last_fillup_date: "last_fuel_up",
    last_fuel_price: "last_fuel_price",
    distance_since_last_fillup_km: "distance_since_last_fuel_up",
    estimated_fuel_remaining_l: "estimated_fuel_remaining",
    estimated_range_remaining_km: "estimated_range_remaining",
    estimated_days_to_next_fillup: "estimated_days_to_next_fuel_up",
    estimated_next_fillup_date: "estimated_next_fuel_up",
    fuel_cost_per_km_month: "fuel_cost_per_logged_km_this_month",
    total_cost_per_km_month: "total_cost_per_logged_km_this_month",
    last_app_sync: "last_fuelio_app_sync",
  });

  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[c]);
  const valid = (state) => state && !["unknown", "unavailable", "none", "null", ""].includes(String(state.state).toLowerCase());
  const num = (state) => valid(state) && Number.isFinite(Number(state.state)) ? Number(state.state) : null;
  const decimal = (value, unit = "") => Number.isFinite(value) ? `${fmt.format(value)}${unit ? ` ${unit}` : ""}` : "—";
  const kronor = (value) => Number.isFinite(value) ? `${money.format(value)} kr` : "—";
  const date = (value) => /^\d{4}-\d{2}-\d{2}$/.test(String(value || "")) ? value : "—";
  const dateTime = (value) => {
    const parsed = new Date(String(value || ""));
    return Number.isNaN(parsed.getTime()) ? "—" : new Intl.DateTimeFormat(UI_LANGUAGE, {
      month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"
    }).format(parsed);
  };

  const EN_REPLACEMENTS = [
    ["Läser Fuelio …", "Loading Fuelio …"], ["RESERV", "RESERVE"], ["Sedan tankning", "Since fuel-up"],
    ["Förbrukning", "Consumption"], ["Aktuell månad", "Current month"], ["Körsträcka", "Distance"],
    ["Bränsle", "Fuel"], ["Övrigt", "Other"], ["Totalt", "Total"], ["Kostnad/km", "Cost/km"],
    ["Bränsle/km", "Fuel/km"], ["Mer information", "More information"], ["Senaste tankning", "Latest fuel-up"],
    ["Senaste literpris", "Latest fuel price"], ["Fuelio-förbrukning", "Fuelio consumption"],
    ["Beräknad nästa tankning", "Estimated next fuel-up"], ["Dagar till teoretiskt tom", "Days to theoretical empty"],
    ["Kalibrera mot bilens visade återstående räckvidd. Detta påverkar bara HA och återställs automatiskt vid nästa registrerade primärtankning.", "Calibrate against the vehicle's displayed remaining range. This only affects Home Assistant and resets automatically at the next registered primary-tank fill-up."],
    ["Återstående räckvidd i kilometer", "Remaining range in kilometres"], ["Kalibrera", "Calibrate"],
    ["Återställ automatisk", "Restore automatic"], ["Underlag", "Basis"], ["uppmätt", "measured"],
    ["manuellt kalibrerad", "manually calibrated"], ["Estimerad tanknivå", "Estimated tank level"],
    ["stigande", "rising"], ["fallande", "falling"], ["stabil", "stable"]
  ];
  const localizeHtml = (html) => {
    const language = String(UI_LANGUAGE).toLowerCase();
    if (language.startsWith("sv")) return html;
    return EN_REPLACEMENTS.reduce((out, [from, to]) => out.replaceAll(from, to), html);
  };
  const style = `
    :host { display:block; color:var(--primary-text-color,#202124); font:inherit; }
    * { box-sizing:border-box; }
    ha-card { overflow:hidden; }
    .shell { padding:15px; }
    .header { display:flex; align-items:flex-start; justify-content:space-between; gap:10px; margin-bottom:14px; }
    .title { min-width:0; }
    .title h2 { margin:0; font-size:1.16rem; line-height:1.2; font-weight:800; }
    .title .odo { margin-top:4px; font-size:.78rem; color:var(--secondary-text-color,#68727d); }
    .sync { flex:0 0 auto; text-align:right; font-size:.67rem; color:var(--secondary-text-color,#68727d); line-height:1.35; }
    .tank { border:1px solid var(--divider-color,#e2e4e8); border-radius:18px; padding:13px; margin-bottom:11px; }
    .tank-head { display:flex; align-items:center; justify-content:space-between; gap:10px; margin-bottom:9px; }
    .tank-head strong { font-size:.88rem; }
    .reserve { padding:4px 8px; border-radius:999px; font-size:.68rem; font-weight:850; background:color-mix(in srgb,var(--error-color,#db4437) 14%,var(--card-background-color,#fff)); color:var(--error-color,#db4437); }
    .bar { position:relative; height:14px; overflow:hidden; border-radius:999px; background:var(--secondary-background-color,#eceff2); }
    .bar > span { display:block; height:100%; border-radius:999px; background:var(--primary-color,#03a9f4); }
    .tank.reserve-mode .bar > span { background:var(--error-color,#db4437); }
    .tank-line { display:flex; align-items:baseline; justify-content:space-between; gap:10px; margin-top:8px; }
    .tank-line strong { font-size:1.04rem; }
    .tank-line span { font-size:.77rem; color:var(--secondary-text-color,#68727d); text-align:right; }
    .quick { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; margin-bottom:11px; }
    .quick > div { min-width:0; padding:10px 11px; border-radius:14px; background:var(--secondary-background-color,#f4f5f7); }
    .quick span { display:block; color:var(--secondary-text-color,#68727d); font-size:.66rem; margin-bottom:4px; }
    .quick strong { display:block; font-size:.94rem; font-variant-numeric:tabular-nums; overflow-wrap:anywhere; }
    .section { border:1px solid var(--divider-color,#e2e4e8); border-radius:18px; overflow:hidden; margin-top:10px; }
    .section-title { padding:11px 13px 8px; font-size:.72rem; font-weight:850; text-transform:uppercase; letter-spacing:.04em; color:var(--secondary-text-color,#68727d); }
    .row { display:flex; justify-content:space-between; align-items:baseline; gap:12px; padding:9px 13px; border-top:1px solid var(--divider-color,#e2e4e8); }
    .row span { font-size:.75rem; color:var(--secondary-text-color,#68727d); }
    .row strong { font-size:.88rem; text-align:right; font-variant-numeric:tabular-nums; }
    .details > button { appearance:none; width:100%; display:flex; justify-content:space-between; align-items:center; border:0; background:none; color:inherit; padding:12px 13px; font:inherit; font-size:.78rem; font-weight:800; cursor:pointer; }
    .details-body { padding-bottom:3px; }
    .calibration { padding:11px 13px 13px; border-top:1px solid var(--divider-color,#e2e4e8); }
    .calibration p { margin:0 0 9px; font-size:.69rem; color:var(--secondary-text-color,#68727d); line-height:1.4; }
    .calibration form { display:flex; gap:7px; }
    .calibration input { min-width:0; flex:1; border:1px solid var(--divider-color,#d4d9df); border-radius:11px; padding:9px 10px; background:var(--card-background-color,#fff); color:inherit; font:inherit; }
    .calibration button { appearance:none; border:1px solid var(--primary-color,#03a9f4); border-radius:11px; padding:9px 11px; background:var(--primary-color,#03a9f4); color:var(--text-primary-color,#fff); font:inherit; font-weight:800; cursor:pointer; }
    .calibration .secondary { margin-top:7px; width:100%; background:transparent; color:var(--primary-text-color,#202124); border-color:var(--divider-color,#d4d9df); }
    .error { margin-top:8px; font-size:.69rem; color:var(--error-color,#db4437); }
    .basis { margin-top:9px; padding:9px 10px; border-radius:11px; background:var(--secondary-background-color,#f4f5f7); font-size:.68rem; color:var(--secondary-text-color,#68727d); line-height:1.45; }
    .foot { margin-top:10px; text-align:center; color:var(--secondary-text-color,#68727d); font-size:.62rem; }
  `;

  class HaFuelioMobileCard extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this._detailsOpen = false;
      this._error = "";
      this._signature = null;

      this.shadowRoot.addEventListener("click", async (event) => {
        const toggle = event.target.closest?.("[data-details-toggle]");
        if (toggle) {
          this._detailsOpen = !this._detailsOpen;
          this._render();
          return;
        }
        const clear = event.target.closest?.("[data-calibration-clear]");
        if (clear) {
          try {
            await this._callRangeService("clear_range_calibration");
            this._error = "";
          } catch (error) {
            this._error = error?.message || "Återställningen misslyckades.";
          }
          this._render();
        }
      });

      this.shadowRoot.addEventListener("submit", async (event) => {
        if (event.target?.id !== "fuelio-mobile-calibration") return;
        event.preventDefault();
        const input = event.target.querySelector?.("input[name=range_km]");
        const rangeKm = Number(input?.value);
        if (!Number.isFinite(rangeKm) || rangeKm < 1 || rangeKm > 5000) {
          this._error = "Ange 1–5 000 km.";
          this._render();
          return;
        }
        try {
          await this._callRangeService("calibrate_range", { range_km: rangeKm });
          this._error = "";
        } catch (error) {
          this._error = error?.message || "Kalibreringen misslyckades.";
        }
        this._render();
      });
    }

    setConfig(config) {
      if (!config || typeof config.entity !== "string" || !/^sensor\.[a-z0-9_]+_monthly_cost_breakdown$/.test(config.entity)) {
        throw new Error("Fuelio Mobile Card: ange entity: sensor.DIN_BIL_monthly_cost_breakdown");
      }
      this._config = { ...config };
      this._prefix = config.entity.slice(0, -"monthly_cost_breakdown".length);
      this._signature = null;
      this._render();
    }

    static getStubConfig() { return { entity: "sensor.din_bil_monthly_cost_breakdown" }; }
    getCardSize() { return 6; }

    set hass(hass) {
      this._hass = hass;
      if (!this._config) return;
      const keys = [
        "monthly_cost_breakdown", "latest_odometer_km", "last_reported_consumption",
        "last_fillup_date", "last_fuel_price", "distance_since_last_fillup_km",
        "estimated_fuel_remaining_l", "estimated_range_remaining_km",
        "estimated_days_to_next_fillup", "estimated_next_fillup_date",
        "fuel_cost_per_km_month", "total_cost_per_km_month", "last_app_sync",
      ];
      const signature = keys.map((key) => {
        const entry = this._state(key);
        const attrs = key === "monthly_cost_breakdown"
          ? JSON.stringify(entry?.attributes?.months || [])
          : JSON.stringify(entry?.attributes || {});
        return entry ? `${entry.state}|${entry.last_updated || ""}|${attrs}` : "missing";
      }).join(";");
      if (signature === this._signature) return;
      this._signature = signature;
      this._render();
    }

    _resolveId(key) {
      const states = this._hass?.states || {};
      const registry = this._hass?.entities || {};
      const suffix = ENTITY_SLUGS[key] || key;
      const reference = registry[this._config?.entity] || registry[this._prefix + "last_fuel_price"];
      const device = reference?.platform === "fuelio" ? reference.device_id : null;
      const allowed = (id) => !device || !registry[id] ||
        (registry[id].platform === "fuelio" && registry[id].device_id === device);
      const exactIds = [
        key === "monthly_cost_breakdown" ? this._config?.entity : null,
        this._prefix + suffix,
        this._prefix + key,
      ];
      for (const id of exactIds) {
        if (id && states[id] && allowed(id)) return id;
      }
      if (!device) return null;
      const matches = Object.values(registry).filter((entry) => entry &&
        entry.platform === "fuelio" && entry.device_id === device && states[entry.entity_id] &&
        ((typeof entry.unique_id === "string" && entry.unique_id.endsWith("_" + key)) ||
          entry.entity_id.endsWith("_" + suffix) || entry.entity_id.endsWith("_" + key)));
      return matches.length === 1 ? matches[0].entity_id : null;
    }

    _state(key) {
      const id = this._resolveId(key);
      return id ? this._hass?.states?.[id] : undefined;
    }

    _value(key) { return num(this._state(key)); }

    _currentMonth() {
      const rows = this._state("monthly_cost_breakdown")?.attributes?.months;
      if (!Array.isArray(rows)) return null;
      const now = new Date();
      const key = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
      return rows.find((row) => row?.month === key) || rows[0] || null;
    }

    _forecast() {
      return this._state("estimated_fuel_remaining_l")?.attributes ||
        this._state("estimated_range_remaining_km")?.attributes || {};
    }

    _rangeServiceEntity() {
      return this._resolveId("estimated_range_remaining_km") || this._config?.entity || null;
    }

    async _callRangeService(service, data = {}) {
      const entityId = this._rangeServiceEntity();
      if (!entityId || !this._hass?.callService) throw new Error("Fuelio-entiteten är inte tillgänglig.");
      await this._hass.callService("fuelio", service, { entity_id: entityId, ...data });
    }

    _render() {
      if (!this.shadowRoot || !this._config) return;
      if (!this._hass) {
        this.shadowRoot.innerHTML = localizeHtml(`<style>${style}</style><ha-card><div class="shell">Läser Fuelio …</div></ha-card>`);
        return;
      }

      const title = this._config.title || "Fuelio";
      const forecast = this._forecast();
      const month = this._currentMonth();
      const remaining = this._value("estimated_fuel_remaining_l");
      const range = this._value("estimated_range_remaining_km");
      const capacity = Number(forecast?.tank_capacity_l);
      const percent = Number.isFinite(remaining) && Number.isFinite(capacity) && capacity > 0
        ? Math.max(0, Math.min(100, remaining / capacity * 100))
        : null;
      const reserve = Number.isFinite(range) && range < RESERVE_RANGE_KM;
      const measured = forecast?.economy || {};
      const measuredConsumption = Number(measured?.recent_consumption_l_per_100km);
      const trend = measured?.trend === "increasing" ? "↑ ökar" :
        measured?.trend === "decreasing" ? "↓ minskar" :
        measured?.trend === "stable" ? "→ stabil" : null;
      const basis = Number(forecast?.consumption_basis_l_per_100km);
      const manual = forecast?.manual_calibration_active === true;
      const canCalibrate = Number.isFinite(Number(forecast?.fuel_available_since_calibration_l)) &&
        Number.isFinite(Number(forecast?.distance_since_calibration_km));
      const currentRangeInput = Number.isFinite(range) ? Math.max(1, Math.round(range)) : "";

      const km = Number(month?.km);
      const fuel = Number(month?.fuel);
      const other = Number(month?.other);
      const total = Number(month?.total);
      const monthFuelPerKm = this._value("fuel_cost_per_km_month");
      const monthTotalPerKm = this._value("total_cost_per_km_month");

      const details = this._detailsOpen ? `
        <div class="details-body">
          <div class="row"><span>Senaste tankning</span><strong>${esc(date(this._state("last_fillup_date")?.state))}</strong></div>
          <div class="row"><span>Senaste literpris</span><strong>${esc(decimal(this._value("last_fuel_price"), "kr/L"))}</strong></div>
          <div class="row"><span>Fuelio-förbrukning</span><strong>${esc(decimal(this._value("last_reported_consumption"), "L/100 km"))}</strong></div>
          <div class="row"><span>Beräknad nästa tankning</span><strong>${esc(date(this._state("estimated_next_fillup_date")?.state))}</strong></div>
          <div class="row"><span>Dagar till teoretiskt tom</span><strong>${esc(decimal(this._value("estimated_days_to_next_fillup"), "d"))}</strong></div>
          <div class="calibration">
            <p>Kalibrera mot bilens visade återstående räckvidd. Detta påverkar bara HA och återställs automatiskt vid nästa registrerade primärtankning.</p>
            <form id="fuelio-mobile-calibration">
              <input name="range_km" type="number" min="1" max="5000" step="1" value="${esc(currentRangeInput)}" ${canCalibrate ? "" : "disabled"} aria-label="Återstående räckvidd i kilometer">
              <button type="submit" ${canCalibrate ? "" : "disabled"}>Kalibrera</button>
            </form>
            ${manual ? `<button type="button" class="secondary" data-calibration-clear>Återställ automatisk</button>` : ""}
            ${this._error ? `<div class="error">${esc(this._error)}</div>` : ""}
            <div class="basis">
              Underlag: <strong>${esc(decimal(basis, "L/100 km"))}</strong>
              ${Number.isFinite(measuredConsumption) ? ` · uppmätt ${esc(decimal(measuredConsumption, "L/100 km"))}` : ""}
              ${trend ? ` · ${esc(trend)}` : ""}
              ${manual ? " · manuellt kalibrerad" : ""}
            </div>
          </div>
        </div>` : "";

      this.shadowRoot.innerHTML = localizeHtml(`<style>${style}</style><ha-card><div class="shell">
        <div class="header">
          <div class="title"><h2>🚙 ${esc(title)}</h2><div class="odo">${esc(decimal(this._value("latest_odometer_km"), "km"))}</div></div>
          <div class="sync">ZIP<br><strong>${esc(dateTime(this._state("last_app_sync")?.state))}</strong></div>
        </div>

        <section class="tank${reserve ? " reserve-mode" : ""}">
          <div class="tank-head"><strong>⛽ Tank</strong>${reserve ? '<span class="reserve">RESERV</span>' : ""}</div>
          <div class="bar" aria-label="Estimerad tanknivå"><span style="width:${Number.isFinite(percent) ? percent.toFixed(1) : 0}%"></span></div>
          <div class="tank-line">
            <strong>${reserve ? `RESERV · ${esc(decimal(range, "km"))}` : esc(decimal(remaining, "L"))}</strong>
            <span>${reserve ? esc(decimal(remaining, "L")) : esc(decimal(range, "km"))}</span>
          </div>
        </section>

        <div class="quick">
          <div><span>Sedan tankning</span><strong>${esc(decimal(this._value("distance_since_last_fillup_km"), "km"))}</strong></div>
          <div><span>Förbrukning</span><strong>${esc(decimal(Number.isFinite(measuredConsumption) ? measuredConsumption : basis, "L/100 km"))}</strong></div>
        </div>

        <section class="section">
          <div class="section-title">${esc(month?.month || "Aktuell månad")}</div>
          <div class="row"><span>Körsträcka</span><strong>${esc(decimal(km, "km"))}</strong></div>
          <div class="row"><span>Bränsle</span><strong>${esc(kronor(fuel))}</strong></div>
          <div class="row"><span>Övrigt</span><strong>${esc(kronor(other))}</strong></div>
          <div class="row"><span>Totalt</span><strong>${esc(kronor(total))}</strong></div>
          <div class="row"><span>Kostnad/km</span><strong>${esc(decimal(monthTotalPerKm, "kr/km"))}</strong></div>
          <div class="row"><span>Bränsle/km</span><strong>${esc(decimal(monthFuelPerKm, "kr/km"))}</strong></div>
        </section>

        <section class="section details">
          <button type="button" data-details-toggle aria-expanded="${this._detailsOpen}">
            <span>Mer information</span><span aria-hidden="true">${this._detailsOpen ? "⌃" : "⌄"}</span>
          </button>
          ${details}
        </section>

        <div class="foot">Fuelio Mobile · read-only · ${CARD_VERSION}</div>
      </div></ha-card>`);
    }
  }

  if (!customElements.get("ha-fuelio-mobile-card")) customElements.define("ha-fuelio-mobile-card", HaFuelioMobileCard);
  window.customCards = window.customCards || [];
  if (!window.customCards.some((card) => card.type === "ha-fuelio-mobile-card")) {
    window.customCards.push({
      type: "ha-fuelio-mobile-card",
      name: "HA-Fuelio Mobile Card",
      description: "Compact mobile view with tank status, range, reserve warning, monthly costs and calibration.",
    });
  }
})();
