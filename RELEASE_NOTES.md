# HA-Fuelio 2026.11.3b4 🚗📐

Compact overview formatting polish, following the 3b3 2×2 layout fix.

- Keep odometer values on one line with `km` centered underneath in the four-card overview.
- Keep fuel-consumption numbers on one line with `L/100 km` centered underneath.
- Show whole SEK (no öre) for the collapsed **Booked expenses** monthly and yearly values; preserve precise amounts in the detailed sections and underlying data.
- Shorten the fourth overview heading to **Körkostnad** / **Driving cost** while retaining `kr/km` with the values.
- Tighten summary typography and horizontal padding for normal HA card widths.
- Keep calculations, all entities, tank/range calibration and mobile card unchanged.
- Tested source expectations updated; `main` remains stable at `2026.11.2` pending live HA visual validation.

# HA-Fuelio 2026.11.3b3 🧩

- Lower the overview 2×2 card-grid breakpoint from 430 px to 340 px to fit standard Home Assistant columns.
- Center overview row labels and Tank & range stat content.
- Preserve existing data, calculations and all entity IDs.

# HA-Fuelio 2026.11.3b2 📐✨

Responsive 2×2 overview polish.

- Lower the four-card overview breakpoint to 430 px so normal dashboard columns render the intended 2×2 grid instead of falling back to a 1×4 stack.
- Keep true narrow/mobile layouts single-column.
- Center label, primary value and detail text in the six KPI tiles at the top of the desktop dashboard.
- Preserve the centered summary-card titles, paired key values, full-width expansion behavior and existing calculations.
- No backend, entity, data-model or calibration changes.
- Sync manifest, desktop/mobile card versions and documentation to `2026.11.3b2`.
- Release flow remains `dev → beta → main`; stable `2026.11.2` stays on `main` pending real-HA visual validation.

# HA-Fuelio 2026.11.3b1 🧩📐

Centered 2×2 overview summary cards.

- Redesign the four compact overview expanders — Odometer, Fuel, Booked expenses and Estimated driving cost/km — as a centered 2×2 card grid on desktop.
- Keep two equally weighted key values visible in every collapsed card beneath a centered title.
- Make the whole card clickable and keep the chevron unobtrusive in the top-right corner.
- Expand an opened overview card across the full two-column summary-grid width.
- Keep detailed rows centered inside the opened card.
- Fall back to a single-column summary grid on narrow layouts.
- Keep Tank & range first and full-width above the four summary cards.
- Preserve all existing calculations, entities, expand/collapse state and backend behavior; this release is frontend layout only.
- Sync desktop/mobile card versions and documentation to `2026.11.3b1`.
- Release flow remains `dev → beta → main`; stable `2026.11.2` stays on `main` pending real-HA visual validation.

# HA-Fuelio 2026.11.2 ⛽🎯✅

Stable OBD fuel-left calibration release.

- Promote the live-validated `2026.11.2b1` OBD fuel-left calibration to stable.
- Keep fuel-left as the primary current-tank anchor, with optional range and OBD average-consumption consistency checks.
- Preserve forward counting from the OBD snapshot using ODO distance and later partial fills.
- Preserve automatic reset on the next primary full fill-up and the legacy range-only fallback.
- Keep desktop/mobile English/Swedish calibration UI and all existing sensor/entity IDs unchanged.
- Include the Contributors acknowledgement in the stable README.
- No new sensors or source/write-back changes from the validated beta.
- Complete the release path `dev → beta → main`.

# HA-Fuelio 2026.11.2b1 ⛽🎯

OBD fuel-left calibration for the current tank.

- Add a new `calibrate_fuel_left` Home Assistant service with required `fuel_left_l` and optional `range_km` / `consumption_l_per_100km` inputs.
- Treat OBD-reported fuel left as the primary current-tank anchor instead of forcing fuel remaining to be derived only from a historical full fill-up.
- If range and OBD average consumption are both provided, validate that `fuel_left / range × 100` agrees with the OBD consumption within a bounded tolerance before accepting the snapshot.
- Use OBD consumption when supplied; otherwise infer consumption from fuel-left + range, or fall back to the automatic Fuelio basis when only fuel-left is provided.
- After calibration, count fuel forward from the OBD snapshot using ODO distance and later recorded partial fills.
- Clear the fuel-left calibration automatically on the next registered primary full fill-up, matching existing manual-calibration lifecycle semantics.
- Keep the legacy range-only calibration available when fuel-left is left blank.
- Add desktop/mobile calibration fields for fuel left, range and OBD average consumption, with English/Swedish UI text.
- Add regression coverage using a `44.38 L / 789 km / 5.6 L/100 km` OBD snapshot plus forward-counting and inconsistency rejection tests.
- Preserve all existing sensor/entity IDs and the read-only Fuelio ZIP contract; no new sensors are added.
- Release flow remains `dev → beta → main`; stable `2026.11.1` stays on `main` pending real-HA beta validation.

