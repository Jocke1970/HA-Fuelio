# HA-Fuelio 🚙

Read-only Home Assistant custom integration for [Fuelio](https://www.fuel.io/). **`dev` contains changes after experimental release `v0.1.0-beta.2`; do not treat dev as a tested release.** The first installation and 19 entity registrations were observed in a running HA instance on beta.2. Reload, ZIP refresh and missing-file behavior still require real HA testing.

## Current scope

- Parses **one vehicle per ZIP**, with Fuelio sync CSV sections `Vehicle`, `Log`, `Costs`, `TripLog`.
- Parser checked against a locally provided **private** metric Fuelio ZIP and synthetic regression fixtures. The ZIP and identifying vehicle records are not included in this repository.
- Exposes 19 summary sensors on one HA device per backup: trip count, distance, travel time, monthly distance, fuel quantity and spending, other expenses, dates, odometer, and more.
- Polls a **local ZIP path** every five minutes. The path must be inside HA's configuration folder (including after symlink resolution).
- Read-only: does not modify Fuelio, Drivvo or the backup.
- New integrations use generic titles and names (`Fuelio vehicle`); the parser does not retain raw Vehicle.Name, GPS coordinates, VIN, registration number, trip titles or notes in the snapshot or publish those as attributes.

**Not implemented:** automatic Google Drive downloads, route maps, trip-detail entities, multiple vehicles inside one CSV, actual travel cost attribution, or the visual dashboard.

## Development installation

1. For a test install, copy `custom_components/fuelio/` from branch `dev` into HA's `/config/custom_components/fuelio/`, or use the latest *released* beta instead.
2. Put your Fuelio **sync ZIP** at `/config/fuelio/vehicle-1-sync.csv.zip` inside the *actual HA configuration folder*, not a nested `/config/config/` directory. Never commit it to GitHub.
3. Restart HA; choose Settings → Devices & services → Add integration → Fuelio.
4. Enter `fuelio/vehicle-1-sync.csv.zip`, or the absolute path inside HA's configuration folder.
5. Replace the same ZIP atomically on later exports; the integration polls approximately every five minutes.

Depending on installation type, the physical configuration folder might be `/homeassistant` instead of `/config`. Relative paths are resolved against HA's active configuration folder. ZIP updates are manual.

## Important semantics

- `TripDist` is **metres**, converted to km. `TripDuration` is **seconds**, converted to hours.
- `TripCost` is an **estimate** and is **never added** to actual spending (fuel + other expenses).
- Future-dated expenses are counted separately and excluded from current actual spending. Templates and income entries are excluded.
- `Last reported fuel consumption` uses the newest **nonempty, actual reported value**, even if the latest fill-up has a blank field. It is not a computed lifetime average. If *no* reading exists, HA state remains `unknown` (missing data, not a failed ZIP refresh).
- Historic ZIP import does **not backfill Home Assistant recorder or long-term statistics**. Totals may decrease if historical records are corrected or deleted.
- Only metric exports (`DistUnit=0`, `FuelUnit=0`) are supported. Other units fail explicitly.
- Currency is labeled **SEK**, based on the known Fuelio configuration; the CSV has not independently supplied a verified ISO currency code.

## Privacy and upgrading from beta.2

Newly configured instances no longer use Fuelio's raw Vehicle.Name in their title or device name. **Existing config-entry titles and entity IDs (including plate-based IDs) are deliberately not renamed automatically:** integrations, dashboards, automations and history may depend on those IDs. After upgrading, rename the existing Fuelio config entry, device and any identifying sensor entity IDs manually using Home Assistant's UI *after checking your dashboard and automation references*. A device name provided by the user is not overwritten intentionally. Changing the parser cannot erase old names already present in the entity registry, recorder or backups.

Real Fuelio archives can contain location history, registrations, VINs and notes. Never upload ZIP/CSV/GPX, credentials, or raw diagnostics to public GitHub. `.gitignore` is defense in depth; always review staged files.

## Development workflow

`dev` → PR to `beta` → test as prerelease → PR to `main` → stable release. Do not promote to `main` until the actual HA reload, ZIP-replacement, unavailable-state, sensor-value and privacy checks pass. Current tests cover the pure parser, ZIP loader and HACS metadata; they do **not** exercise the HA runtime.

Run `python -m unittest discover -s tests -v` from repository root. Committed fixtures are fabricated and contain no private backups.
