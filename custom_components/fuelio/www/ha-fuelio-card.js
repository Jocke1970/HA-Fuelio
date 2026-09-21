/* HA-Fuelio Card 0.1.0-dev.1 — self-contained, read-only Lovelace card. */
(() => {
  "use strict";
  const CARD_VERSION = "0.1.0-dev.1";
  const fmt = new Intl.NumberFormat("sv-SE", { maximumFractionDigits: 2 });
  const money = new Intl.NumberFormat("sv-SE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const valid = (state) => state && !["unknown", "unavailable", "none", "null", ""].includes(String(state.state).toLowerCase());
  const num = (state) => valid(state) && Number.isFinite(Number(state.state)) ? Number(state.state) : null;
  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const kroner = (value) => Number.isFinite(value) ? `${money.format(value)} kr` : "—";
  const decimal = (value, unit = "") => Number.isFinite(value) ? `${fmt.format(value)}${unit ? ` ${unit}` : ""}` : "—";
  const date = (value) => /^\d{4}-\d{2}-\d{2}$/.test(String(value || "")) ? value : "—";
  const monthName = (key) => /^\d{4}-(0[1-9]|1[0-2])$/.test(key)
    ? new Intl.DateTimeFormat("sv-SE", { month: "long", year: "numeric", timeZone: "UTC" }).format(new Date(`${key}-01T12:00:00Z`))
    : "Okänd månad";
  const style = `
    :host { display:block; color:var(--primary-text-color, #202124); font:inherit; }
    * { box-sizing:border-box; }
    .shell { overflow:hidden; border-radius:22px; padding:16px; background:var(--ha-card-background, var(--card-background-color,#fff)); box-shadow:var(--ha-card-box-shadow,0 1px 4px #00000019); }
    .header { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:16px; }
    h2 { font-size:1.2rem; margin:0; font-weight:750; } h3 { font-size:1rem; margin:0; }
    .muted { color:var(--secondary-text-color,#68727d); font-size:.79rem; }
    .pill { padding:5px 9px; border-radius:99px; background:var(--secondary-background-color,#eef1f4); font-size:.73rem; }
    .grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }
    .tile { min-width:0; border:1px solid var(--divider-color,#e2e4e8); border-radius:17px; padding:14px 9px; text-align:center; }
    .tile .ico { font-size:1.2rem; display:block; margin-bottom:7px; }
    .tile .label { font-size:.78rem; font-weight:700; margin-bottom:7px; }
    .tile .value { font-weight:780; font-size:1.05rem; overflow-wrap:anywhere; font-variant-numeric:tabular-nums; }
    .tile .detail { font-size:.71rem; color:var(--secondary-text-color,#68727d); margin-top:5px; }
    .section { margin-top:12px; border:1px solid var(--divider-color,#e2e4e8); border-radius:18px; overflow:hidden; }
    .section>button { cursor:pointer; display:flex; align-items:center; justify-content:space-between; width:100%; background:none; border:none; color:inherit; padding:14px; text-align:left; font:inherit; font-weight:750; }
    .section>button:focus-visible,select:focus-visible { outline:2px solid var(--primary-color,#03a9f4); outline-offset:-2px; }
    .body { padding:0 12px 13px; } .section-title { font-weight:750; margin:14px 2px 9px; font-size:.9rem; }
    .select-label { display:block; margin:12px 2px 6px; font-size:.78rem; color:var(--secondary-text-color,#68727d); }
    select { width:100%; color:inherit; background:var(--ha-card-background,var(--card-background-color,#fff)); border:1px solid var(--divider-color,#d4d9df); border-radius:12px; padding:11px 10px; font:inherit; }
    .summary { border:1px solid var(--divider-color,#e2e4e8); border-radius:15px; padding:11px; display:flex; align-items:center; justify-content:space-between; gap:8px; margin-top:10px; font-size:.8rem; }
    .summary strong { font-variant-numeric:tabular-nums; text-align:right; }
    .notice { padding:12px; margin-top:10px; background:var(--secondary-background-color,#f4f5f7); color:var(--secondary-text-color,#68727d); border-radius:13px; font-size:.8rem; line-height:1.45; }
    .small { font-size:.75rem; } .foot { text-align:right; margin-top:12px; }
    @media (min-width:620px) { .shell { padding:20px; } .grid { grid-template-columns:repeat(4,minmax(0,1fr)); } .records { grid-template-columns:repeat(4,minmax(0,1fr)); } }
    @media (max-width:340px) { .tile { padding:11px 5px; } .tile .value { font-size:.92rem; } }
  `;

  class HaFuelioCard extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this._open = { costs: true, fuel: true, records: true, service: false, version: false };
      this._month = null;
      this._signature = null;
      this.shadowRoot.addEventListener("click", (event) => {
        const button = event.target.closest?.("button[data-section]");
        if (!button) return;
        const section = button.dataset.section;
        if (!Object.prototype.hasOwnProperty.call(this._open, section)) return;
        this._open[section] = !this._open[section];
        this._render();
      });
      this.shadowRoot.addEventListener("change", (event) => {
        if (event.target?.id !== "fuelio-month") return;
        const candidate = event.target.value;
        const available = this._months();
        if (available.some((item) => item.month === candidate)) {
          this._month = candidate;
          this._render();
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
        "fuel_price_min_year", "fuel_price_max_year", "fuel_price_min_all", "fuel_price_max_all",
        "consumption_min_year", "consumption_max_year", "consumption_min_all", "consumption_max_all",
      ];
      // React only when Fuelio values change, not on every unrelated HA state update.
      const signature = sensorKeys.map((key) => {
        const entry = hass.states[this._prefix + key];
        return entry ? `${entry.state}|${entry.last_updated || ""}|${key === "monthly_cost_breakdown" ? JSON.stringify(entry.attributes?.months || []) : (entry.attributes?.recorded_on || "")}` : "missing";
      }).join(";");
      if (signature === this._signature) return;
      this._signature = signature;
      this._render();
    }

    _state(key) { return this._hass?.states?.[this._prefix + key]; }
    _value(key) { return num(this._state(key)); }
    _months() {
      const rows = this._state("monthly_cost_breakdown")?.attributes?.months;
      if (!Array.isArray(rows)) return [];
      return rows.filter((row) => row && /^\d{4}-(0[1-9]|1[0-2])$/.test(row.month) &&
        ["fuel", "other", "total"].every((key) => Number.isFinite(row[key]))).slice(0, 120);
    }
    _tile(icon, label, value, detail = "") {
      return `<div class="tile"><span class="ico" aria-hidden="true">${icon}</span><div class="label">${esc(label)}</div><div class="value">${esc(value)}</div>${detail ? `<div class="detail">${esc(detail)}</div>` : ""}</div>`;
    }
    _section(id, icon, title, inner) {
      const open = this._open[id];
      return `<section class="section"><button type="button" data-section="${id}" aria-expanded="${open}" aria-controls="panel-${id}"><span>${icon} ${esc(title)}</span><span aria-hidden="true">${open ? "⌃" : "⌄"}</span></button>${open ? `<div id="panel-${id}" class="body">${inner}</div>` : ""}</section>`;
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
      const currentYear = allMonths[0]?.month?.slice(0, 4) || String(new Date().getFullYear());
      const yearTotal = allMonths.filter((item) => item.month.startsWith(`${currentYear}-`)).reduce((sum, item) => sum + item.total, 0);
      const historyTruncated = this._state("monthly_cost_breakdown")?.attributes?.history_truncated === true;
      const title = typeof this._config.title === "string" ? this._config.title : "Fuelio · Bilöversikt";
      const isAvailable = valid(this._state("monthly_cost_breakdown"));
      const overview = `<div class="grid">
        ${this._tile("🛣️", "Mätarställning", decimal(this._value("latest_odometer_km"), "km"))}
        ${this._tile("⛽", "Senaste förbrukning", decimal(this._value("last_reported_consumption"), "L/100 km"))}
        ${this._tile("💰", "Literpris", decimal(this._value("last_fuel_price"), "kr/L"))}
        ${this._tile("🧾", "Tankningar", decimal(this._value("fuel_count"), "st"))}
      </div>`;
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
        ${this._tile("📉", "Uppskattad körkostnad", kroner(this._value("estimated_trip_cost")), "Hela exporten · ej faktisk utgift")}
      </div><div class="summary"><span><strong>Totalt sedan importstart</strong><br><span class="muted">Bränsle ${esc(kroner(this._value("fuel_cost")))} · Övrigt ${esc(kroner(this._value("other_expenses")))}</span></span><strong>${esc(kroner(this._value("total_actual_cost")))}</strong></div>
      ${historyTruncated ? `<div class="notice">Månadsväljaren visar de senaste 120 månaderna. Livstidssumman inkluderar även äldre data.</div>` : ""}`;
      const fuel = `<div class="grid">
        ${this._tile("⛽", "Senaste förbrukning", decimal(this._value("last_reported_consumption"), "L/100 km"), "Rapporterat värde, inte livstidssnitt")}
        ${this._tile("💰", "Senaste literpris", decimal(this._value("last_fuel_price"), "kr/L"))}
        ${this._tile("🛢️", "Tankad volym", decimal(this._value("fuel_litres"), "L"), "Sedan importstart")}
        ${this._tile("📆", "Senaste tankning", date(this._state("last_fillup_date")?.state))}
      </div>`;
      const records = `<div class="section-title">Literpris · kalenderåret</div><div class="grid records">
        ${this._recordTile("fuel_price_min_year", "Lägsta i år", "kr/L")}
        ${this._recordTile("fuel_price_max_year", "Högsta i år", "kr/L")}
      </div><div class="section-title">Literpris · sedan importstart</div><div class="grid records">
        ${this._recordTile("fuel_price_min_all", "Lägsta totalt", "kr/L")}
        ${this._recordTile("fuel_price_max_all", "Högsta totalt", "kr/L")}
      </div><div class="section-title">Rapporterad förbrukning · kalenderåret</div><div class="grid records">
        ${this._recordTile("consumption_min_year", "Lägsta i år", "L/100 km")}
        ${this._recordTile("consumption_max_year", "Högsta i år", "L/100 km")}
      </div><div class="section-title">Rapporterad förbrukning · sedan importstart</div><div class="grid records">
        ${this._recordTile("consumption_min_all", "Lägsta totalt", "L/100 km")}
        ${this._recordTile("consumption_max_all", "Högsta totalt", "L/100 km")}
      </div><div class="notice">Rekorden bygger på registrerade tankningar med giltiga positiva värden. Datumet visas under varje rekord. Saknade värden visas som —. Ett rekord per tankning är inte samma sak som ett vägt livstidssnitt.</div>`;
      const service = `<div class="notice">Serviceintervall, betalningspåminnelser, tanknivå och räckvidd finns ännu inte i HA-Fuelios datamodell. Inga Drivvo-värden används eller gissas här.</div>`;
      const version = `<div class="summary"><span>Kort</span><strong>HA-Fuelio Card</strong></div><div class="summary"><span>Frontend-version</span><strong>${CARD_VERSION}</strong></div><div class="summary"><span>Resurs</span><strong>/local/ha-fuelio-card.js</strong></div><div class="notice">Lokal Fuelio ZIP · läses ungefär var femte minut. Kortet läser endast HA-entiteter och gör inga serviceanrop.</div>`;
      this.shadowRoot.innerHTML = `<style>${style}</style><ha-card><div class="shell"><div class="header"><h2>🚙 ${esc(title)}</h2><span class="pill">${isAvailable ? "✅ Data tillgänglig" : "⚠️ Data saknas"}</span></div>
        ${overview}
        <div class="summary"><span>🛣️ ${esc(decimal(this._value("trip_count"), "resor"))} · ${esc(decimal(this._value("trip_distance_km"), "km"))} · ${esc(decimal(this._value("trip_duration_hours"), "h"))}</span><span class="muted">Senaste resa ${esc(date(this._state("last_trip_date")?.state))}</span></div>
        ${this._section("costs", "💳", "Kostnader", costs)}
        ${this._section("fuel", "⛽", "Bränsle", fuel)}
        ${this._section("records", "🏆", "Pris- & förbrukningsrekord", records)}
        ${this._section("service", "🔧", "Service & underhåll", service)}
        ${this._section("version", "ℹ️", "Versionsinformation", version)}
        <div class="foot muted">Fuelio · read-only · ${CARD_VERSION}</div>
      </div></ha-card>`;
    }
  }

  if (!customElements.get("ha-fuelio-card")) customElements.define("ha-fuelio-card", HaFuelioCard);
  window.customCards = window.customCards || [];
  if (!window.customCards.some((card) => card.type === "ha-fuelio-card")) {
    window.customCards.push({ type: "ha-fuelio-card", name: "HA-Fuelio Card", description: "Fuelio dashboard med kostnader, tankningar och historiska rekord." });
  }
})();
