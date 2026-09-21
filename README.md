# HA-Fuelio 🚙

**Beta.5 card hotfix:** The 28 sensor IDs are generated from displayed names rather than Python parser keys; existing entities can keep an old vehicle prefix while new ones use a generic prefix. The card now resolves them through the HA entity/device registry. Upgrade your existing integration and copy the card JS again into `/config/www`, keeping one Lovelace resource at `/local/ha-fuelio-card.js?v=0.1.0-beta.5`. Browser refresh required. No entity renaming or new ZIP is required.


Read-only Home Assistant custom integration for [Fuelio](https://www.fuel.io/). **`dev` contains an experimental candidate for `v0.1.0-beta.5`; the most recently released beta is `v0.1.0-beta.3`.** Keep Drivvo as a reference until aggregate values and update behavior are verified in real Home Assistant.

## What it does

- Reads a single vehicle's **metric** Fuelio sync CSV ZIP (`Vehicle`, `Log`, `Costs`, `TripLog`) from HA's config folder about every five minutes. Never changes Fuelio, Drivvo or the ZIP.
- **28 sensors on dev:** the original 19 summary sensors (IDs unchanged), eight new fuel-price/consumption records, and one monthly cost-breakdown sensor for the custom card.
- New records: lowest/highest positive fuel price **this calendar year** and **since the first relevant record in the export**, plus lowest/highest positive *reported L/100 km per fuel-up* for the same two periods. Each record sensor has a `recorded_on` attribute with the newest date when tied. No reported consumption means `unknown`, never an invented average. Fuel price uses positive `VolumePrice`, falling back to positive cost divided by litres when needed.
- `Monthly cost breakdown` exposes the current month's actual spend as its state and `months` attributes (`month: YYYY-MM`, `fuel`, `other`, `total`) for the most recent **120 recorded months**. The current month is always included; `history_truncated: true` warns if older months are omitted from the selector. **Lifetime sensors still include all records.** Future expenses, template entries, and income entries never count toward actual spend. Fuelio trip estimates are separate from actual costs.
- `custom_components/fuelio/brand/icon.png` is the native Home Assistant integration icon. A responsive, standalone, read-only Lovelace card is included at `custom_components/fuelio/www/ha-fuelio-card.js`; see installation below.

**Not yet available:** automatic Google Drive/Dropbox sync, individual trip/route entities, map, service intervals, tank level, range, precise expense categories such as 'service', nonmetric exports, recorder backfill or multiple vehicles within a single CSV. These fields are deliberately shown as unavailable rather than imported from Drivvo.

## Install or upgrade the integration

1. In HACS, use the custom **Integration** repository `https://github.com/Jocke1970/HA-Fuelio` and choose the latest **published** prerelease. For beta.5 testing, choose `v0.1.0-beta.5` only once that release exists. Beta.1 is broken and must not be installed.
2. Keep your ZIP in HA's **actual configuration directory**, e.g. `/config/fuelio/vehicle-1-sync.csv.zip` or `/homeassistant/fuelio/vehicle-1-sync.csv.zip` depending on deployment. Never place it in a nested `config/config` directory, post it publicly or commit it to GitHub.
3. Restart Home Assistant after the upgrade. **Do not remove/re-add an existing Fuelio integration**: its config entry and 19 prior entity IDs must remain stable. New installs use Settings → Devices & services → Add integration → Fuelio, ZIP path `fuelio/vehicle-1-sync.csv.zip`.
4. On beta.5, check for **28 Fuelio sensors** (19 original + 8 records + 1 monthly), no duplicated old IDs, plausible fuel prices and reported consumption, and unchanged existing totals. Optional missing extrema can legitimately be `unknown`.

Manual integration alternative: copy `custom_components/fuelio/` from the chosen release into HA's existing `custom_components/fuelio/` folder, then restart. Never overwrite your Fuelio ZIP.

## Install the Lovelace card (manual frontend resource)

**HACS installs the integration files but this release does not automatically register its separate Lovelace card.** Run this complete command in a Home Assistant terminal (replace `/config` with the actual config root if needed):

```bash
mkdir -p /config/www && cp /config/custom_components/fuelio/www/ha-fuelio-card.js /config/www/ha-fuelio-card.js && ls -lh /config/www/ha-fuelio-card.js
```

If `www` was newly created, restart Home Assistant so `/local` is available. In your dashboard's **Resources** settings, add a JavaScript module resource with URL `/local/ha-fuelio-card.js?v=0.1.0-beta.5` and type **JavaScript module**. Refresh the browser/dashboard after updating the file or version in the URL to avoid cached JS. **Do not add the resource twice.**

Paste this entire YAML as a **Manual card**, replacing `sensor.your_vehicle_monthly_cost_breakdown` with your actual sensor entity ID from Developer Tools → States:

```yaml
type: custom:ha-fuelio-card
entity: sensor.your_vehicle_monthly_cost_breakdown
title: Fuelio · Bilöversikt
```

This card determines the vehicle's other sensor IDs from the common prefix of the `monthly_cost_breakdown` entity. No registration or GPS information is embedded in the JavaScript or repository examples. You can place multiple cards with different monthly entities for separately configured vehicles. The card requires the beta.5 backend's new sensors; on older installs it displays missing values instead of inventing them.

The card displays compact overview tiles, month selector with year/month expenditure, lifetime totals, fuel summary, eight dated records, service-data limitations, and its frontend version (`0.1.0-dev.1` during this initial preview). The layout uses two columns on mobile and four where space permits. It sends **no Home Assistant service calls** and has no remote dependencies.

## Data definitions and privacy

- `TripDist` metres → km; `TripDuration` seconds → hours; `TripCost` is **estimated** and never added to actual fuel and other expenses.
- `Last reported fuel consumption` uses the most recent nonempty recorded value, even when the most recent fill-up is blank. It is not the lifetime average. The new minimum/maximum sensors compare **individual real L/100km readings**, not a mean of a year, and reject zero/missing records.
- This year's records mean **Jan 1 to today** in HA's local timezone, excluding future-dated fill-ups. Since-start means data present in the Fuelio ZIP, **not** historic Drivvo data. Dates use the calendar day in the export.
- The monthly selector groups all valid costs other than fuel as **Övriga utgifter**. It cannot distinguish service from parking unless Fuelio exposes and we validate reliable categories. Historical months without any recorded spending are not inserted artificially, except the current month (to show zero when appropriate).
- Monetary values are labelled SEK based on the known configuration, not independent proof of the export's ISO currency. Historical corrections can reduce totals. ZIP imports do not backfill Home Assistant Recorder.
- Original entity unique IDs use the stable existing format. Existing vehicle/plate-based entity IDs and config-entry titles are **not silently renamed** on upgrade. Rename them manually in HA only after checking automations, dashboards and history references.
- Fuelio ZIPs may include VIN, registration, notes and precise location trails. The snapshot and the month/record attributes contain only generic names, numeric aggregates and dates. Never commit or publish unredacted exports or diagnostics.

## Verification and branches

`dev` → pull request → `beta` prerelease → real HA tests → pull request → `main` stable. Do not promote to `main` without verification. The beta.2 missing-file and recovery tests passed in a real HA; beta.3 was observed with all 19 sensor values (including an available reported consumption of 5.8 L/100km). An exhaustive comparison with Fuelio, changed-content ZIP refresh, card behavior and complete reload/unload have not all been independently verified.

Run regression tests from repository root:

```bash
python -m unittest discover -s tests -v
node --check custom_components/fuelio/www/ha-fuelio-card.js
node tests/test_frontend.mjs
```

All committed test records are fabricated; no real Fuelio backup belongs in the repository.