# HA-Fuelio 2026.11.1 🌐📅✅

Stable bilingual integration and calendar-options release.

- Promote the bilingual English/Swedish integration UI from `2026.11.1b1` to stable.
- Keep all 42 sensor friendly names localized through Home Assistant translation keys.
- Keep config flow, options, range-calibration services and both bundled dashboard cards bilingual.
- Keep the Fuelio calendar optional through **Configure**, defaulting to enabled for backward compatibility.
- Preserve the English-only repository documentation policy.
- Preserve existing sensor unique IDs/entity IDs and the calendar unique ID.
- No source ZIP, write-back, statistics or dashboard-layout logic changes from the validated beta.
- Complete the release path `dev → beta → main`.

# HA-Fuelio 2026.11.1b1 🌐📅

Bilingual integration UI and optional calendar platform.

- Add English/Swedish Home Assistant translations for config flow, options, all 42 sensor friendly names and range-calibration services.
- Update both bundled dashboard cards to follow the Home Assistant/browser language while preserving the existing Swedish UI as the Swedish locale.
- Replace stale "development build" configuration text and use a language-neutral config-entry title for new installations.
- Add an Options Flow with **Enable Fuelio calendar**, defaulting to **on** so existing installations preserve the 2026.11.0 behavior.
- Reload the config entry when options change; disabling the calendar leaves all sensor/dashboard functionality intact.
- Use canonical English fallback category labels in aggregate data (`Uncategorized`, `Other categories`); the Swedish dashboard localizes those presentation labels.
- Make fixed calendar metadata more language-neutral (`ODO`, note marker) while retaining Fuelio user-entered titles/categories unchanged.
- Standardize repository documentation in English and add EN/SV translation-parity regression coverage.
- Preserve existing sensor unique IDs/entity IDs and the calendar unique ID. No source ZIP or write-back behavior changes.
- Release flow remains `dev → beta → main`; stable `2026.11.0` stays on `main` until this beta is live-tested.

# HA-Fuelio 2026.11.0 🚙✅

Stable November 2026 release.

Promoted from beta.11 after live Home Assistant validation of the complete desktop/mobile flow and final UI polish.

- Stable dashboard architecture with compact summary expanders, Tank & range first, Trip statistics drill-down and inline graphs.
- Trip statistics supports year → month → ISO week → day, with TripDist kept separate from ODO checkpoints and rolling 3-period averages on single-series charts.
- Read-only Fuelio calendar includes timed TripLog journeys plus sanitized current/future cost events.
- Measured full→full fuel-economy windows feed the range model with safe fallbacks and manual current-tank calibration.
- Top status chips are left-aligned, wrap cleanly and retain readable availability/sync/latest-trip hierarchy.
- Source remains the local Fuelio ZIP only; no write-back to Fuelio.
- No entity-ID migration in this stable release. Existing 42 sensors plus the existing calendar entity remain intact.
- Release path completed as `dev → beta → main`.

# HA-Fuelio 2026.11.0b11 ✨🚙

Top status-chip polish before stable promotion.

- Move the header status chips into a dedicated left-aligned row beneath the title.
- Let the row wrap naturally from the left so **Latest trip** no longer appears as an orphaned right-aligned chip on narrow layouts.
- Give **Data available** a subtle positive tint, keep **ZIP updated** as the primary neutral status, and visually tone down **Latest trip**.
- Keep all dashboard calculations, overview ordering, Trip statistics and entity contracts unchanged.
- No new sensors, backend storage, write-back or data-model changes.
- Preserve all 42 sensor unique IDs/entity IDs and the existing calendar entity; total integration entity count remains **43**.
- Sync manifest, desktop/mobile card versions and documentation to `2026.11.0b11`.
- Release flow remains `dev → beta → main`; after final real-HA visual validation, this beta is intended for stable promotion.

# HA-Fuelio 2026.11.0b10 🧹🚙

Final beta layout polish before stable review.

