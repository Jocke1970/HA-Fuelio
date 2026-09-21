# HA-Fuelio v0.1.0-beta.4 🚙

**Experimental dashboard-and-records prerelease.** Beta.3 was observed in running Home Assistant with 19 registered sensors, all reporting values and the actual last reported consumption available. Beta.4's new entities and frontend still need real Home Assistant testing. Keep Drivvo as an independent reference until totals, record semantics and ZIP refresh have been checked.

## New in beta.4

- **28 sensors in total**: preserve the original 19 identifiers and add eight record sensors and one monthly cost-breakdown sensor.
- **Fuel price minima/maxima** this calendar year and since the oldest valid tanking record in the Fuelio export. A valid positive `VolumePrice` is preferred; when missing, a positive fill-up cost / litres is used. Zero, missing and future-dated readings are excluded.
- **Reported fuel consumption minima/maxima** for the same periods based on real positive Fuelio L/100km entries. These are extremes of **individual recorded tanking consumption readings, not a weighted annual/lifetime mean**. If there are no valid readings for a period, the corresponding sensor is `unknown`.
- Every record sensor exposes a `recorded_on` attribute (`YYYY-MM-DD`), newest date chosen when multiple records tie.
- New `Monthly cost breakdown` sensor: state is the current month's actual fuel + other expense spend; attributes contain a list of aggregated `month`, `fuel`, `other`, `total` values, up to the most recent 120 months. `history_truncated` indicates that older months are omitted from the selector; lifetime expenditure sensors are not truncated. No trip/GPS, notes, plate or VIN attributes.
- `custom_components/fuelio/brand/icon.png`: converted and validated 256 × 256 local HA integration icon.
- `custom_components/fuelio/www/ha-fuelio-card.js`: initial responsive **read-only** dashboard with overview, month selector, cost and fuel summaries, eight dated records, service limitations and version information. The frontend preview is internally labelled `0.1.0-dev.1`; backend version is `0.1.0-beta.4`.

## Updating an existing installation

1. In HACS, select **`v0.1.0-beta.4`** for your already-added HA-Fuelio integration (enable prereleases). Do not delete/re-add the existing config entry; restart HA after installing.
2. Keep the private ZIP in the same configured location, normally `/config/fuelio/vehicle-1-sync.csv.zip` or the actual HA config equivalent. Do not upload it publicly or overwrite it for the sake of this update.
3. Verify **28 registered sensors**: 19 old IDs remain and nine new entities appear. No duplicates should be created. Check that the old totals match beta.3 and that the new records reflect only the history present in your Fuelio backup.

## Install the dashboard card (one additional manual step)

HACS downloads the card within the integration folder but does **not** automatically register a separate Lovelace resource. From a terminal in HA, using your actual config root (`/config` below):

```bash
mkdir -p /config/www && cp /config/custom_components/fuelio/www/ha-fuelio-card.js /config/www/ha-fuelio-card.js && ls -lh /config/www/ha-fuelio-card.js
```

If `www` is new, restart HA. Add **one** dashboard JavaScript-module resource at `/local/ha-fuelio-card.js?v=0.1.0-beta.4` and refresh the browser. Add a Manual card using the actual entity ID for your car:

```yaml
type: custom:ha-fuelio-card
entity: sensor.your_vehicle_monthly_cost_breakdown
title: Fuelio · Bilöversikt
```

See README for exact steps. The card uses only its configured entity prefix to find the other Fuelio entities and performs no HA service calls.

## Important limits

- **No automatic Drive download, trip map, service due dates, tank level, range or detailed expense categories yet.** These are not guessed or imported from Drivvo. All other Fuelio costs appear as `Övriga utgifter`.
- Year means January 1 to today in HA local time; lifetime means the valid records in the current ZIP, **not** the older Drivvo database. Exporting only three fill-ups yields records from only those three.
- Costs and readings are metric and labelled SEK based on the observed Fuelio setup. Old history is not backfilled into Recorder. Current-month zero costs are displayed as zero, and missing records as `unknown` / `—`.
- No raw private Fuelio files or identifiers committed; no automatic renaming of old plate-based entity IDs or config titles.

## Verification before stable

GitHub Actions compiles Python, runs synthetic Python parser/metadata and record tests, checks JavaScript syntax and runs a synthetic frontend smoke test. These are **not** a substitute for a running Home Assistant test. In beta.4, validate HACS installation, 28 entities, no duplicates, sensor aggregation against Fuelio, record dates, monthly selector/mobile layout, upgrade and reload, new-content ZIP poll and error recovery. Keep `main` unchanged until testing passes.
