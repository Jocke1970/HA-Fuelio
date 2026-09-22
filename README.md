# HA-Fuelio 🚙

Read-only Home Assistant integration for [Fuelio](https://www.fuel.io/). **Latest published test release: `v0.1.0-beta.8`**. Development is gated `dev → beta → main`: beta.8 has been tested in a real Home Assistant installation, but its calculations are **not yet fully validated** against source records. Do not promote to `main` until remaining checks are resolved. Drivvo is only a comparison reference, never a data source for HA-Fuelio.

## Features and data contract (beta.8)

- Imports a **local**, single-vehicle, metric Fuelio sync CSV ZIP (`Vehicle`, `Log`, optional `CostCategories`, `Costs`, `TripLog`) about every five minutes. Read-only: never writes to the ZIP or Fuelio. Automatic Google Drive retrieval is **not implemented**.
- **36 sensors**: 19 original summaries, eight dated price/consumption extrema, one monthly cost breakdown, and eight period-analytics sensors. Existing sensor unique IDs and existing HA entity IDs are preserved, including historical entity slugs ending `_logged_km` whose *display names* now correctly describe odometer kilometres. Newly created sensor entity-ID prefixes can differ from older registered entities.
- The `Monthly cost breakdown` sensor exposes bounded aggregate attributes: `months` (up to 120), `years` (up to 40), `categories_all`, `lifetime_odometer_km`, `estimated_lifetime`, `latest_two_consumption`, `latest_two_consumption_count` and coverage metadata. Period rows include booked fuel/non-fuel costs, purchased litres, observed ODO distance, logged trip km, trip count, mean logged trip length, fill-up count, categories and separately labelled booked/estimated cost metrics. All-month history may be truncated for HA attribute size; lifetime aggregates are separate.
- Costs are categorized by `Costs.CostTypeID` joined to `CostCategories.CostTypeID`; only the category's display name and aggregate amount are exposed. Missing mappings become `Okategoriserat`, with category-list overflow grouped into `Övriga kategorier`. **`isTemplate=1` and `isIncome=1` entries are excluded**, as are future-dated expenses from actual spending. A genuinely paid item manually marked as a template is therefore *also excluded*; see [validation and open questions](BETA8_VALIDATION.md). Do not assume every recurring entry is a realized payment.
- Eight fuel records: lowest/highest positive recorded unit prices and individually reported L/100 km, for the current calendar year and imported history, with `recorded_on` attributes. A missing report remains unknown; the latest-two-reading average is an explicitly separate estimate.
- Standalone read-only Lovelace card at `custom_components/fuelio/www/ha-fuelio-card.js`: current-period four-panel overview, historical month selector, categories, fuel statistics and fill-ups, records and estimated-versus-booked cost sections. Card icon: `custom_components/fuelio/brand/icon.png`.

### Distances and cost definitions

**Observed ODO distance:** latest applicable tank-up `Odo (km)` or OBD trip `StartOdo`/`EndOdo` checkpoint minus the preceding baseline. For a month/year, use the latest observation *before* its first day and the latest observation *inside* it. If no previous checkpoint exists, measure only from the first in-period observation and label `partial_start`/`Delperiod`. This is not an exact midnight reading. A missing/invalid distance produces unknown, not an invented rate. `logged_trip_km` is the sum of `TripDist` and is used for trip statistics/cross-checks; **do not add it to or substitute it for the ODO delta**. ODO and logged-trip distance may differ when checkpoints straddle month boundaries or travel was not logged.

**Booked expenses / observed ODO km:** (fuel paid during period + actual non-fuel expenses paid during period) / observed ODO km. Separate existing fuel-only and combined SEK/km sensors cover current month, year and import lifetime. These measure *cash outlay* in the chosen period, not fuel consumed in that period.

**Estimated consumed-fuel driving cost:** for each observed ODO interval, derive an estimated SEK/km using the up-to-two most recent positive consumption readings and latest valid fuel unit price available at the **interval's start**, then multiply by its ODO delta. Later refuelling updates *future* intervals only. Sum interval estimates for period fuel cost; add actual booked **non-fuel** expenses for estimated total driving cost, without adding purchased fuel a second time. Divide by observed period ODO km for estimated SEK/km. Missing earlier rates or invalid coverage suppress the full-period estimate; one consumption reading is labelled limited. Fuel purchased ≠ fuel consumed, and day-only timestamps, tank mixing and unavailable per-trip actual consumption limit precision.

**Historical month selector:** changes the selected month in the Costs section, including its observed ODO delta, logged trip count, and mean `TripDist` per logged trip. The four overview panels always show the **current** calendar month/year instead. Original `TripCost` estimated travel expense is a separate whole-import figure, never an actual payment or selected-month expense.

For detailed fields see [analytics schema](docs/analytics-schema.md), [ODO algorithm](ODOMETER_ALGORITHM.md) and [beta.8 test status](BETA8_VALIDATION.md).

## Install or upgrade

1. Add HACS custom repository `https://github.com/Jocke1970/HA-Fuelio` as an **Integration** and install the latest *published* prerelease. Avoid the broken beta.1 tag. Update beta.8 through HACS and restart Home Assistant.
2. Keep your private ZIP at `fuelio/vehicle-1-sync.csv.zip` relative to the actual HA configuration root. Examples: `/config/fuelio/vehicle-1-sync.csv.zip` or `/homeassistant/fuelio/vehicle-1-sync.csv.zip`; **not** a nested `config/config` directory. Do not put the ZIP in GitHub or paste its private records into logs/issues.
3. **Do not remove/re-add the config entry or rename existing entities.** The old and new entity-ID prefixes can coexist; the card maps sensors through the HA entity/device registry.
4. Reinstall the frontend file after each integration upgrade:

```bash
mkdir -p /config/www && \
cp -f /config/custom_components/fuelio/www/ha-fuelio-card.js /config/www/ha-fuelio-card.js && \
ls -lh /config/www/ha-fuelio-card.js
```

5. Under dashboard **Resources**, update the **existing single** JavaScript-module entry to `/local/ha-fuelio-card.js?v=0.1.0-beta.8` (do not add a duplicate), then hard-refresh the browser. If `/config/www` was just created, restart HA to expose `/local`.
6. Manual Lovelace card YAML for the existing tested installation:

```yaml
type: custom:ha-fuelio-card
entity: sensor.externa_sensorer_fuelio_vehicle_monthly_cost_breakdown
title: Fuelio · Bilöversikt
```

Use your **actual** monthly-breakdown entity ID on other installations; do not assume it starts with `sensor.mmk912_`. The card does not call HA services or make remote requests. Wider desktop layouts depend on the parent dashboard's available card width; a narrow column cannot be overridden safely from inside the card.

## Privacy and limitations

Backups may contain registration, VIN, GPS tracks and private notes. No raw backup, identifiable fixtures, coordinates, trip records, notes or secrets should enter this public repository. HA-Fuelio exposes only aggregates, but user-supplied cost *category names* are visible in local HA attributes. Previously registered entity IDs may still embed user-chosen identifying text; beta.8 does not rename them automatically. Backup imports do not backfill HA Recorder.

Not implemented: automatic Google Drive/Dropbox sync, service schedules/reminders, fuel level/range, actual per-trip consumption, multiple vehicles in one ZIP, nonmetric exports or stable release. Currency is labelled SEK for the configured profile, not independently verified from the export. Future expenses and refuellings are not booked as current spending.

## Test and release status — 2026-09-22

GitHub's synthetic suite passed **33 Python tests plus four frontend tests**, JavaScript syntax and Python compilation for beta.8. A real HA installation confirmed frontend beta.8, **36 registered sensors, zero unknown/unavailable**, the four overview panels, working selected-month categories and trip statistics, and expected booked/estimated arithmetic. These observations do **not** prove exact allocation of driving cost or correctness of all raw records.

Remaining checks: compare the per-interval estimates and ODO checkpoints with Fuelio; investigate differences between observed ODO km and the sum of logged trips without forcing them to match; determine desired handling for a paid recurring cost that has `isTemplate=1`; verify the next live ZIP replacement and reload without duplicate entities. The final Jinja-Ninja warning is a **bug in that external report template**: it still prints an alert even when expected and actual counts are both 36. No integration sensor-count error has been observed. See [beta.8 validation](BETA8_VALIDATION.md).

```bash
python -m unittest discover -s tests -v
node --check custom_components/fuelio/www/ha-fuelio-card.js
node tests/test_frontend.mjs
node tests/test_frontend_real_ids.mjs
node tests/test_cost_frontend.mjs
node tests/test_estimate_frontend.mjs
```

**Release gate:** documentation-only changes go to `dev` first. Do not call beta.8 stable or promote to `main` based solely on automated tests or current UI screenshots.