- Move the lifetime trip summary (**trip count · logged km · travel time**) into the top of **Trip statistics**.
- Remove that summary from the gap between the top overview and the dashboard section list.
- Keep the summary labelled **Since import start** inside Trip statistics.
- Preserve the b9 overview order and compact summary expanders unchanged.
- No new sensors, backend storage, write-back or data-model changes.
- Preserve all 42 sensor unique IDs/entity IDs and the existing calendar entity; total integration entity count remains **43**.
- Sync manifest, desktop/mobile card versions and documentation to `2026.11.0b10`.
- Release flow remains `dev → beta → main`; stable promotion should follow successful real-HA validation of this final beta layout.

# HA-Fuelio 2026.11.0b9 🧭🚙

Overview order and odometer summary polish.

- Move **Tank & range** to the first position in the top overview.
- Convert **Odometer** into the same compact summary-expander model as the other overview groups.
- Keep **Current** odometer + **Month** distance visible directly in the collapsed Odometer header.
- Reveal monthly ODO detail, year distance and import-lifetime distance only when Odometer is expanded.
- Keep Fuel, Booked expenses and Estimated driving cost/km as compact summary expanders.
- No new sensors, backend storage, write-back or data-model changes.
- Preserve all 42 sensor unique IDs/entity IDs and the existing calendar entity; total integration entity count remains **43**.
- Sync manifest, desktop/mobile card versions and documentation to `2026.11.0b9`.
- Release flow remains `dev → beta → main`; real Home Assistant validation is required before stable promotion.

# HA-Fuelio 2026.11.0b8 🧩🚙

Compact overview summary expanders.

- Convert **Fuel**, **Booked expenses** and **Estimated driving cost/km** in the top overview into compact summary expanders.
- Keep the most useful values visible directly in each collapsed header row:
  - Fuel: latest reported consumption + running average.
  - Booked costs: current month + current year.
  - Estimated driving cost/km: current month + current year.
- Expanding a group reveals secondary detail rows while preserving the same calculations and data source.
- Keep **Odometer** as a normal always-visible overview card.
- Keep all main dashboard sections collapsed by default as introduced in b7.
- No new sensors, backend storage, write-back path or data-model changes.
- Preserve all 42 sensor unique IDs/entity IDs and the existing calendar entity; total integration entity count remains **43**.
- Sync manifest, desktop/mobile card versions and documentation to `2026.11.0b8`.
- Release flow remains `dev → beta → main`; real Home Assistant validation is required before stable promotion.

# HA-Fuelio 2026.11.0b7 📊🚙

Inline Trip statistics graphs and calmer dashboard defaults.

- Start all main desktop dashboard sections collapsed by default.
- Add a nested **Chart** expander inside **Trip statistics** that follows the same selected year/month/week/day period; no duplicate period selectors.
- Keep **TripDist vs ODO distance** as a clean two-line comparison without smoothing.
- Render **Trip count**, **Travel time** and **Average/trip** as actual-period bars with a rolling **3-period mean** line overlaid.
- The rolling window follows chart granularity automatically: year charts use months, month charts use ISO weeks, and week charts use days.
- Keep day as the terminal statistics level; no per-trip one-point graph is invented.
- Reuse the existing bounded ZIP-derived trip statistics and self-contained SVG renderer. No new sensors, storage, write-back or external chart dependency.
- Preserve all 42 sensor unique IDs/entity IDs and the existing calendar entity; total integration entity count remains **43**.
- Sync manifest, desktop/mobile card versions and documentation to `2026.11.0b7`.
- Release flow remains `dev → beta → main`; real Home Assistant validation is required before stable promotion.

# HA-Fuelio 2026.11.0b6 📈🚙

Trip-statistics drill-down charts.

- Add clickable charts to **Trip statistics** for year, month and week levels.
- **TripDist** and **ODO distance** share a two-series line chart so their divergence can be inspected over time without treating either as authoritative for the other.
- Add dedicated charts for trip count, total travel time and average distance per trip.
- Drill charts down exactly one level: year → months, month → ISO weeks, week → days.
- Keep day as the terminal statistics level; it deliberately has no one-point chart because per-trip day charts would require a different data model.
- Reuse the existing self-contained SVG chart modal and the b5 bounded ZIP-derived trip-statistics attributes. No new sensors, no new backend storage and no external chart dependency are introduced.
- Preserve all 42 sensor unique IDs/entity IDs and the existing calendar entity; total integration entity count remains **43**.
- Sync manifest, desktop/mobile card versions and documentation to `2026.11.0b6`.
- Release flow remains `dev → beta → main`; real Home Assistant validation is required before stable promotion.

# HA-Fuelio 2026.11.0b5 🚙📊

Hierarchical trip statistics plus calendar polish.

