# HA-Fuelio 🚙

Read-only Home Assistant integration for [Fuelio](https://www.fuel.io/). Development follows `dev → beta → main`; `main` is not promoted until real Home Assistant testing is complete. **Beta.7 is a development candidate; beta.6 is published and tested in HA.** Keep Drivvo as a reference for independent verification.

## Features

- Reads one vehicle's local metric Fuelio sync ZIP (`Vehicle`, `Log`, optional `CostCategories`, `Costs`, `TripLog`) roughly every five minutes. It never modifies the ZIP or posts to Fuelio.
- **36 sensors in beta.7:** the original 19 stable summary sensors, eight dated fuel-price/consumption extrema, monthly cost breakdown, and eight additional analytics sensors. Existing sensor unique IDs are unchanged.
- Six **SEK per odometer km** sensors: fuel expenditure and total actual expenditure for the current calendar month, current calendar year and entire imported history. Two more sensors count fuel-ups for the current month and year; the original `Fuel-ups` counts all non-future fill-ups in the import.
- `Monthly cost breakdown` contains capped aggregate `months` (up to 120), `years` (up to 40), and `categories_all` attributes. Each period has fuel, other and total expenditure, ODO-difference km, litres, trip-distance cross-check, checkpoint dates/coverage, fill-up count, both per-km ratios and category totals. The current month always exists; `history_truncated` indicates when older months are absent from the selector. Lifetime sensors cover all records.
- `Costs.CostTypeID` links to `CostCategories.CostTypeID` and uses the matching `Name` only as an aggregate display label. Missing/unmatched category IDs are `Okategoriserat`. Templates, income and future expenses do not count as actual expenditure. Each category list contains at most 20 entries, with overflow grouped into `Övriga kategorier`. No individual expense, notes, internal IDs, trip routes, location coordinates or vehicle identifiers are exposed as state attributes.
- Eight extrema: positive recorded fuel prices and individual reported fuel consumption, lowest/highest this year and since import start, with `recorded_on` dates. Missing actual consumption stays `unknown` rather than using an invented average.
- A responsive, standalone Lovelace card at `custom_components/fuelio/www/ha-fuelio-card.js` displays monthly selection, categorized expenses, per-period fuel-ups, cost/km, fuel statistics, records and limitations. Icon: `custom_components/fuelio/brand/icon.png`.

### Critical interpretation of kr/km

`Fuel SEK/ODO km = fuel expenditure booked in the period / odometer checkpoint difference for that calendar period`.

`Total SEK/ODO km = (fuel + actual non-fuel expenditure) / the same ODO difference`.

A checkpoint is a tanking `Odo (km)` or OBD trip `StartOdo`/`EndOdo` with its date. For the calendar start, take the latest checkpoint strictly before that first day, then the latest in-period checkpoint as the end. If no earlier reading exists, use the first in-period reading and mark `odo_coverage: partial_start`: only the observable part is measured. If readings are absent or contradictory, km/ratios are unknown, not zero. This is observed distance allocated to calendar periods, *not exact midnight odometer readings*. `logged_trip_km` is a cross-check, never added to ODO difference. A fuel-up may book costs for fuel consumed before its transaction date. Estimated TripCost is never counted as actual expenditure.

## Install or upgrade

1. Add the HACS custom integration repository `https://github.com/Jocke1970/HA-Fuelio` (category **Integration**) and select the latest **published** beta prerelease. Do not install the broken beta.1 tag.
2. Keep the private ZIP inside Home Assistant's actual configuration root: `fuelio/vehicle-1-sync.csv.zip`, typically `/config/fuelio/vehicle-1-sync.csv.zip` or `/homeassistant/fuelio/vehicle-1-sync.csv.zip`. Do not put it in a nested `config/config` folder, GitHub or public logs. The config flow uses the relative path `fuelio/vehicle-1-sync.csv.zip`.
3. Update through HACS and restart Home Assistant. **Do not delete/re-add the integration or rename existing entities:** the original registration-based IDs may differ from the new generic vehicle-name IDs, but the card uses the HA entity/device registry to associate them safely.
4. For beta.7, check for 36 entities (28 previous + eight new), and compare the new category, fill-up and kr/km figures with your private Fuelio export. Nothing is promoted to stable without the real HA test.

Manual alternative: copy the integration directory from the selected release into the existing `custom_components/fuelio/` directory and restart. Never overwrite the Fuelio ZIP.

## Lovelace card

HACS installs the integration but does not automatically register the separate card. After updating the integration, run this **entire command** in the HA terminal (adapt `/config` if your configuration root differs):

```bash
mkdir -p /config/www && cp -f /config/custom_components/fuelio/www/ha-fuelio-card.js /config/www/ha-fuelio-card.js && ls -lh /config/www/ha-fuelio-card.js
```

Keep **one** dashboard resource of type JavaScript module and update its URL to `/local/ha-fuelio-card.js?v=0.1.0-beta.7`. Fully refresh the browser. If `/config/www` was first created, restart HA to expose `/local`.

Manual dashboard card (replace `entity` with the actual monthly breakdown sensor if this vehicle uses another ID):

```yaml
type: custom:ha-fuelio-card
entity: sensor.mmk912_monthly_cost_breakdown
title: Fuelio · Bilöversikt
```

For the existing test installation, `sensor.mmk912_monthly_cost_breakdown` is a legacy vehicle hint; the real registered monthly sensor can have a different prefix. The card resolves the rest within the same Fuelio device. Multiple vehicles need separate card configurations. The card is read-only and has no remote requests or Home Assistant service calls.

## Privacy, scope and limitations

The backup may contain VIN, registration, notes and precise GPS trails. Only aggregate values are retained. Cost category names are user-supplied text and become visible in the user's own HA attributes; do not include sensitive information in category names if that matters. Never commit, upload or publish an unredacted ZIP, private credentials, raw diagnostics or genuine vehicle test fixtures.

Not yet implemented: automatic Google Drive/Dropbox sync, service schedules, fuel level/range, individual routes, recorder history backfill, nonmetric exports or multiple vehicles in one ZIP. Amounts are labelled SEK according to the current configured profile, not independent verification of export currency. Future refuelling/expenses are excluded from reported actual spend. Backup imports do not backfill HA Recorder.

## Testing and release workflow

`dev → PR → beta prerelease → real HA validation → PR → main`. Known real tests: beta.2 missing-ZIP failure and recovery; beta.3 all original 19 values; beta.5 all 28 sensor values and the dashboard after mixed-prefix fixes. Beta.6 passed 36-sensor/card/category display tests. Beta.7 requires real tests for odometer distances, four-tile current-month overview, cost/km, historic month selection and changed ZIP refresh. The older uploaded backup contains `CostCategories`/`Costs.CostTypeID`, but the newer six-expense HA backup is not present in this repository or in the current conversation attachments.

Local CI commands, using only fabricated test fixtures:

```bash
python -m unittest discover -s tests -v
node --check custom_components/fuelio/www/ha-fuelio-card.js
node tests/test_frontend.mjs
node tests/test_frontend_real_ids.mjs
node tests/test_cost_frontend.mjs
```
