/* HA-Fuelio Card 0.1.0-beta.13 — interactive SVG charts, desktop-first, read-only Lovelace card. */
(() => {
  "use strict";
  const CARD_VERSION = "0.1.0-beta.13";
  const fmt = new Intl.NumberFormat("sv-SE", { maximumFractionDigits: 2 });
  const money = new Intl.NumberFormat("sv-SE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  // Home Assistant derives entity IDs from display names, NOT description.key.
// Old IDs may retain a pre-privacy vehicle prefix while new IDs use a generic one.
const ENTITY_SLUGS = Object.freeze({
  trip_count: "trips", trip_distance_km: "trip_distance", monthly_trip_distance_km: "trip_distance_this_month",
  trip_duration_hours: "travel_time", estimated_trip_cost: "estimated_trip_costs_not_actual_spend",
  fuel_count: "fuel_ups", fuel_litres: "fuel_volume", fuel_cost: "fuel_expenditure",
  monthly_fuel_cost: "fuel_expenditure_this_month", last_fuel_price: "last_fuel_price",
  last_reported_consumption: "last_reported_fuel_consumption", last_fillup_date: "last_fuel_up",
  expense_count: "expense_entries", other_expenses: "other_expenditure",
  monthly_other_expenses: "other_expenditure_this_month", upcoming_expense_count: "future_expense_entries",
  total_actual_cost: "total_actual_expenditure", last_trip_date: "last_trip",
  latest_odometer_km: "latest_odometer",
  distance_since_last_fillup_km: "distance_since_last_fuel_up",
  estimated_fuel_remaining_l: "estimated_fuel_remaining",
  estimated_range_remaining_km: "estimated_range_remaining",
  estimated_days_to_next_fillup: "estimated_days_to_next_fuel_up",
  estimated_next_fillup_date: "estimated_next_fuel_up",
  last_app_sync: "last_fuelio_app_sync",
  fuel_price_min_year: "lowest_fuel_price_this_year",
  fuel_price_max_year: "highest_fuel_price_this_year", fuel_price_min_all: "lowest_fuel_price_since_import_start",
  fuel_price_max_all: "highest_fuel_price_since_import_start",
  consumption_min_year: "lowest_reported_consumption_this_year",
  consumption_max_year: "highest_reported_consumption_this_year",
  consumption_min_all: "lowest_reported_consumption_since_import_start",
  consumption_max_all: "highest_reported_consumption_since_import_start",
  fuel_count_month: "fuel_ups_this_month", fuel_count_year: "fuel_ups_this_year",
  fuel_cost_per_km_month: "fuel_cost_per_logged_km_this_month",
  total_cost_per_km_month: "total_cost_per_logged_km_this_month",
  fuel_cost_per_km_year: "fuel_cost_per_logged_km_this_year",
  total_cost_per_km_year: "total_cost_per_logged_km_this_year",
  fuel_cost_per_km_all: "fuel_cost_per_logged_km_since_import_start",
  total_cost_per_km_all: "total_cost_per_logged_km_since_import_start",
  monthly_cost_breakdown: "monthly_cost_breakdown",
});
  const valid = (state) => state && !["unknown", "unavailable", "none", "null", ""].includes(String(state.state).toLowerCase());
  const num = (state) => valid(state) && Number.isFinite(Number(state.state)) ? Number(state.state) : null;
  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const kroner = (value) => Number.isFinite(value) ? `${money.format(value)} kr` : "—";
  const decimal = (value, unit = "") => Number.isFinite(value) ? `${fmt.format(value)}${unit ? ` ${unit}` : ""}` : "—";
  const date = (value) => /^\d{4}-\d{2}-\d{2}$/.test(String(value || "")) ? value : "—";
  const dateTime = (value) => {
    const parsed = new Date(String(value || ""));
    return Number.isNaN(parsed.getTime()) ? "—" : new Intl.DateTimeFormat("sv-SE", {
      dateStyle: "short", timeStyle: "short"
    }).format(parsed);
  };
  const monthName = (key) => /^\d{4}-(0[1-9]|1[0-2])$/.test(key)
    ? new Intl.DateTimeFormat("sv-SE", { month: "long", year: "numeric", timeZone: "UTC" }).format(new Date(`${key}-01T12:00:00Z`))
    : "Okänd månad";
  const style = `
    :host { display:block; container-type:inline-size; color:var(--primary-text-color,#202124); font:inherit; }
    * { box-sizing:border-box; }
    .shell { overflow:hidden; border-radius:26px; padding:18px; background:var(--ha-card-background,var(--card-background-color,#fff)); box-shadow:var(--ha-card-box-shadow,0 8px 28px #00000012); }
    .header { display:flex; align-items:flex-start; justify-content:space-between; flex-wrap:wrap; gap:12px; margin-bottom:16px; }
    .title-wrap { display:flex; flex-direction:column; gap:5px; }
    h2 { font-size:1.3rem; margin:0; font-weight:800; letter-spacing:-.02em; }
    h3 { font-size:1rem; margin:0; }
    .header-meta { display:flex; flex-wrap:wrap; justify-content:flex-end; gap:7px; }
    .muted { color:var(--secondary-text-color,#68727d); font-size:.78rem; }
    .pill { padding:6px 10px; border-radius:999px; background:var(--secondary-background-color,#eef1f4); font-size:.72rem; white-space:nowrap; }
    .pill strong { font-weight:800; }
    .kpi-strip { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; margin-bottom:12px; }
    .kpi { min-width:0; border:1px solid var(--divider-color,#e2e4e8); border-radius:18px; padding:13px 14px; background:linear-gradient(180deg,color-mix(in srgb,var(--card-background-color,#fff) 96%,var(--primary-color,#03a9f4) 4%),var(--card-background-color,#fff)); }
    .kpi .label { color:var(--secondary-text-color,#68727d); font-size:.7rem; font-weight:700; margin-bottom:5px; }
    .kpi .value { font-size:1.18rem; font-weight:850; line-height:1.15; letter-spacing:-.02em; overflow-wrap:anywhere; font-variant-numeric:tabular-nums; }
    .kpi .detail { color:var(--secondary-text-color,#68727d); font-size:.68rem; margin-top:5px; }
    button.kpi,button.tile { color:inherit; font:inherit; width:100%; }
    .chart-action { cursor:pointer; position:relative; transition:transform .12s ease,border-color .12s ease,box-shadow .12s ease; }
    .chart-action:hover { transform:translateY(-1px); border-color:color-mix(in srgb,var(--primary-color,#03a9f4) 45%,var(--divider-color,#e2e4e8)); box-shadow:0 6px 16px #00000010; }
    .chart-action:focus-visible,.category-chart:focus-visible { outline:2px solid var(--primary-color,#03a9f4); outline-offset:2px; }
    .chart-hint { display:block; margin-top:5px; font-size:.62rem; color:var(--primary-color,#03a9f4); font-weight:750; }
    .overview { display:grid; grid-template-columns:1fr; gap:12px; }
    .overview-panel,.range-panel { border:1px solid var(--divider-color,#e2e4e8); border-radius:20px; padding:15px; min-width:0; background:var(--card-background-color,#fff); }
    .overview-panel h3,.range-panel h3 { font-size:.98rem; margin:0 0 9px; }
    .overview-row { display:flex; justify-content:space-between; align-items:baseline; flex-wrap:wrap; gap:5px 10px; padding:8px 0; border-top:1px solid var(--divider-color,#e2e4e8); }
    .overview-row:first-of-type { border-top:0; }
    .overview-row .name { color:var(--secondary-text-color,#68727d); font-size:.75rem; }
    .overview-row strong { text-align:right; font-size:.95rem; font-variant-numeric:tabular-nums; overflow-wrap:anywhere; }
    .overview-row .note { width:100%; text-align:right; font-size:.68rem; color:var(--secondary-text-color,#68727d); }
    .range-panel { display:grid; gap:12px; }
    .range-head { display:flex; align-items:center; justify-content:space-between; gap:12px; }
    .range-main { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }
    .range-stat { min-width:0; padding:11px 12px; border-radius:15px; background:var(--secondary-background-color,#f4f5f7); }
    .range-stat span { display:block; color:var(--secondary-text-color,#68727d); font-size:.69rem; margin-bottom:4px; }
    .range-stat strong { display:block; font-size:1.08rem; font-variant-numeric:tabular-nums; overflow-wrap:anywhere; }
    .fuel-meter { height:10px; border-radius:999px; background:var(--secondary-background-color,#e8ebef); overflow:hidden; }
    .fuel-meter>span { display:block; height:100%; border-radius:999px; background:var(--primary-color,#03a9f4); }
    .fuel-meter-note { display:flex; justify-content:space-between; gap:10px; margin-top:6px; color:var(--secondary-text-color,#68727d); font-size:.68rem; }
    .tripbar { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px 14px; margin-top:12px; padding:10px 12px; border:1px solid var(--divider-color,#e2e4e8); border-radius:16px; font-size:.78rem; }
    .dashboard-grid { display:grid; grid-template-columns:1fr; gap:12px; margin-top:12px; }
    .section { border:1px solid var(--divider-color,#e2e4e8); border-radius:20px; overflow:hidden; min-width:0; background:var(--card-background-color,#fff); }
    .section>button { cursor:pointer; display:flex; align-items:center; justify-content:space-between; width:100%; background:none; border:none; color:inherit; padding:14px 16px; text-align:left; font:inherit; font-weight:800; }
    .section>button:focus-visible,select:focus-visible { outline:2px solid var(--primary-color,#03a9f4); outline-offset:-2px; }
    .body { padding:0 14px 14px; }
    .section-title { font-weight:800; margin:14px 2px 9px; font-size:.86rem; }
    .grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:9px; }
    .tile { min-width:0; border:1px solid var(--divider-color,#e2e4e8); border-radius:16px; padding:12px 8px; text-align:center; }
    .tile .ico { font-size:1.05rem; display:block; margin-bottom:5px; }
    .tile .label { font-size:.71rem; font-weight:750; margin-bottom:5px; }
    .tile .value { font-weight:850; font-size:1rem; overflow-wrap:anywhere; font-variant-numeric:tabular-nums; }
    .tile .detail { font-size:.66rem; color:var(--secondary-text-color,#68727d); margin-top:4px; }
    .select-label { display:block; margin:12px 2px 6px; font-size:.75rem; color:var(--secondary-text-color,#68727d); }
    select { width:100%; color:inherit; background:var(--ha-card-background,var(--card-background-color,#fff)); border:1px solid var(--divider-color,#d4d9df); border-radius:12px; padding:10px; font:inherit; }
    .summary { border:1px solid var(--divider-color,#e2e4e8); border-radius:14px; padding:10px 11px; display:flex; align-items:center; justify-content:space-between; gap:8px; margin-top:9px; font-size:.77rem; }
    .summary strong { font-variant-numeric:tabular-nums; text-align:right; }
    .notice { padding:10px 11px; margin-top:9px; background:var(--secondary-background-color,#f4f5f7); color:var(--secondary-text-color,#68727d); border-radius:12px; font-size:.74rem; line-height:1.4; }
    .small { font-size:.72rem; }
    .foot { text-align:right; margin-top:12px; }
    .category-list { border:1px solid var(--divider-color,#e2e4e8); border-radius:14px; padding:3px 11px; }
    .category-chart { cursor:pointer; transition:border-color .12s ease,box-shadow .12s ease; }
    .category-chart:hover { border-color:color-mix(in srgb,var(--primary-color,#03a9f4) 45%,var(--divider-color,#e2e4e8)); box-shadow:0 6px 16px #00000010; }
    .category-row { display:flex; justify-content:space-between; gap:12px; padding:8px 0; border-bottom:1px solid var(--divider-color,#e2e4e8); font-size:.79rem; }
    .category-row:last-child { border:0; }
    .category-row strong { white-space:nowrap; font-variant-numeric:tabular-nums; }
    .annual-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:9px; }
    .annual-columns { display:grid; grid-template-columns:1fr; gap:14px; }
    .annual-block { min-width:0; }
    .annual-hero { margin-bottom:2px; }
    .records-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:9px; }
    .chart-backdrop { position:fixed; inset:0; z-index:9999; display:flex; align-items:center; justify-content:center; padding:18px; background:#0008; backdrop-filter:blur(4px); }
    .chart-modal { width:min(1100px,96vw); max-height:92vh; overflow:auto; border:1px solid var(--divider-color,#e2e4e8); border-radius:24px; background:var(--ha-card-background,var(--card-background-color,#fff)); color:var(--primary-text-color,#202124); box-shadow:0 24px 80px #0008; }
    .chart-head { position:sticky; top:0; z-index:2; display:flex; align-items:flex-start; justify-content:space-between; gap:16px; padding:18px 20px 14px; border-bottom:1px solid var(--divider-color,#e2e4e8); background:var(--ha-card-background,var(--card-background-color,#fff)); }
    .chart-head h3 { font-size:1.15rem; margin:0 0 4px; }
    .chart-close { flex:none; width:38px; height:38px; border:1px solid var(--divider-color,#e2e4e8); border-radius:999px; background:var(--secondary-background-color,#f4f5f7); color:inherit; cursor:pointer; font-size:1.05rem; }
    .chart-body { padding:16px 18px 8px; }
    .chart-wrap { width:100%; overflow-x:auto; }
    .chart-svg { display:block; width:100%; min-width:640px; height:auto; overflow:visible; }
    .chart-svg text { fill:var(--secondary-text-color,#68727d); font-size:13px; font-family:inherit; }
    .chart-svg .axis-strong { fill:var(--primary-text-color,#202124); font-weight:750; }
    .chart-svg .gridline { stroke:var(--divider-color,#dfe3e8); stroke-width:1; }
    .chart-svg .series-a-fill { fill:var(--primary-color,#03a9f4); }
    .chart-svg .series-b-fill { fill:var(--accent-color,#ff9800); }
    .chart-svg .series-a-line { fill:none; stroke:var(--primary-color,#03a9f4); stroke-width:4; stroke-linecap:round; stroke-linejoin:round; }
    .chart-svg .series-b-line { fill:none; stroke:var(--accent-color,#ff9800); stroke-width:4; stroke-linecap:round; stroke-linejoin:round; }
    .chart-svg .series-a-dot { fill:var(--primary-color,#03a9f4); stroke:var(--card-background-color,#fff); stroke-width:2; }
    .chart-svg .series-b-dot { fill:var(--accent-color,#ff9800); stroke:var(--card-background-color,#fff); stroke-width:2; }
    .chart-legend { display:flex; flex-wrap:wrap; gap:12px 20px; padding:2px 4px 12px; color:var(--secondary-text-color,#68727d); font-size:.76rem; }
    .chart-legend span::before { content:""; display:inline-block; width:10px; height:10px; border-radius:3px; margin-right:6px; vertical-align:-1px; background:var(--primary-color,#03a9f4); }
    .chart-legend span:nth-child(2)::before { background:var(--accent-color,#ff9800); }
    .chart-note { margin:0 18px 18px; padding:10px 12px; border-radius:12px; background:var(--secondary-background-color,#f4f5f7); color:var(--secondary-text-color,#68727d); font-size:.74rem; line-height:1.4; }
    .chart-empty { padding:44px 20px; text-align:center; color:var(--secondary-text-color,#68727d); }
    @container (min-width:720px) {
      .shell { padding:22px; }
      .kpi-strip { grid-template-columns:repeat(3,minmax(0,1fr)); }
      .overview { grid-template-columns:repeat(2,minmax(0,1fr)); }
      .range-panel { grid-column:1 / -1; }
      .grid { grid-template-columns:repeat(3,minmax(0,1fr)); }
      .annual-grid { grid-template-columns:repeat(3,minmax(0,1fr)); }
      .records-grid { grid-template-columns:repeat(4,minmax(0,1fr)); }
    }
    @container (min-width:1050px) {
      .shell { padding:24px; }
      .kpi-strip { grid-template-columns:repeat(6,minmax(0,1fr)); }
      .overview { grid-template-columns:repeat(4,minmax(0,1fr)); }
      .range-panel { grid-column:span 2; }
      .dashboard-grid { grid-template-columns:minmax(0,1.6fr) minmax(340px,.9fr); align-items:start; }
      .section-costs { grid-row:span 2; }
      .section-annual,.section-records,.section-service,.section-version { grid-column:1 / -1; }
      .grid { grid-template-columns:repeat(3,minmax(0,1fr)); }
      .section-costs .grid { grid-template-columns:repeat(3,minmax(0,1fr)); }
    }
    @container (min-width:1380px) {
      .overview { grid-template-columns:repeat(6,minmax(0,1fr)); }
      .overview-panel { grid-column:span 1; }
      .range-panel { grid-column:span 2; }
      .dashboard-grid { grid-template-columns:minmax(0,1.75fr) minmax(400px,.85fr); }
      .annual-grid { grid-template-columns:repeat(6,minmax(0,1fr)); }
      .annual-columns { grid-template-columns:1.15fr .85fr; gap:18px; }
      .section-records .body { display:grid; grid-template-columns:1fr 1fr; gap:0 18px; }
      .section-records .notice { grid-column:1 / -1; }
    }
    @media (max-width:340px) { .tile { padding:10px 5px; } .tile .value { font-size:.9rem; } }
  `;
  class HaFuelioCard extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this._open = { annual: true, costs: true, fuel: true, records: false, service: false, version: false };
      this._month = null;
      this._year = null;
      this._chart = null;
      this._signature = null;
      this.shadowRoot.addEventListener("click", (event) => {
        const close = event.target.closest?.("[data-chart-close]");
        if (close || event.target?.classList?.contains?.("chart-backdrop")) {
          this._chart = null;
          this._render();
          return;
        }
        const chartTarget = event.target.closest?.("[data-chart]");
        if (chartTarget) {
          this._chart = {
            id: chartTarget.dataset.chart,
            year: chartTarget.dataset.chartYear || this._year || String(new Date().getFullYear()),
          };
          this._render();
          return;
        }
        const button = event.target.closest?.("button[data-section]");
        if (!button) return;
        const section = button.dataset.section;
        if (!Object.prototype.hasOwnProperty.call(this._open, section)) return;
        this._open[section] = !this._open[section];
        this._render();
      });
      this.shadowRoot.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && this._chart) {
          this._chart = null;
          this._render();
          return;
        }
        if ((event.key === "Enter" || event.key === " ") && event.target?.matches?.(".category-chart[data-chart]")) {
          event.preventDefault();
          this._chart = {
            id: event.target.dataset.chart,
            year: event.target.dataset.chartYear || this._year || String(new Date().getFullYear()),
          };
          this._render();
        }
      });
      this.shadowRoot.addEventListener("change", (event) => {
        const candidate = event.target?.value;
        if (event.target?.id === "fuelio-month") {
          const available = this._months();
          if (available.some((item) => item.month === candidate)) {
            this._month = candidate;
            this._render();
          }
          return;
        }
        if (event.target?.id === "fuelio-year") {
          const available = this._years();
          if (available.some((item) => String(item.year) === candidate)) {
            this._year = candidate;
            this._render();
          }
        }
      });
    }

    setConfig(config) {
      if (!config || typeof config.entity !== "string" || !/^sensor\.[a-z0-9_]+_monthly_cost_breakdown$/.test(config.entity)) {
        throw new Error("Fuelio Card: ange entity: sensor.DIN_BIL_monthly_cost_breakdown");
      }
      this._config = { ...config };
      this._prefix = config.entity.slice(0, -"monthly_cost_breakdown".length);
      this._signature = null;
      this._render();
    }

    static getStubConfig() { return { entity: "sensor.din_bil_monthly_cost_breakdown" }; }
    getCardSize() { return 10; }

    set hass(hass) {
      this._hass = hass;
      if (!this._config) return;
      const sensorKeys = [
        "monthly_cost_breakdown", "latest_odometer_km", "trip_count", "trip_distance_km", "trip_duration_hours",
        "last_fuel_up_date", "last_fillup_date", "last_fuel_price", "last_reported_consumption", "fuel_count",
        "fuel_litres", "fuel_cost", "other_expenses", "total_actual_cost", "estimated_trip_cost", "last_trip_date",
        "fuel_count_month", "fuel_count_year", "fuel_cost_per_km_month", "total_cost_per_km_month",
        "fuel_cost_per_km_year", "total_cost_per_km_year", "fuel_cost_per_km_all", "total_cost_per_km_all",
        "fuel_price_min_year", "fuel_price_max_year", "fuel_price_min_all", "fuel_price_max_all",
        "consumption_min_year", "consumption_max_year", "consumption_min_all", "consumption_max_all",
        "distance_since_last_fillup_km", "estimated_fuel_remaining_l", "estimated_range_remaining_km",
        "estimated_days_to_next_fillup", "estimated_next_fillup_date", "last_app_sync",
      ];
      // React only when Fuelio values change, not on every unrelated HA state update.
      const signature = sensorKeys.map((key) => {
        const entry = this._state(key);
        return entry ? `${entry.state}|${entry.last_updated || ""}|${key === "monthly_cost_breakdown" ? JSON.stringify([entry.attributes?.months || [], entry.attributes?.years || [], entry.attributes?.categories_all || []]) : (entry.attributes?.recorded_on || "")}` : "missing";
      }).join(";");
      if (signature === this._signature) return;
      this._signature = signature;
      this._render();
    }

    _resolveId(key) {
    const states = this._hass?.states || {};
    const registry = this._hass?.entities || {};
    const suffix = ENTITY_SLUGS[key] || key;
    // The configured monthly ID may not actually exist when an upgrade gives
    // the nine new sensors a different device-name prefix.
    const reference = registry[this._config?.entity] || registry[this._prefix + "last_fuel_price"];
    const device = reference?.platform === "fuelio" ? reference.device_id : null;
    const allowed = (id) => !device || !registry[id] ||
      (registry[id].platform === "fuelio" && registry[id].device_id === device);
    const exactIds = [key === "monthly_cost_breakdown" ? this._config?.entity : null,
      this._prefix + suffix, this._prefix + key];
    for (const id of exactIds) {
      if (id && states[id] && allowed(id)) return id;
    }
    // Match the *same device*, never another configured vehicle. Unique IDs
    // survive user entity renames; generated name slugs are the fallback.
    if (!device) return null;
    const matches = Object.values(registry).filter((entry) => entry &&
      entry.platform === "fuelio" && entry.device_id === device && states[entry.entity_id] &&
      ((typeof entry.unique_id === "string" && entry.unique_id.endsWith("_" + key)) ||
        entry.entity_id.endsWith("_" + suffix) || entry.entity_id.endsWith("_" + key)));
    return matches.length === 1 ? matches[0].entity_id : null;
  }
  _state(key) { const id = this._resolveId(key); return id ? this._hass?.states?.[id] : undefined; }
    _value(key) { return num(this._state(key)); }
    _months() {
      const rows = this._state("monthly_cost_breakdown")?.attributes?.months;
      if (!Array.isArray(rows)) return [];
      return rows.filter((row) => row && /^\d{4}-(0[1-9]|1[0-2])$/.test(row.month) &&
        ["fuel", "other", "total"].every((key) => Number.isFinite(row[key]))).slice(0, 120);
    }
    _years() {
      const rows = this._state("monthly_cost_breakdown")?.attributes?.years;
      if (!Array.isArray(rows)) return [];
      return rows.filter((row) => row && /^\d{4}$/.test(String(row.year)) &&
        ["fuel", "other", "total"].every((key) => Number.isFinite(row[key]))).slice(0, 40);
    }
    _chartAttrs(chart, year) {
      if (!chart) return "";
      const safeYear = /^\d{4}$/.test(String(year || "")) ? String(year) : "";
      return ` data-chart="${esc(chart)}"${safeYear ? ` data-chart-year="${safeYear}"` : ""}`;
    }
    _tile(icon, label, value, detail = "", chart = null, year = null) {
      const inner = `<span class="ico" aria-hidden="true">${icon}</span><div class="label">${esc(label)}</div><div class="value">${esc(value)}</div>${detail ? `<div class="detail">${esc(detail)}</div>` : ""}${chart ? `<span class="chart-hint">Visa graf ↗</span>` : ""}`;
      return chart
        ? `<button type="button" class="tile chart-action"${this._chartAttrs(chart, year)} aria-label="${esc(label)} – visa graf">${inner}</button>`
        : `<div class="tile">${inner}</div>`;
    }
    _kpi(icon, label, value, detail = "", chart = null, year = null) {
      const inner = `<div class="label">${icon} ${esc(label)}</div><div class="value">${esc(value)}</div>${detail ? `<div class="detail">${esc(detail)}</div>` : ""}${chart ? `<span class="chart-hint">Visa graf ↗</span>` : ""}`;
      return chart
        ? `<button type="button" class="kpi chart-action"${this._chartAttrs(chart, year)} aria-label="${esc(label)} – visa graf">${inner}</button>`
        : `<div class="kpi">${inner}</div>`;
    }
    _monthsForYear(year) {
      return this._months().filter((row) => row.month.startsWith(`${year}-`)).sort((a, b) => a.month.localeCompare(b.month));
    }
    _monthLabel(key) {
      if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(String(key || ""))) return "—";
      return new Intl.DateTimeFormat("sv-SE", { month:"short", timeZone:"UTC" }).format(new Date(`${key}-01T12:00:00Z`)).replace(".", "");
    }
    _chartGrid(maxValue, left, top, plotWidth, plotHeight, unit = "") {
      const scaleMax = Math.max(Number(maxValue) || 0, 1);
      return Array.from({ length:5 }, (_, index) => {
        const ratio = index / 4;
        const y = top + plotHeight - ratio * plotHeight;
        const value = scaleMax * ratio;
        return `<line class="gridline" x1="${left}" y1="${y}" x2="${left + plotWidth}" y2="${y}"></line><text x="${left - 10}" y="${y + 4}" text-anchor="end">${esc(fmt.format(value))}${unit ? ` ${esc(unit)}` : ""}</text>`;
      }).join("");
    }
    _barChart(rows, series, unit = "", stacked = false) {
      if (!rows.length) return `<div class="chart-empty">Ingen månadsdata för valt år.</div>`;
      const width = 900, height = 360, left = 78, right = 24, top = 24, bottom = 58;
      const plotWidth = width - left - right, plotHeight = height - top - bottom;
      const totals = rows.map((row) => stacked
        ? series.reduce((sum, item) => sum + (Number.isFinite(Number(row[item.key])) ? Number(row[item.key]) : 0), 0)
        : Math.max(...series.map((item) => Number.isFinite(Number(row[item.key])) ? Number(row[item.key]) : 0)));
      const maxValue = Math.max(...totals, 1) * 1.1;
      const step = plotWidth / rows.length;
      const groupWidth = Math.min(step * .68, 62);
      const barWidth = stacked ? groupWidth : groupWidth / Math.max(series.length, 1);
      let bars = "";
      rows.forEach((row, rowIndex) => {
        let accumulated = 0;
        series.forEach((item, seriesIndex) => {
          const value = Number(row[item.key]);
          if (!Number.isFinite(value) || value < 0) return;
          const h = value / maxValue * plotHeight;
          const x = left + rowIndex * step + (step - groupWidth) / 2 + (stacked ? 0 : seriesIndex * barWidth);
          const y = stacked ? top + plotHeight - (accumulated + value) / maxValue * plotHeight : top + plotHeight - h;
          bars += `<rect class="${seriesIndex === 0 ? "series-a-fill" : "series-b-fill"}" x="${x}" y="${y}" width="${Math.max(barWidth - (stacked ? 0 : 2), 3)}" height="${Math.max(h, 0)}" rx="4"><title>${esc(monthName(row.month))} · ${esc(item.label)}: ${esc(decimal(value, unit))}</title></rect>`;
          if (stacked) accumulated += value;
        });
        bars += `<text x="${left + rowIndex * step + step / 2}" y="${top + plotHeight + 24}" text-anchor="middle">${esc(this._monthLabel(row.month))}</text>`;
      });
      const legend = `<div class="chart-legend">${series.map((item) => `<span>${esc(item.label)}</span>`).join("")}</div>`;
      return `${legend}<div class="chart-wrap"><svg class="chart-svg" viewBox="0 0 ${width} ${height}" role="img">${this._chartGrid(maxValue,left,top,plotWidth,plotHeight,unit)}${bars}</svg></div>`;
    }
    _lineChart(rows, series, unit = "") {
      if (!rows.length) return `<div class="chart-empty">Ingen månadsdata för valt år.</div>`;
      const width = 900, height = 360, left = 78, right = 24, top = 24, bottom = 58;
      const plotWidth = width - left - right, plotHeight = height - top - bottom;
      const values = rows.flatMap((row) => series.map((item) => Number(row[item.key])).filter(Number.isFinite));
      const maxValue = Math.max(...values, 1) * 1.1;
      const step = rows.length > 1 ? plotWidth / (rows.length - 1) : plotWidth;
      let shapes = "";
      series.forEach((item, seriesIndex) => {
        let segment = [];
        const flush = () => {
          if (segment.length > 1) shapes += `<polyline class="${seriesIndex === 0 ? "series-a-line" : "series-b-line"}" points="${segment.join(" ")}"></polyline>`;
          segment = [];
        };
        rows.forEach((row, rowIndex) => {
          const value = Number(row[item.key]);
          if (!Number.isFinite(value) || value < 0) { flush(); return; }
          const x = left + (rows.length > 1 ? rowIndex * step : plotWidth / 2);
          const y = top + plotHeight - value / maxValue * plotHeight;
          segment.push(`${x},${y}`);
          shapes += `<circle class="${seriesIndex === 0 ? "series-a-dot" : "series-b-dot"}" cx="${x}" cy="${y}" r="5"><title>${esc(monthName(row.month))} · ${esc(item.label)}: ${esc(decimal(value, unit))}</title></circle>`;
        });
        flush();
      });
      const labels = rows.map((row,rowIndex) => {
        const x = left + (rows.length > 1 ? rowIndex * step : plotWidth / 2);
        return `<text x="${x}" y="${top + plotHeight + 24}" text-anchor="middle">${esc(this._monthLabel(row.month))}</text>`;
      }).join("");
      const legend = `<div class="chart-legend">${series.map((item) => `<span>${esc(item.label)}</span>`).join("")}</div>`;
      return `${legend}<div class="chart-wrap"><svg class="chart-svg" viewBox="0 0 ${width} ${height}" role="img">${this._chartGrid(maxValue,left,top,plotWidth,plotHeight,unit)}${shapes}${labels}</svg></div>`;
    }
    _categoryChart(rows) {
      const values = Array.isArray(rows) ? rows.filter((row) => row && Number.isFinite(Number(row.amount)) && Number(row.amount) >= 0) : [];
      if (!values.length) return `<div class="chart-empty">Inga kategoriserade utgifter för valt år.</div>`;
      const width = 900, rowHeight = 44, left = 220, right = 100, top = 18, bottom = 20;
      const height = top + bottom + values.length * rowHeight;
      const plotWidth = width - left - right;
      const maxValue = Math.max(...values.map((row) => Number(row.amount)), 1);
      const body = values.map((row,index) => {
        const value = Number(row.amount);
        const y = top + index * rowHeight;
        const barWidth = value / maxValue * plotWidth;
        return `<text class="axis-strong" x="${left - 12}" y="${y + 25}" text-anchor="end">${esc(row.name)}</text><rect class="series-a-fill" x="${left}" y="${y + 8}" width="${barWidth}" height="24" rx="6"><title>${esc(row.name)}: ${esc(kroner(value))}</title></rect><text x="${left + plotWidth + 12}" y="${y + 25}">${esc(kroner(value))}</text>`;
      }).join("");
      return `<div class="chart-wrap"><svg class="chart-svg" viewBox="0 0 ${width} ${height}" role="img">${body}</svg></div>`;
    }
    _chartModal() {
      if (!this._chart) return "";
      const year = /^\d{4}$/.test(String(this._chart.year || "")) ? String(this._chart.year) : String(new Date().getFullYear());
      const months = this._monthsForYear(year);
      const annual = this._years().find((row) => String(row.year) === year);
      let title = "Graf", content = "", note = "";
      if (this._chart.id === "costs") {
        title = "💳 Kostnader per månad";
        content = this._barChart(months, [{key:"fuel",label:"Bränsle"},{key:"other",label:"Övrigt"}], "kr", true);
        note = "Staplarna visar bokförda kostnader på betalnings-/tankningsdatum. Bränsle och övriga utgifter är staplade.";
      } else if (this._chart.id === "distance") {
        title = "🛣️ Avläst körsträcka per månad";
        content = this._barChart(months, [{key:"km",label:"ODO-körsträcka"}], "km");
        note = "Körsträckan bygger på Fuelios ODO-checkpoints. Första importerade månaden kan vara en delperiod.";
      } else if (this._chart.id === "litres") {
        title = "🛢️ Tankad volym per månad";
        content = this._barChart(months, [{key:"litres",label:"Tankade liter"}], "L");
        note = "Visar inköpt bränsle per månad, inte beräknat förbrukat bränsle.";
      } else if (this._chart.id === "cost-per-km") {
        title = "📏 Kostnad per avläst ODO-km";
        content = this._lineChart(months, [{key:"total_per_logged_km",label:"Bokfört totalt/km"},{key:"estimated_total_per_km",label:"Beräknad total/km"}], "kr/km");
        note = "Bokfört värde är faktiska utgifter ÷ ODO-differens. Beräknat värde använder uppskattad kostnad för förbrukat bränsle plus bokförda övriga utgifter.";
      } else if (this._chart.id === "categories") {
        title = "🧾 Utgifter per kategori";
        content = this._categoryChart(annual?.categories);
        note = "Kategorierna är årsaggregat från Fuelio. Mallposter och inkomster ingår inte.";
      } else {
        content = `<div class="chart-empty">Grafen är inte tillgänglig ännu.</div>`;
      }
      return `<div class="chart-backdrop"><section class="chart-modal" role="dialog" aria-modal="true" aria-label="${esc(title)}"><div class="chart-head"><div><h3>${esc(title)}</h3><div class="muted">År ${esc(year)}</div></div><button type="button" class="chart-close" data-chart-close aria-label="Stäng graf">✕</button></div><div class="chart-body">${content}</div>${note ? `<div class="chart-note">${esc(note)}</div>` : ""}</section></div>`;
    }
    _panel(icon, title, rows) {
      return `<section class="overview-panel"><h3>${icon} ${esc(title)}</h3>${rows.map(([label, value, note]) =>
        `<div class="overview-row"><span class="name">${esc(label)}</span><strong>${esc(value)}</strong>${note ? `<span class="note">${esc(note)}</span>` : ""}</div>`).join("")}</section>`;
    }
    _rangePanel(forecast) {
      const remaining = this._value("estimated_fuel_remaining_l");
      const capacity = Number(forecast?.tank_capacity_l);
      const percent = Number.isFinite(remaining) && Number.isFinite(capacity) && capacity > 0
        ? Math.max(0, Math.min(100, remaining / capacity * 100)) : null;
      return `<section class="range-panel">
        <div class="range-head"><h3>🧭 Tank & räckvidd</h3><span class="pill">${forecast?.confidence === "normal" ? "Kalibrerad" : forecast?.confidence === "limited" ? "Begränsat underlag" : "Estimat"}</span></div>
        <div class="range-main">
          <div class="range-stat"><span>Bränsle kvar</span><strong>${esc(decimal(remaining, "L"))}</strong></div>
          <div class="range-stat"><span>Teoretisk räckvidd</span><strong>${esc(decimal(this._value("estimated_range_remaining_km"), "km"))}</strong></div>
          <div class="range-stat"><span>Sedan senaste tankning</span><strong>${esc(decimal(this._value("distance_since_last_fillup_km"), "km"))}</strong></div>
          <div class="range-stat"><span>Nästa tankning</span><strong>${esc(date(this._state("estimated_next_fillup_date")?.state))}</strong></div>
        </div>
        <div>
          <div class="fuel-meter"><span style="width:${Number.isFinite(percent) ? percent.toFixed(1) : 0}%"></span></div>
          <div class="fuel-meter-note"><span>${Number.isFinite(percent) ? `Ca ${fmt.format(percent)} % kvar` : "Tanknivå saknas"}</span><span>${Number.isFinite(this._value("estimated_days_to_next_fillup")) ? `${decimal(this._value("estimated_days_to_next_fillup"), "dagar")} kvar` : "Körtempo saknas"}</span></div>
        </div>
      </section>`;
    }
    _section(id, icon, title, inner) {
      const open = this._open[id];
      return `<section class="section section-${id}"><button type="button" data-section="${id}" aria-expanded="${open}" aria-controls="panel-${id}"><span>${icon} ${esc(title)}</span><span aria-hidden="true">${open ? "⌃" : "⌄"}</span></button>${open ? `<div id="panel-${id}" class="body">${inner}</div>` : ""}</section>`;
    }
    _recordTile(key, title, unit) {
      const entry = this._state(key);
      const day = entry?.attributes?.recorded_on;
      return this._tile(key.includes("min") ? "↘️" : "↗️", title, decimal(num(entry), unit), date(day));
    }
    _render() {
      if (!this.shadowRoot || !this._config) return;
      if (!this._hass) {
        this.shadowRoot.innerHTML = `<style>${style}</style><ha-card><div class="shell">Läser Fuelio …</div></ha-card>`;
        return;
      }
      const allMonths = this._months();
      if (!this._month || !allMonths.some((row) => row.month === this._month)) this._month = allMonths[0]?.month || null;
      const selected = allMonths.find((row) => row.month === this._month);
      const currentYear = selected?.month?.slice(0, 4) || allMonths[0]?.month?.slice(0, 4) || String(new Date().getFullYear());
      const allYears = this._years();
      const selectedYear = allYears.find((item) => String(item.year) === currentYear) || null;
      if (!this._year || !allYears.some((item) => String(item.year) === this._year)) {
        this._year = String(allYears[0]?.year || currentYear);
      }
      const annualYear = allYears.find((item) => String(item.year) === this._year) || null;
      const yearTotal = selectedYear?.total ?? allMonths.filter((item) => item.month.startsWith(`${currentYear}-`)).reduce((sum, item) => sum + item.total, 0);
      const categories = (values, heading) => `<div class="section-title">${esc(heading)}</div>${Array.isArray(values) && values.length ? `<div class="category-list">${values.map((item) => `<div class="category-row"><span>${esc(item.name)}</span><strong>${esc(kroner(item.amount))}</strong></div>`).join("")}</div>` : `<div class="notice">Inga kategoriserade utgifter för perioden.</div>`}`;
      const historyTruncated = this._state("monthly_cost_breakdown")?.attributes?.history_truncated === true;
      const title = typeof this._config.title === "string" ? this._config.title : "Fuelio · Bilöversikt";
      const isAvailable = valid(this._state("monthly_cost_breakdown"));
      // The overview is always the CURRENT calendar month, independent of the
      // user's separate historical month selector in the Costs section.
      const nowMonth = allMonths[0];
      const odoNote = (period) => period?.odo_coverage === "partial_start" ?
        `Delperiod: ${period.odo_start_on || "första avläsning"} → ${period.odo_end_on || "senaste avläsning"}` :
        period?.odo_start_on && period?.odo_end_on ? `${period.odo_start_on} → ${period.odo_end_on}` : "Avläsningar saknas";
      const currentYearData = allYears.find((item) => String(item.year) === String(nowMonth?.month?.slice(0, 4)));
      const aggregate = this._state("monthly_cost_breakdown")?.attributes || {};
      const lifetime = aggregate.estimated_lifetime || {};
      const forecast = this._state("estimated_range_remaining_km")?.attributes || {};
      const coverageText = (row) => row?.estimate_coverage === "missing_rate" ? "Pris-/förbrukningsunderlag saknas" :
        row?.estimate_coverage?.includes?.("one_consumption_value") ? "En förbrukningsavläsning – begränsat underlag" :
        row?.odo_coverage === "partial_start" ? "Delperiod från första mätningen" : "Uppskattning";
      const syncText = dateTime(this._state("last_app_sync")?.state);
      const kpis = `<div class="kpi-strip">
        ${this._kpi("🛣️", "Mätarställning", decimal(this._value("latest_odometer_km"), "km"))}
        ${this._kpi("📍", "Körsträcka denna månad", decimal(nowMonth?.km, "km"), odoNote(nowMonth))}
        ${this._kpi("⛽", "Senaste förbrukning", decimal(this._value("last_reported_consumption"), "L/100 km"))}
        ${this._kpi("💳", "Utgifter denna månad", kroner(nowMonth?.total))}
        ${this._kpi("📏", "Körkostnad denna månad", decimal(nowMonth?.estimated_total_per_km, "kr/km"), coverageText(nowMonth))}
        ${this._kpi("🧭", "Räckvidd kvar", decimal(this._value("estimated_range_remaining_km"), "km"))}
      </div>`;
      const overview = `<div class="overview">
        ${this._panel("🛣️", "Mätarställning", [
          ["Aktuell", decimal(this._value("latest_odometer_km"), "km")],
          ["Denna månad", decimal(nowMonth?.km, "km"), odoNote(nowMonth)],
          ["I år", decimal(currentYearData?.km, "km"), currentYearData?.odo_coverage === "partial_start" ? "Delperiod" : ""],
          ["Sedan importstart", decimal(aggregate.lifetime_odometer_km, "km")]
        ])}
        ${this._panel("⛽", "Drivmedel", [
          ["Senaste", decimal(this._value("last_reported_consumption"), "L/100 km")],
          ["Löpande snitt", decimal(aggregate.latest_two_consumption, "L/100 km"), `${aggregate.latest_two_consumption_count || 0} giltiga tankningar`],
          ["Tankat denna månad", decimal(nowMonth?.litres, "L")],
          ["Tankat i år", decimal(currentYearData?.litres, "L")]
        ])}
        ${this._panel("💳", "Bokförda utgifter", [
          ["Denna månad", kroner(nowMonth?.total)],
          ["Innevarande år", kroner(currentYearData?.total)]
        ])}
        ${this._panel("📏", "Beräknad körkostnad/km", [
          ["Denna månad", decimal(nowMonth?.estimated_total_per_km, "kr/km"), coverageText(nowMonth)],
          ["Innevarande år", decimal(currentYearData?.estimated_total_per_km, "kr/km"), coverageText(currentYearData)]
        ])}
        ${this._rangePanel(forecast)}
      </div>`;
      const annual = `<label class="select-label" for="fuelio-year">Visa år</label>
      <select id="fuelio-year" ${allYears.length ? "" : "disabled"}>${allYears.map((row) => `<option value="${esc(String(row.year))}" ${String(row.year) === this._year ? "selected" : ""}>${esc(String(row.year))}</option>`).join("")}</select>
      <div class="section-title annual-hero">Årsrapport · ${esc(this._year || "—")}</div>
      <div class="annual-grid">
        ${this._tile("🛣️", "Avläst körsträcka", decimal(annualYear?.km, "km"), odoNote(annualYear))}
        ${this._tile("🚙", "Loggade resor", decimal(annualYear?.trip_count, "st"))}
        ${this._tile("📏", "Genomsnitt/resa", decimal(annualYear?.average_trip_km, "km"))}
        ${this._tile("🛢️", "Tankad volym", decimal(annualYear?.litres, "L"))}
        ${this._tile("⛽", "Tankningar", decimal(annualYear?.fuel_ups, "st"))}
        ${this._tile("📉", "Rapporterat snitt", decimal(annualYear?.average_reported_consumption, "L/100 km"), `${annualYear?.reported_consumption_samples ?? 0} giltiga mätningar`)}
      </div>
      <div class="annual-columns">
        <div class="annual-block">
          <div class="section-title">Kostnader · ${esc(this._year || "—")}</div>
          <div class="grid">
            ${this._tile("⛽", "Bränsle", kroner(annualYear?.fuel))}
            ${this._tile("🧾", "Övriga utgifter", kroner(annualYear?.other))}
            ${this._tile("💳", "Totalt", kroner(annualYear?.total))}
            ${this._tile("📏", "Bokfört totalt/km", decimal(annualYear?.total_per_logged_km, "kr/km"), "Bokförda utgifter ÷ ODO-differens")}
            ${this._tile("🔥", "Beräknat förbrukat bränsle", kroner(annualYear?.estimated_fuel), coverageText(annualYear))}
            ${this._tile("📐", "Beräknad total/km", decimal(annualYear?.estimated_total_per_km, "kr/km"), coverageText(annualYear))}
          </div>
        </div>
        <div class="annual-block">
          <div class="section-title">Bränsle & effektivitet · ${esc(this._year || "—")}</div>
          <div class="grid">
            ${this._tile("💰", "Genomsnittligt literpris", decimal(annualYear?.average_fuel_price, "kr/L"), "Bränslekostnad ÷ tankade liter")}
            ${this._tile("↘️", "Lägsta literpris", decimal(annualYear?.fuel_price_min, "kr/L"))}
            ${this._tile("↗️", "Högsta literpris", decimal(annualYear?.fuel_price_max, "kr/L"))}
            ${this._tile("↘️", "Lägsta förbrukning", decimal(annualYear?.consumption_min, "L/100 km"))}
            ${this._tile("↗️", "Högsta förbrukning", decimal(annualYear?.consumption_max, "L/100 km"))}
            ${this._tile("📊", "Förbrukningsunderlag", decimal(annualYear?.reported_consumption_samples, "st"), "Rapporterade positiva värden")}
          </div>
          ${categories(annualYear?.categories, `Utgifter per kategori · ${this._year || "—"}`)}
        </div>
      </div>
      <div class="notice">Årsrapporten använder Fuelios importerade data för valt kalenderår. Första importerade året kan vara en delperiod; avläst körsträcka bygger på ODO-checkpoints. Rapporterat snitt är medelvärdet av årets giltiga positiva L/100 km-poster. Genomsnittligt literpris är faktiskt bokförd bränslekostnad delat med årets tankade liter.</div>`;

      const costs = `<div class="grid">
        ${this._tile("📅", "Denna månad", kroner(allMonths[0]?.total))}
        ${this._tile("🗓️", `År ${currentYear}`, allMonths.length ? kroner(yearTotal) : "—")}
      </div><label class="select-label" for="fuelio-month">Visa månad</label>
      <select id="fuelio-month" ${allMonths.length ? "" : "disabled"}>${allMonths.map((row) => `<option value="${esc(row.month)}" ${row.month === this._month ? "selected" : ""}>${esc(monthName(row.month))}</option>`).join("")}</select>
      <div class="section-title">${esc(selected ? monthName(selected.month) : "Ingen månadshistorik")}</div>
      <div class="grid">
        ${this._tile("⛽", "Bränsle", kroner(selected?.fuel))}
        ${this._tile("🧾", "Övriga utgifter", kroner(selected?.other))}
        ${this._tile("💳", "Totalt", kroner(selected?.total))}
      </div><div class="section-title">Månadsstatistik · ${esc(selected ? monthName(selected.month) : "Ingen historik")}</div>
      <div class="grid">
        ${this._tile("🛣️", "Avläst körsträcka", decimal(selected?.km, "km"), selected?.odo_coverage === "partial_start" ? "Delperiod" : "ODO-differens")}
        ${this._tile("🚙", "Loggade resor", decimal(selected?.trip_count, "st"))}
        ${this._tile("📏", "Genomsnitt/resa", decimal(selected?.average_trip_km, "km"), "Loggade reskilometer ÷ antal resor")}
      </div><div class="summary"><span><strong>Totalt sedan importstart</strong><br><span class="muted">Bränsle ${esc(kroner(this._value("fuel_cost")))} · Övrigt ${esc(kroner(this._value("other_expenses")))}</span></span><strong>${esc(kroner(this._value("total_actual_cost")))}</strong></div>
      ${categories(selected?.categories, "Utgifter per kategori · vald månad")}
      ${categories(selectedYear?.categories, `Utgifter per kategori · år ${currentYear}`)}
      <div class="summary"><span>Uppskattad resekostnad · hela importen (inte faktisk utgift)</span><strong>${esc(kroner(this._value("estimated_trip_cost")))}</strong></div>
      <div class="section-title">Beräknad körkostnad · förbrukat bränsle</div>
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
      <div class="grid">
        ${this._tile("⛽", "Bränsle · månad", decimal(selected?.fuel_per_logged_km, "kr/km"), odoNote(selected))}
        ${this._tile("💳", "Totalt · månad", decimal(selected?.total_per_logged_km, "kr/km"), odoNote(selected))}
        ${this._tile("⛽", `Bränsle · ${currentYear}`, decimal(selectedYear?.fuel_per_logged_km, "kr/km"), odoNote(selectedYear))}
        ${this._tile("💳", `Totalt · ${currentYear}`, decimal(selectedYear?.total_per_logged_km, "kr/km"), odoNote(selectedYear))}
        ${this._tile("⛽", "Bränsle · sedan start", decimal(this._value("fuel_cost_per_km_all"), "kr/km"))}
        ${this._tile("💳", "Totalt · sedan start", decimal(this._value("total_cost_per_km_all"), "kr/km"))}
      </div>
      <div class="notice">Bokförda utgifter ÷ ODO-differens, från senaste avläsning före periodstart till senaste inom perioden. Saknas tidigare avläsning räknas bara körning efter första avläsningen och perioden markeras som ofullständig. Saknas användbar differens visas —. Tankningar uppdaterar belopp och mätarställning vid nästa ZIP-inläsning.</div>
      ${historyTruncated ? `<div class="notice">Månadsväljaren visar de senaste 120 månaderna. Livstidssumman inkluderar även äldre data.</div>` : ""}`;
      const fuel = `<div class="grid">
        ${this._tile("⛽", "Senaste förbrukning", decimal(this._value("last_reported_consumption"), "L/100 km"), "Rapporterat värde, inte livstidssnitt")}
        ${this._tile("💰", "Senaste literpris", decimal(this._value("last_fuel_price"), "kr/L"))}
        ${this._tile("🛢️", "Tankad volym", decimal(this._value("fuel_litres"), "L"), "Sedan importstart")}
        ${this._tile("📆", "Senaste tankning", date(this._state("last_fillup_date")?.state))}
      </div><div class="notice">Räckvidden räknas från senaste fulltankning som kalibreringspunkt. Senare deltankningar adderas och beräknad förbrukning dras av. Nästa tankdatum använder de senaste 30 dagarnas loggade körtempo och avser teoretiskt tom tank.</div><div class="section-title">Antal tankningar</div><div class="grid">
        ${this._tile("📅", "Vald månad", decimal(selected?.fuel_ups, "st"))}
        ${this._tile("🗓️", `År ${currentYear}`, decimal(selectedYear?.fuel_ups, "st"))}
        ${this._tile("⛽", "Sedan importstart", decimal(this._value("fuel_count"), "st"))}
      </div>`;
      const records = `<div class="section-title">Literpris · kalenderåret</div><div class="records-grid">
        ${this._recordTile("fuel_price_min_year", "Lägsta i år", "kr/L")}
        ${this._recordTile("fuel_price_max_year", "Högsta i år", "kr/L")}
      </div><div class="section-title">Literpris · sedan importstart</div><div class="records-grid">
        ${this._recordTile("fuel_price_min_all", "Lägsta totalt", "kr/L")}
        ${this._recordTile("fuel_price_max_all", "Högsta totalt", "kr/L")}
      </div><div class="section-title">Rapporterad förbrukning · kalenderåret</div><div class="records-grid">
        ${this._recordTile("consumption_min_year", "Lägsta i år", "L/100 km")}
        ${this._recordTile("consumption_max_year", "Högsta i år", "L/100 km")}
      </div><div class="section-title">Rapporterad förbrukning · sedan importstart</div><div class="records-grid">
        ${this._recordTile("consumption_min_all", "Lägsta totalt", "L/100 km")}
        ${this._recordTile("consumption_max_all", "Högsta totalt", "L/100 km")}
      </div><div class="notice">Rekorden bygger på registrerade tankningar med giltiga positiva värden. Datumet visas under varje rekord. Saknade värden visas som —. Ett rekord per tankning är inte samma sak som ett vägt livstidssnitt.</div>`;
      const service = `<div class="notice">Serviceintervall och betalningspåminnelser finns ännu inte i HA-Fuelios datamodell. Tank- och räckviddsprognosen visas i översikten och under Bränsle.</div>`;
      const version = `<div class="summary"><span>Kort</span><strong>HA-Fuelio Card</strong></div><div class="summary"><span>Frontend-version</span><strong>${CARD_VERSION}</strong></div><div class="summary"><span>Senaste ZIP-uppdatering</span><strong>${esc(syncText)}</strong></div><div class="summary"><span>Resurs</span><strong>/local/ha-fuelio-card.js</strong></div><div class="notice">ZIP-tiden är filens modifieringstid. I din rclone-kedja bevaras Drive-filens tid när ZIP:en kopieras till Home Assistant.</div>`;
      this.shadowRoot.innerHTML = `<style>${style}</style><ha-card><div class="shell">
        <div class="header">
          <div class="title-wrap"><h2>🚙 ${esc(title)}</h2><span class="muted">Desktop dashboard · Fuelio read-only</span></div>
          <div class="header-meta">
            <span class="pill">${isAvailable ? "✅ Data tillgänglig" : "⚠️ Data saknas"}</span>
            <span class="pill">🗜️ ZIP uppdaterad <strong>${esc(syncText)}</strong></span>
            <span class="pill">🚗 Senaste resa <strong>${esc(date(this._state("last_trip_date")?.state))}</strong></span>
          </div>
        </div>
        ${kpis}
        ${overview}
        <div class="tripbar"><span>🛣️ <strong>${esc(decimal(this._value("trip_count"), "resor"))}</strong> · ${esc(decimal(this._value("trip_distance_km"), "km"))} · ${esc(decimal(this._value("trip_duration_hours"), "h"))}</span><span class="muted">Löpande Fuelio-statistik sedan importstart</span></div>
        <div class="dashboard-grid">
          ${this._section("annual", "📊", "Årsöversikt", annual)}
          ${this._section("costs", "💳", "Kostnader", costs)}
          ${this._section("fuel", "⛽", "Bränsle", fuel)}
          ${this._section("records", "🏆", "Pris- & förbrukningsrekord", records)}
          ${this._section("service", "🔧", "Service & underhåll", service)}
          ${this._section("version", "ℹ️", "Versionsinformation", version)}
        </div>
        <div class="foot muted">Fuelio · read-only · ${CARD_VERSION}</div>
      </div></ha-card>`;
    }
  }

  if (!customElements.get("ha-fuelio-card")) customElements.define("ha-fuelio-card", HaFuelioCard);
  window.customCards = window.customCards || [];
  if (!window.customCards.some((card) => card.type === "ha-fuelio-card")) {
    window.customCards.push({ type: "ha-fuelio-card", name: "HA-Fuelio Card", description: "Fuelio dashboard med årsöversikt, kostnader, tankningar och historiska rekord." });
  }
})();