- Add a bounded **Trip statistics** drill-down in the desktop card with levels **Year → Month → Week → Day**.
- Only the selected statistics level is expanded; selectors are scoped to the chosen year/week.
- Show the same core metrics at every level: Fuelio `TripDist`, ODO-checkpoint distance, trip count, total travel time and average distance per trip.
- Keep `TripDist` and ODO as deliberately separate measurements; do not force them to match.
- Compute all trip statistics from the current Fuelio ZIP on each coordinator refresh. No HA-Fuelio history database, cache file or write-back path is introduced.
- Bound statistics to 40 years, 120 months, 160 ISO weeks and 400 trip days in Home Assistant attributes.
- Remove `TripCategory` from trip calendar projection/presentation; sanitized trip title and note remain available.
- Preserve all 42 sensor unique IDs/entity IDs and the existing calendar entity; total integration entity count remains **43**.
- Sync manifest, desktop/mobile card versions and documentation to `2026.11.0b5`.
- Release flow remains `dev → beta → main`; real Home Assistant validation is required before stable promotion.

# HA-Fuelio 2026.11.0b4 🚗📅

Richer read-only Fuelio calendar with journey timeline.

- Extend the existing Fuelio calendar with the latest **256 TripLog journeys** as timed Home Assistant events.
- Use Fuelio `StartDate`/`EndDate` for event time and `TripDist` for the displayed journey distance; do not derive trip distance from odometer differences.
- Treat `EndOdo` only as an odometer checkpoint. A zero/blank `StartOdo` is valid and is not treated as broken data.
- Show sanitized TripLog title/category/note when present, plus trip duration and ending odometer.
- Keep GPS coordinates, route geometry, start/end place names, internal IDs, vehicle identifiers and raw TripLog rows out of the calendar projection.
- Enrich current/future cost events with sanitized Fuelio cost title and `Notes` when available, while retaining category, amount and maintenance/expense classification.
- Keep separate bounds of **256 trip events + 256 cost events** to avoid unbounded HA state/memory growth.
- Keep templates, incomes and moving estimated-refuel forecasts excluded.
- Preserve the existing calendar entity and all 42 sensor unique IDs/entity IDs; total integration entity count remains **43**.
- Sync manifest, desktop/mobile card versions and documentation to `2026.11.0b4`.
- Release flow remains `dev → beta → main`; real Home Assistant validation is required before any stable promotion.

# HA-Fuelio 2026.11.0b3 📅🚙

Read-only Fuelio calendar.

- Add a `calendar` platform alongside the existing 42 sensors. The integration now exposes one read-only Fuelio calendar entity without adding sensor entities.
- Project non-template, non-income Fuelio `Costs` rows dated today or later into bounded all-day Home Assistant calendar events.
- Keep calendar data privacy-safe: only date, sanitized cost category, amount and coarse event kind are retained. Fuelio cost titles, notes, internal IDs, registration/VIN-like vehicle data and raw rows are not exposed.
- Mark categories containing the Fuelio category names `Underhåll`, `Service` or `Reparation` as maintenance events; other rows remain general expense events.
- Cap the in-memory calendar projection at 256 events.
- Deliberately exclude `isTemplate=1` rows until Fuelio template/realized-obligation semantics are validated.
- Deliberately exclude estimated next fuel-up from the calendar in b3 because that forecast can move as range and driving pace change.
- Reuse the existing five-minute local ZIP coordinator; no second poller, external calendar account or write-back path is introduced.
- Add synthetic parser privacy/regression coverage and release-tree checks for the calendar platform.
- Release flow remains `dev → beta → main`; real Home Assistant validation of the calendar entity is required before stable promotion.

# HA-Fuelio 2026.11.0b2 📱⛽

Dedicated mobile dashboard.

- Add a separate bundled `ha-fuelio-mobile-card.js` for phone dashboards while keeping the full desktop card independent.
- Mobile overview focuses on odometer, ZIP sync, estimated tank status/range, distance since fuel-up, consumption, current-month spending and cost/km.
- Replace the large tank metrics with a compact horizontal tank bar based on estimated litres versus Fuelio tank capacity.
- Show a clear **RESERV** state only when estimated remaining range is known and strictly below **75 km**; unknown/unavailable range never triggers a reserve warning.
- Keep range calibration in the collapsed **Mer information** section, including the existing automatic-clear behavior on the next primary-tank fill-up.
- Surface measured full→full consumption/trend in the details section when available.
- Serve the mobile card directly at `/fuelio/ha-fuelio-mobile-card.js`; no new sensors or backend data are required.
- Sensor count remains **42** and the desktop card retains its existing feature set.
- Add synthetic mobile-card regressions for reserve threshold, unavailable range, compact monthly data, entity resolution and range calibration.
- Release flow remains `dev → beta → main`; validate the mobile layout in real Home Assistant before stable promotion.

