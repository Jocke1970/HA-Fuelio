# HA-Fuelio 🚙

Fuelio-source-read-only Home Assistant integration for [Fuelio](https://www.fuel.io/). **Latest test release: `2026.11.3b5` on `beta`; stable remains `2026.11.2` on `main`.** Development is gated `dev → beta → main`; `2026.11.2` is the current stable release after live Home Assistant validation of the OBD fuel-left calibration, bilingual UI, optional calendar configuration and existing dashboard/data flow.

## Features and data contract (2026.11.3b5)

- Imports a **local**, single-vehicle, metric Fuelio sync CSV ZIP (`Vehicle`, `Log`, optional `CostCategories`, `Costs`, `TripLog`) about every five minutes. Read-only: never writes to the ZIP or Fuelio. Built-in Google Drive retrieval is **not implemented**; an external rclone workflow can keep this local ZIP current.
- **Bilingual integration UI (English/Swedish):** config flow, options, sensor friendly names, services and both bundled dashboard cards follow the Home Assistant/browser language. Backend aggregate data stays language-neutral where practical.
- **Optional calendar platform:** the read-only Fuelio calendar is enabled by default for backward compatibility, but can be disabled under the integration's **Configure** options. Changing the option reloads the config entry; sensor entities remain available.
- **OBD fuel-left calibration:** the current tank can be anchored to a vehicle/OBD-reported remaining-fuel value. Optional range and OBD average-consumption inputs are consistency checks; if both are supplied they must agree within a bounded tolerance. After calibration, HA-Fuelio counts forward using driven ODO distance and recorded partial fills, then clears the manual anchor on the next primary full fill-up. The older range-only calibration remains available as a fallback.
- **42 sensors**: the existing 36 summaries/analytics sensors plus distance since last fuel-up, estimated fuel remaining, estimated range remaining, estimated days/date to next fuel-up, and last Fuelio app sync. Existing sensor unique IDs and existing HA entity IDs are preserved, including historical entity slugs ending `_logged_km` whose *display names* now correctly describe odometer kilometres. Newly created sensor entity-ID prefixes can differ from older registered entities.
- The `Monthly cost breakdown` sensor exposes bounded aggregate attributes: `months` (up to 120), `years` (up to 40), `categories_all`, `lifetime_odometer_km`, `estimated_lifetime`, `latest_two_consumption`, `latest_two_consumption_count` and coverage metadata. Period rows include booked fuel/non-fuel costs, purchased litres, observed ODO distance, logged trip km, trip count, mean logged trip length, fill-up count, categories and separately labelled booked/estimated cost metrics. Year rows additionally include average reported consumption/sample count, weighted actual average fuel price and yearly min/max price/consumption values. All-month history may be truncated for HA attribute size; lifetime aggregates are separate.
- Fuelio can export a realized recurring cost on an impossible month-end date (for example `2026-09-31`). The parser clamps only cost-row day 29-31 overflow to the real last day of that month; other date parsing remains strict.
- Costs are categorized by `Costs.CostTypeID` joined to `CostCategories.CostTypeID`; only the category's display name and aggregate amount are exposed. Missing mappings become `Uncategorized`, with category-list overflow grouped into `Other categories`. **`isTemplate=1` and `isIncome=1` entries are excluded**, as are future-dated expenses from actual spending. A genuinely paid item manually marked as a template is therefore *also excluded*; see [validation and open questions](BETA8_VALIDATION.md). Do not assume every recurring entry is a realized payment.
- Eight fuel records: lowest/highest positive recorded unit prices and individually reported L/100 km, for the current calendar year and imported history, with `recorded_on` attributes. A missing report remains unknown; the latest-two-reading average is an explicitly separate estimate.
- **Measured fuel economy:** independent full→full L/100 km windows from Fuelio `Full`, litres and odometer values. Partial fills are banked until the next full tank, aggregates are distance/fuel weighted, and `Missed`, `ExcludeDistance`, implausible windows, tank changes and fuel-type breaks are excluded. The range forecast exposes measured-window count, weighted/recent/latest consumption, latest-five trend, anomaly/exclusion counts and confidence. Automatic range basis precedence is manual calibration → recent measured full→full → Fuelio latest-two reported consumption.
- Clickable KPI/annual tiles open self-contained SVG chart modals for monthly booked costs, ODO distance, purchased litres, booked-vs-estimated cost/km and annual expense-category distribution. Graphs use the same bounded aggregate attributes already exposed by the integration; missing values are not converted to zero.
- **Service & maintenance** surfaces existing booked Fuelio categories matching `Underhåll`, `Service` or `Reparation` for the selected month, selected annual-report year and import lifetime. This is presentation of already-counted costs, not a separate accounting model.
- Desktop-first dashboard with an independent annual-report selector and internal SVG drill-down charts. The bundled read-only Lovelace card is served directly by the integration at `/fuelio/ha-fuelio-card.js`: current-period overview with tank/range forecasting, historical month selector, categories, fuel statistics and fill-ups, records and estimated-versus-booked cost sections. Card icon: `custom_components/fuelio/brand/icon.png`.
- **Top status chips** now render as a left-aligned wrapped status row beneath the title. Availability gets a subtle positive tint, ZIP sync remains the primary neutral status, and latest trip is visually quieter so wrapped layouts stay balanced.
- **Frozen desktop accordion (validated in HA, `2026.11.3b5`)**: Eleven sections form one responsive two-column grid below the six KPIs and full-width Tank & range panel. Closed tiles show only icon and centered title; opening one tile shows its details across both columns, temporarily hides the original row partner, and closes any other open section. Version information is the final full-width tile; narrow layouts fall back to one column. This is the accepted layout, not an outstanding design proposal.
- **Separate mobile dashboard** at `/fuelio/ha-fuelio-mobile-card.js`: compact odometer/sync header, horizontal estimated tank bar, range and consumption, current-month cost summary, and a collapsed details/calibration section. It shows **RESERV** only when the estimated range is known and below 75 km. The mobile card uses the same 42 entities and adds no backend sensors.
- **Read-only Fuelio calendar**: one Home Assistant calendar entity combines current/future non-template, non-income `Costs` with the latest Fuelio `TripLog` journeys. Costs are all-day events and may include sanitized user-entered title/note; trips are timed events using `StartDate`/`EndDate`, `TripDist` for logged/GPS distance, and `EndOdo` only as an odometer checkpoint. GPS coordinates, route/place fields, internal IDs, vehicle identifiers and raw rows are never projected. Cost and trip projections are bounded independently at 256 events each. Estimated fuel-up forecasts remain excluded.
- **Trip statistics**: bounded ZIP-derived drill-down for year → month → ISO week → day. The main dashboard sections now start collapsed. Inside Trip statistics, a nested **Chart** expander follows the same selected level/period. TripDist vs ODO remains a clean two-line comparison; trip count, travel time and average trip length use actual-period bars plus a rolling 3-period mean line. Charts drill down one level (year→months, month→weeks, week→days). Day is terminal. No additional entity or local history database is created. The lifetime trip summary (trip count, logged km and travel time) now lives inside Trip statistics instead of between the overview and dashboard sections.

### Distances and cost definitions

**Observed ODO distance:** latest applicable tank-up `Odo (km)` or OBD trip `StartOdo`/`EndOdo` checkpoint minus the preceding baseline. For a month/year, use the latest observation *before* its first day and the latest observation *inside* it. If no previous checkpoint exists, measure only from the first in-period observation and label `partial_start`/`Delperiod`. This is not an exact midnight reading. A missing/invalid distance produces unknown, not an invented rate. `logged_trip_km` is the sum of `TripDist` and is used for trip statistics/cross-checks; **do not add it to or substitute it for the ODO delta**. ODO and logged-trip distance may differ when checkpoints straddle month boundaries or travel was not logged.

**Booked expenses / observed ODO km:** (fuel paid during period + actual non-fuel expenses paid during period) / observed ODO km. Separate existing fuel-only and combined SEK/km sensors cover current month, year and import lifetime. These measure *cash outlay* in the chosen period, not fuel consumed in that period.

**Estimated consumed-fuel driving cost:** for each observed ODO interval, derive an estimated SEK/km using the up-to-two most recent positive consumption readings and latest valid fuel unit price available at the **interval's start**, then multiply by its ODO delta. Later refuelling updates *future* intervals only. Sum interval estimates for period fuel cost; add actual booked **non-fuel** expenses for estimated total driving cost, without adding purchased fuel a second time. Divide by observed period ODO km for estimated SEK/km. Missing earlier rates or invalid coverage suppress the full-period estimate; one consumption reading is labelled limited. Fuel purchased ≠ fuel consumed, and day-only timestamps, tank mixing and unavailable per-trip actual consumption limit precision.

**Historical month selector:** changes the selected month in the Costs section, including its observed ODO delta, logged trip count, and mean `TripDist` per logged trip. The six top KPIs and current-period Mätarställning, Drivmedel, Bokförda utgifter and Körkostnad accordion details always reflect the **current** month/year instead. Original `TripCost` estimated travel expense is a separate whole-import figure, never an actual payment or selected-month expense.

**Tank/range forecast:** the latest primary-tank full fill-up is the calibration point. Later partial fills add recorded litres; estimated driving consumption prefers the recent measured full→full basis when available, otherwise it uses the latest up-to-two positive Fuelio-reported L/100 km values. Remaining litres are bounded to tank capacity, remaining range is theoretical, and next-fuel-up date/days use up to 30 calendar days of logged driving pace. The dashboard can apply an HA-local **current-tank range calibration** from the vehicle computer: entered remaining km are converted to a temporary consumption basis, persisted across HA reloads, and automatically cleared only when the latest actual primary-tank fill-up changes. Historical/backfilled tank records do not clear it. This override never writes to Fuelio or the ZIP. The sync timestamp is the local ZIP mtime; in the tested rclone workflow it matches Drive's preserved modification time.

For detailed fields see [analytics schema](docs/analytics-schema.md), [calendar model](docs/calendar.md), [ODO algorithm](ODOMETER_ALGORITHM.md) and [beta.8 test status](BETA8_VALIDATION.md).

### Integration options

Open **Settings → Devices & services → Fuelio → Configure** to enable or disable the optional Fuelio calendar. Existing installations default to **enabled**, preserving the previous calendar behavior. Disabling the calendar removes only the calendar platform after reload; sensor and dashboard data remain unchanged.

## Install or upgrade

1. Add HACS custom repository `https://github.com/Jocke1970/HA-Fuelio` as an **Integration**. Install the latest stable release, or explicitly select the `2026.11.3b5` prerelease to test the frozen layout. HACS installs GitHub tags/releases, **not** arbitrary `beta` branch commits. Restart Home Assistant after installing or updating.
2. Keep your private ZIP at `fuelio/vehicle-1-sync.csv.zip` relative to the actual HA configuration root. Examples: `/config/fuelio/vehicle-1-sync.csv.zip` or `/homeassistant/fuelio/vehicle-1-sync.csv.zip`; **not** a nested `config/config` directory. Do not put the ZIP in GitHub or paste its private records into logs/issues.
3. **Do not remove/re-add the config entry or rename existing entities.** The old and new entity-ID prefixes can coexist; the card maps sensors through the HA entity/device registry.
4. **One-time migration for installations from b14 or older:** under dashboard **Resources**, replace the existing Fuelio JavaScript-module URL with `/fuelio/ha-fuelio-card.js`. Do not add a duplicate resource. After this migration, future Fuelio beta updates require no `/config/www` copy and no cache-bust query string.
5. Update future releases through HACS and restart/reload Home Assistant as required. The integration serves the card directly from its installed HACS files with cache headers disabled. If the footer still shows an older version after updating, reload the HA dashboard/browser, then inspect the installed integration's bundled frontend version before assuming HACS installed the wrong release.
6. Manual Lovelace card YAML for the existing tested installation:

```yaml
type: custom:ha-fuelio-card
entity: sensor.externa_sensorer_fuelio_vehicle_monthly_cost_breakdown
title: Fuelio · Vehicle overview

```

Mobile card on a mobile dashboard:

```yaml
type: custom:ha-fuelio-mobile-card
entity: sensor.externa_sensorer_fuelio_vehicle_monthly_cost_breakdown
title: Caddy
```

The mobile card also requires `/fuelio/ha-fuelio-mobile-card.js` as a separate **JavaScript Module** under dashboard Resources. Use your **actual** monthly-breakdown entity ID on other installations; do not assume a specific sensor prefix. Both cards stay local/read-only toward Fuelio; the range-calibration controls call only HA-Fuelio's local Home Assistant services and never write to Fuelio or the ZIP. Wider desktop layouts depend on the parent dashboard's available card width; a narrow column cannot be overridden safely from inside the card.

After `/fuelio/ha-fuelio-card.js` has been verified, the old manual copy `/config/www/ha-fuelio-card.js` may be deleted. It is no longer part of the supported update path.

## Privacy and limitations

Backups may contain registration, VIN, GPS tracks and private notes. No raw backup, identifiable fixtures, coordinates, trip records, notes or secrets should enter this public repository. HA-Fuelio sensors expose aggregates; the local read-only calendar may additionally expose sanitized user-entered cost/trip title, note and category text. GPS coordinates, route/place fields, registration/VIN-like vehicle data and raw source rows remain excluded. Previously registered entity IDs may still embed user-chosen identifying text; HA-Fuelio does not rename them automatically. Backup imports do not backfill HA Recorder.

Not implemented: built-in Google Drive/Dropbox transport, service schedules/reminders, actual per-trip consumption, multiple vehicles in one ZIP, or nonmetric exports. Currency is labelled SEK for the configured profile, not independently verified from the export. Future expenses and refuellings are not booked as current spending.

## Testing and release policy

The `2026.11.3b5` dashboard layout has been visually accepted in real Home Assistant and is frozen pending a deliberate new design decision. The current beta has passed repository CI, including parser, frontend and translation regressions. This does **not** by itself approve a stable release; promote to `main` only after explicit stable-release review. Historical beta validation remains in linked documents.

Known semantic caveats remain documented: ODO and TripDist are intentionally separate measurements, templates are excluded from booked costs, and range estimates depend on available Fuelio history. The historical Jinja-Ninja warning was a **bug in that external report template**. See [beta.8 validation](BETA8_VALIDATION.md) for the archived validation details.

```bash
python -m unittest discover -s tests -v
node --check custom_components/fuelio/www/ha-fuelio-card.js
node --check custom_components/fuelio/www/ha-fuelio-mobile-card.js
node tests/test_frontend.mjs
node tests/test_frontend_real_ids.mjs
node tests/test_cost_frontend.mjs
node tests/test_estimate_frontend.mjs
node tests/test_mobile_frontend.mjs
node tests/test_i18n_frontend.mjs
```

**Release gate:** changes go to `dev` first, then `beta` for real-HA validation. For HACS prereleases, confirm the actual GitHub prerelease exists and its tag points to the tested commit (a branch version bump alone is insufficient). The root README, developer docs, both bundled card versions, manifest and first release-notes heading must agree with the targeted version. For documentation-only updates, do not retag an existing release. Before stable promotion, align versions and documentation with the intended stable version. After the `beta → main` merge, the normal `main` test workflow must pass; only then may the stable-release workflow tag and publish that exact tested `main` commit. A stale CI result is rejected if `main` has moved meanwhile. Do not promote to `main` based solely on automated tests.

## Contributors

- **Joachim Eriksson** — project owner, product direction, real Home Assistant validation and release decisions.
- **ChatGPT (OpenAI)** — implementation support, code review, test design, documentation and release-workflow assistance.

