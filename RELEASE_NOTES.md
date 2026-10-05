# HA-Fuelio v0.1.0-beta.14 🔧

Service & maintenance cost visibility fix.

- Replace the placeholder-only **Service & underhåll** section with real cost summaries from existing Fuelio category aggregates.
- Show maintenance/service/repair costs for:
  - the month selected in **Kostnader**
  - the year selected in **Årsöversikt**
  - the full imported period
- Match Fuelio category names containing **Underhåll**, **Service** or **Reparation**; unrelated categories such as `Tjänster` are not included.
- Existing booked cost totals are unchanged; this release fixes presentation/visibility only.
- No new sensors or unique-ID/entity-ID changes. Sensor count remains **42**.
- Frontend version becomes **0.1.0-beta.14**.

Update the beta through HACS and restart Home Assistant. The Lovelace resource cache-bust should use `/local/ha-fuelio-card.js?v=0.1.0-beta.14` after the updated card file is in `/config/www`.

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

- Add a full-width **Årsöversikt** section with an independent year selector (up to the existing 40-year bounded history).
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
- Promote **Tank & räckvidd** to a spotlight panel with estimated fuel remaining, theoretical range, distance since latest fill-up, predicted next fill-up and a visual estimated tank-level bar.
- Show **ZIP uppdaterad** prominently in the header. The timestamp comes from the existing `last_app_sync` sensor, i.e. the local ZIP modification time preserved from Drive by the tested rclone workflow.
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
- The Lovelace card adds a current **Tank & räckvidd** overview panel and shows latest Fuelio sync in Versionsinformation. The old notice claiming range was not modelled is removed. Frontend version is beta.9.
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
- Monthly cost breakdown attributes now include logged km, fuel-ups, both cost/km ratios and category totals; add year aggregates and lifetime category totals. Attribute summaries are capped (120 months, 40 years, 20 category rows per group), with excess names combined under `Övriga kategorier`.
- The card shows per-category expenses, six period cost/km tiles, and a separate month/year/lifetime fill-up section; no false whole-vehicle cost/km claim. Four-column mode now requires >=850px.
- Preserve the existing 28 sensor IDs and unique IDs; eight new sensors bring the integration to **36 sensors**. Existing ZIP paths remain unchanged.

Upgrade the integration in HACS and restart. Re-copy `custom_components/fuelio/www/ha-fuelio-card.js` to `/config/www/ha-fuelio-card.js`, update the SINGLE Lovelace resource to `/local/ha-fuelio-card.js?v=0.1.0-beta.6`, then hard refresh. Keep existing card YAML. Compare categories and cost/km with your private Fuelio backup in real HA before stable promotion. `main` remains unchanged.