# HA-Fuelio 2026.11.0b1 🚙📊

Measured full-to-full fuel economy and safer automatic range forecasting.

- Add a pure `fuel_economy.py` engine that derives consumption from Fuelio full-tank anchors instead of trusting reported `l/100km` alone.
- Bank partial fills into the next full-tank window and calculate aggregate consumption as total fuel / total distance; short windows never get equal weight with long windows.
- Reject implausible windows and expose aggregate anomaly/exclusion counts. Fuelio `Missed` and `ExcludeDistance` flags invalidate affected measurement windows.
- Keep tanks separated and avoid mixing Fuelio fuel types inside a measured window.
- Expose measured-window count, weighted/recent/latest L/100 km, latest-five trend, confidence, anomaly count and exclusion count in the existing range-forecast attributes.
- Automatic range-basis precedence is now: persisted manual calibration → recent measured full-to-full basis → Fuelio latest-two reported consumption fallback.
- Manual current-tank calibration semantics from b17 are unchanged and still clear only when the latest actual primary-tank fill-up changes.
- No new Home Assistant entities; sensor count remains **42**. The source remains local Fuelio ZIP only and read-only.
- Add synthetic regression tests for full→partial→full banking, distance weighting, `Missed`/`ExcludeDistance`, implausible windows, confidence/trend and parser fallback behavior.
- Version calendar rolls to **2026.11.0b1**. Release flow remains `dev → beta → main`; real-HA validation is required before any stable promotion.

# HA-Fuelio 2026.10.0b17 🛠️

Range-calibration persistence and setup robustness.

- Replace the b16 calibration reset anchor based on **primary fill-up count** with an opaque marker for the **latest actual primary-tank fill-up**.
- Historical/backfilled Fuelio tank records no longer look like a new tanking and therefore no longer clear an active calibration.
- A genuinely new latest primary-tank fill-up still clears the manual range calibration automatically.
- Migrate existing b16 calibration state without forcing a reset when no newer fill-up occurred after calibration.
- Move Fuelio service registration from per-config-entry setup into integration-global `async_setup`.
- Keep the current ZIP parser and 42-sensor data model unchanged.
- Frontend remains HACS-managed at `/fuelio/ha-fuelio-card.js`.

# HA-Fuelio 2026.10.0b16 🎯

Current-tank range calibration.

- Add a **Calibrate** button to **Tank & range**.
- Enter the vehicle computer's current remaining range in kilometres; HA-Fuelio derives a temporary L/100 km basis so the theoretical range matches that value at the calibration moment.
- The calibrated consumption basis then continues to count range down normally as new odometer data arrives; the entered range is not frozen.
- Persist the override locally in Home Assistant across integration reloads/restarts. Nothing is written back to Fuelio or the source ZIP.
- Automatically discard the override on the next registered **primary-tank fill-up**, so new Fuelio fuel/distance information becomes authoritative again.
- Add an explicit **Restore automatic** action while manual calibration is active.
- Forecast attributes expose automatic vs manual consumption basis and calibration state for transparent UI/status.
- No new entities: sensor count remains **42**.
- Frontend remains HACS-managed at `/fuelio/ha-fuelio-card.js`.

# HA-Fuelio 2026.10.0b15 🧹

Permanent HACS-managed frontend delivery.

- Serve the bundled Lovelace card directly from the integration at `/fuelio/ha-fuelio-card.js` using Home Assistant's async static-path API with cache headers disabled.
- Remove the need to manually copy `ha-fuelio-card.js` into `/config/www` after every beta.
- Remove the need to bump a `?v=...` query string for every beta.
- One-time migration: replace the existing Lovelace resource URL with `/fuelio/ha-fuelio-card.js` (JavaScript module), then future beta updates are HACS-only.
- The legacy `/config/www/ha-fuelio-card.js` can be deleted after the resource has been switched and verified.
- Do not auto-load the card with `add_extra_js_url`; keep it as a normal Lovelace resource to avoid frontend custom-element load-order races in panel views.
- Sensor model remains unchanged at **42 entities**. The Service & maintenance fix from b14 is retained.

# HA-Fuelio 2026.10.0b14 🔧

Service & maintenance cost visibility fix.

