# HA-Fuelio 🚙

Read-only Home Assistant custom integration for [Fuelio](https://www.fuel.io/). **Development preview (`dev` branch): not released or confirmed in a running HA instance.**

## Current scope

- Parses **one vehicle per ZIP**, with Fuelio sync CSV sections `Vehicle`, `Log`, `Costs`, `TripLog`.
- Parser checked against a locally provided **private** metric Fuelio ZIP and synthetic regression fixtures. The ZIP and identifying vehicle records are not included in this repository.
- Exposes 19 summary sensors on one HA device per backup: trip count, distance, travel time, monthly distance, fuel quantity and spending, other expenses, dates, odometer, and more.
- Polls a **local ZIP path** every five minutes. The path must be inside HA's `/config` folder (including after symlink resolution).
- Read-only: does not modify Fuelio, Drivvo or the backup.
- No GPS coordinates, VIN, registration number, trip titles or notes are stored in the snapshot or published as HA attributes.

**Not implemented:** automatic Google Drive downloads, route maps, trip-detail entities, multiple vehicles inside one CSV, actual travel cost attribution, or the visual dashboard. Not yet a HACS release.

## Development installation

1. Copy `custom_components/fuelio/` from branch `dev` into HA's `/config/custom_components/fuelio/`.
2. Copy your Fuelio **sync ZIP** into e.g. `/config/fuelio/vehicle-1-sync.csv.zip` on HA. Never commit this file to GitHub.
3. Restart HA; choose Settings → Devices & services → Add integration → Fuelio.
4. Enter `fuelio/vehicle-1-sync.csv.zip`, or the absolute path under `/config`.
5. After future Fuelio exports, replace the same ZIP atomically. Sensors refresh within about five minutes.

On non-HAOS installations, `/config` may map to another directory. Relative paths are resolved against HA's active configuration folder. ZIP updates are deliberately manual in this preview.

## Important semantics

- `TripDist` is **metres**, converted to km. `TripDuration` is **seconds**, converted to hours.
- `TripCost` is an **estimate**, displayed separately and **never added** to actual fuel + other expenses. Do not double count.
- Future-dated expenses are counted separately and excluded from current actual spending. Templates and income entries are excluded.
- The optional Fuelio consumption figure is **last reported** consumption, not an invented lifetime average. An empty field becomes unavailable.
- Historic ZIP import does **not backfill Home Assistant's recorder or long-term statistics**. Totals may decrease when historical records are corrected or deleted.
- Only metric exports (`DistUnit=0`, `FuelUnit=0`) are supported initially. Other units fail explicitly rather than silently getting wrong conversions.
- Money is labeled **SEK**, assuming Fuelio is configured for Swedish kronor. Currency is not independently encoded in the sample; a future options flow must make this selectable before international release.

## Development workflow

`dev` → PR to `beta` → test as prerelease → PR to `main` → stable release. No automatic promotion or release until regression tests and real HA installation checks pass.

Run `python -m unittest discover -s tests -v` from repository root. The committed tests use fabricated CSV data and do not require HA.

## Privacy

Real Fuelio backups can contain location history, registrations, VINs and notes. Never upload ZIP/CSV/GPX, credentials or raw diagnostics to GitHub. `.gitignore` is defense in depth; always review staged files. Only synthetic fixtures are committed.