- Replace the placeholder-only **Service & maintenance** section with real cost summaries from existing Fuelio category aggregates.
- Show maintenance/service/repair costs for:
  - the month selected in **Kostnader**
  - the year selected in **Annual overview**
  - the full imported period
- Match Fuelio category names containing `Underhåll`, `Service` or `Reparation`; unrelated categories such as the source category `Tjänster` are not included.
- Existing booked cost totals are unchanged; this release fixes presentation/visibility only.
- No new sensors or unique-ID/entity-ID changes. Sensor count remains **42**.
- Frontend version becomes **2026.10.0b14**.

Update the beta through HACS and restart Home Assistant. The Lovelace resource cache-bust should use `/local/ha-fuelio-card.js?v=2026.10.0b14` after the updated card file is in `/config/www`.

# HA-Fuelio v0.1.0-beta.13 🚙📈

Interactive drill-down charts for the desktop Fuelio dashboard.

- Make selected KPI and annual-report tiles clickable and open an internal modal without leaving the dashboard.
- Add a self-contained SVG chart engine; no Chart.js, ApexCharts, Browser Mod or other frontend dependency is required.
- Initial graph set uses existing bounded monthly/yearly aggregate attributes only:
  - booked fuel + non-fuel costs per month (stacked bars)
  - observed ODO distance per month
  - purchased litres per month
  - booked total SEK/ODO-km versus estimated total SEK/km
  - annual non-fuel expense categories
- Annual graphs follow the independent year selector. Current-period KPI graphs use the current calendar year.
- Native SVG titles provide hover values, with theme-aware HA colors, modal close button, backdrop close and Escape-key close.
- Missing monthly metrics stay unavailable; they are never silently plotted as zero.
- Backend data model and sensor count remain unchanged at **42**. Beta.13 is primarily a frontend interaction release on the beta.12/beta.11 backend.

Upgrade through HACS, restart Home Assistant, copy the updated `ha-fuelio-card.js` to `/config/www`, update the existing resource to `/local/ha-fuelio-card.js?v=0.1.0-beta.13`, and hard-refresh.

# HA-Fuelio v0.1.0-beta.12 🚙📊

Annual reporting on top of the beta.11 parser fix.

- Add a full-width **Annual overview** section with an independent year selector (up to the existing 40-year bounded history).
- Annual headline metrics: observed ODO distance, logged trip count, mean logged trip length, purchased litres, fill-up count and average reported L/100 km.
- Annual cost summary: booked fuel, non-fuel and total spending; booked total SEK/ODO-km; estimated consumed-fuel cost and estimated total SEK/km.
- Annual fuel/efficiency summary: weighted actual average fuel price (booked fuel spend ÷ purchased litres), yearly min/max positive unit price, yearly min/max reported consumption and number of valid consumption observations.
- Show **every aggregated expense category for the selected year** (bounded by the existing category privacy/size rules).
- Enrich the existing `years` attribute objects on `Monthly cost breakdown`; no new entities are created. Sensor count remains **42** and existing unique IDs/entity IDs stay unchanged.
- Keep the beta.11 cost-only month-end normalization for Fuelio's invalid recurring dates.
- Frontend version becomes **0.1.0-beta.12**.

Upgrade through HACS, restart Home Assistant, re-copy `/config/custom_components/fuelio/www/ha-fuelio-card.js` to `/config/www/ha-fuelio-card.js`, update the existing Lovelace resource to `/local/ha-fuelio-card.js?v=0.1.0-beta.12`, and hard-refresh.

# HA-Fuelio v0.1.0-beta.11 🚙

Targeted parser fix for Fuelio's recurring month-end cost export bug.

- Accept impossible **month-end dates only for cost rows** when Fuelio materializes a recurring expense on day 29-31 in a shorter month, e.g. `2026-09-31`.
- Clamp only that narrow case to the month's real last day (`2026-09-31 → 2026-09-30`).
- Keep tanking, trip and all other dates strictly validated; malformed non-month-end dates still fail instead of being silently accepted.
- This fixes the real backup observed on 2026-10-01 where an ordinary non-template cost row was exported as `2026-09-31 05:00`.
- No sensor IDs, calculations, card layout or frontend file change. Sensor count remains **42** and HA-Fuelio Card remains **0.1.0-beta.10**.

Upgrade the integration through HACS to beta.11 and restart Home Assistant. No Lovelace resource/cache-bust change is required for this backend-only fix.

# HA-Fuelio v0.1.0-beta.10 🚙

Desktop-first UI refresh built on the validated beta.9 backend.

- Redesign the Lovelace card for a dedicated wide dashboard: six top KPIs, denser desktop grids, stronger visual hierarchy, a wider costs/fuel composition and compact secondary sections.
- Promote **Tank & range** to a spotlight panel with estimated fuel remaining, theoretical range, distance since latest fill-up, predicted next fill-up and a visual estimated tank-level bar.
- Show **ZIP updated** prominently in the header. The timestamp comes from the existing `last_app_sync` sensor, i.e. the local ZIP modification time preserved from Drive by the tested rclone workflow.
- Keep the same 42 backend sensors and beta.9 calculation model; this release is primarily frontend presentation plus a redraw fix.
- Add the six beta.9 range/sync sensors to the card's change signature so a new ZIP timestamp/range value redraws the card even when unrelated Fuelio values do not change.
- Collapse the records section by default to reduce vertical scrolling on desktop; detailed cost/fuel sections remain open.
- The complete beta.9 card remains preserved by the immutable release/tag `v0.1.0-beta.9`, so no loose backup JS file is added to the repository.

Upgrade through HACS, restart Home Assistant, re-copy `/config/custom_components/fuelio/www/ha-fuelio-card.js` to `/config/www/ha-fuelio-card.js`, update the existing resource to `/local/ha-fuelio-card.js?v=0.1.0-beta.10`, and hard-refresh. A separate compact/mobile card can be designed later.

# HA-Fuelio v0.1.0-beta.9 🚙

Fuel-tank range forecasting and Fuelio source-sync visibility.

- Add **six read-only sensors** (42 total): distance since last fuel-up, estimated fuel remaining, estimated range remaining, estimated days to next fuel-up, estimated next fuel-up date, and last Fuelio app sync.
- Range estimation uses the primary tank's exported capacity and the latest full fill-up as a calibration point. Later partial fill-ups add their actual litres; estimated consumption since calibration is subtracted using the rolling mean of up to the latest two valid reported L/100 km values. Remaining fuel is physically bounded to 0..tank capacity. A partial fill therefore does not make the estimate unavailable.
- The next-fuel-up prediction divides theoretical remaining range by aggregate logged driving pace over up to the latest 30 calendar days. The predicted date represents **theoretical empty tank**, not a claim about when the driver will choose to refuel. Forecast attributes expose consumption basis/sample count, calibration date, partial-fill count, 30-day daily-distance basis and a normal/limited confidence label.
- The new source-sync sensor uses the local ZIP file modification time. In the tested rclone Google Drive workflow, rclone preserves Drive's modification time, so this surfaces when Fuelio/Drive last changed the sync ZIP. It is intentionally separate from Home Assistant's own polling/read time.
- The Lovelace card adds a current **Tank & range** overview panel and shows latest Fuelio sync in Versionsinformation. The old notice claiming range was not modelled is removed. Frontend version is beta.9.
- Existing 36 entity unique IDs remain unchanged; beta.9 only adds new keys. Raw trips, coordinates, VIN/plate, notes and source rows remain private and are not exposed.
- Google Drive downloading remains an external transport concern (for example the tested Rclone Backup add-on); HA-Fuelio itself still reads a local ZIP and stays read-only.

Upgrade through HACS, restart Home Assistant, re-copy `/config/custom_components/fuelio/www/ha-fuelio-card.js` to `/config/www/ha-fuelio-card.js`, update the existing JavaScript resource to `/local/ha-fuelio-card.js?v=0.1.0-beta.9`, and hard-refresh. Real-HA validation is required before any promotion to `main`.

# HA-Fuelio v0.1.0-beta.8 🚙

Experimental time-aware consumed-fuel costing and vehicle overview. Keep beta.7 as a known reference until real Home Assistant validation.

- New responsive four-group current-period overview: latest odometer plus current month/year/since-import ODO distance; latest reported fuel consumption, litres bought this month/year, last up-to-two reported consumption mean; actual booked spending this month/year; estimated driving total SEK/km this month/year. Historical month selection changes only the Costs content, not the current overview.
- Selected historic month now displays observed ODO distance, logged TripLog trip count, and mean LOGGED trip length. These two kilometre measures are explicitly different.
- Monthly, yearly and lifetime aggregate attributes add estimated consumed-fuel spending and estimated consumed-fuel/total SEK per ODO-km. For each observed odometer interval, use at most the two most recent positive reported L/100km readings and latest valid price known at its START; the next refuel changes only subsequent intervals. Estimated total = estimated fuel + actual non-fuel expense, never add booked fuel twice. Incomplete fuel-price/consumption coverage yields unavailable period estimates; single-reading fallback is marked limited. Daily timestamp precision and tank mixing remain limitations.
- Existing six booked cash-outlay-per-ODO-km sensors remain separate and keep their established unique IDs/entity IDs (including old `logged_km` slugs). No new sensors: still **36 total**. Existing CostCategories, ZIP path and read-only privacy constraints remain.
- 33 synthetic Python tests and four frontend smoke/regression tests pass on dev, including late refuel does not reprice earlier travel, missing data, one consumption reading and month selector not changing overview. Real HA and Fuelio value comparison required before stable main promotion. Google Drive automatic download is not included.

Upgrade integration in HACS, restart HA, re-copy `/config/custom_components/fuelio/www/ha-fuelio-card.js` to `/config/www/ha-fuelio-card.js`, update the EXISTING single JavaScript resource to `/local/ha-fuelio-card.js?v=0.1.0-beta.8`, and hard-refresh. Keep current YAML, config entry and private ZIP. Check that frontend version says beta.8 and exactly 36 sensors remain. The new estimated cost/km can show — if historical measurements are insufficient; this is intentional, not zero.

# HA-Fuelio v0.1.0-beta.7 🚙

Odometer semantics and overview fix for real-HA testing.

- Calculate month/year/import-lifetime fuel and actual-total SEK/km using ODO checkpoints from Fuelio fuel-ups and OBD trip StartOdo/EndOdo, not sum of TripDist. For each calendar period, last observation before period start is the baseline; end is latest observation inside period. If no pre-period checkpoint exists, start at the earliest in-period reading and mark `odo_coverage: partial_start`. No usable readings or rollback yields `unknown` rather than invented distance.
- Monthly breakdown attributes include `km` (observed odometer difference), `litres`, `logged_trip_km` (sanity check), and checkpoint dates/coverage. Category amounts and bounded aggregates remain. 36 unique sensor keys and IDs retained, including legacy `_logged_km` entity IDs; human-facing names clarify odometer basis.
- Header shows odometer plus current-month ODO delta, current-month litres, current-month actual expenditure and total SEK/ODO-km. It never follows the historical cost month selector. Fuel consumption/price remain in the Fuel section. Move whole-export estimated trip cost to its own explicitly non-actual summary.
- No automatic Drive download or stable main promotion. A nearest checkpoint can lie before the calendar boundary; these are observed-distance period allocations, not exact midnight readings. Validate against private Fuelio and real HA.

Upgrade HACS, reboot HA, re-copy card JS into `/config/www/ha-fuelio-card.js`, change the EXISTING sole module resource to `/local/ha-fuelio-card.js?v=0.1.0-beta.7` and hard refresh. Keep YAML and local ZIP unchanged. Verify 36 sensors and test monthly transitions.
# HA-Fuelio v0.1.0-beta.6 🚙

Experimental period analytics release based on the beta.5 dashboard tests.

- Add six read-only SEK/km sensors: fuel and all actual spending for current calendar month, calendar year, and full imported history. Denominator is **logged trip km in the SAME period**, not total vehicle mileage. No logged km yields `unknown`, not zero. A new valid ZIP updates ratios on the existing five-minute polling cycle.
- Add current month and year fill-up count sensors; lifetime fill-up count remains existing stable sensor. Future-dated fill-ups are not counted.
- Parse optional `CostCategories` (`CostTypeID` → `Name`) and join actual `Costs.CostTypeID`; exclude templates, incomes and future expenses. Unknown category ID or missing section is `Okategoriserat`. Expose only aggregated name/amount, never private cost titles, notes, category internal IDs or raw rows.
- Monthly cost breakdown attributes now include logged km, fuel-ups, both cost/km ratios and category totals; add year aggregates and lifetime category totals. Attribute summaries are capped (120 months, 40 years, 20 category rows per group), with excess names combined under `Other categories`.
- The card shows per-category expenses, six period cost/km tiles, and a separate month/year/lifetime fill-up section; no false whole-vehicle cost/km claim. Four-column mode now requires >=850px.
- Preserve the existing 28 sensor IDs and unique IDs; eight new sensors bring the integration to **36 sensors**. Existing ZIP paths remain unchanged.

Upgrade the integration in HACS and restart. Re-copy `custom_components/fuelio/www/ha-fuelio-card.js` to `/config/www/ha-fuelio-card.js`, update the SINGLE Lovelace resource to `/local/ha-fuelio-card.js?v=0.1.0-beta.6`, then hard refresh. Keep existing card YAML. Compare categories and cost/km with your private Fuelio backup in real HA before stable promotion. `main` remains unchanged.
