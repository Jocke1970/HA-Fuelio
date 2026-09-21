# HA-Fuelio 🚙

Read-only Home Assistant integration for Fuelio. **Experimental beta (`v0.1.0-beta.1`): Home Assistant installation and HACS delivery have not yet been smoke-tested.** Keep Drivvo as a backup until the values have been compared.

## What is included?

- A native Home Assistant **configuration flow** under Settings → Devices & services → Add integration → Fuelio.
- 19 summary sensors for one vehicle per ZIP: trips, travel distance/time, monthly distance, refuelling, fuel volume and expenses, other costs, dates and odometer.
- Read-only refresh from a local Fuelio sync ZIP every five minutes. The backup path must stay inside HA's configuration folder, including after resolving symbolic links.
- No raw trips, vehicle registration, VIN or GPS location are exposed in sensor attributes. Private sample backups and credentials are not committed.

**UI scope:** only the configuration form and regular sensor entities. There is **no dedicated dashboard, custom Lovelace card, trip list, map or historical recorder backfill** in this beta.

**Not yet implemented:** automatic Google Drive retrieval, Dropbox, separate trip entities, nonmetric units or a multi-vehicle CSV import. This prerelease uses SEK-labelled currency values and expects one vehicle per backup ZIP.

## Install this beta

### HACS custom repository (experimental)

Add `https://github.com/Jocke1970/HA-Fuelio` as a custom repository with category **Integration**, then choose `v0.1.0-beta.1` if it is available. Prerelease handling and actual installation have not been verified yet; use the manual route below if HACS does not offer the version.

### Manual alternative

Copy `custom_components/fuelio/` from the `v0.1.0-beta.1` release tag into HA's `/config/custom_components/fuelio/`.

### Configure

1. Export a Fuelio sync ZIP and put it at `/config/fuelio/vehicle-1-sync.csv.zip` (create the directory first). Keep the file private: backups can contain exact location history, registration numbers, notes and VIN.
2. Restart Home Assistant.
3. Select Settings → Devices & services → Add integration → **Fuelio**.
4. Enter `fuelio/vehicle-1-sync.csv.zip` as the ZIP path (or an absolute path inside HA's config folder).
5. Compare all available sensors against Fuelio and report issues without attaching personal backups or raw logs.

On non-HAOS installations the config folder may be somewhere other than `/config`; use the actual Home Assistant config directory. Later, replace the ZIP **atomically** at the same path. The integration refreshes it roughly every five minutes, but does not download backups itself.

## Interpretation and limitations

- TripDist in the export is metres → km; TripDuration is seconds → hours.
- TripCost is an **estimated** amount and is never added to actual spending (fuel + other expenses).
- Future-dated expenses are counted separately, excluding them from current actual expenditure. Template and income records are excluded.
- Last reported fuel consumption is the last available recorded reading, not a computed lifetime mean; an empty value remains unavailable.
- Importing historic data does **not** backfill Home Assistant recorder or long-term statistics. Historical corrections may cause total sensors to decrease.
- Only metric exports (`DistUnit=0`, `FuelUnit=0`) currently work; nonmetric units trigger a validation error instead of silently generating inaccurate values.
- Currency is labelled SEK based on the known Fuelio configuration; the CSV has not supplied an independently verified ISO currency code.

## Development and release rules

`dev` → pull request → `beta` → real HA beta smoke test → pull request → `main` (stable). This beta is for testing; **do not promote to main** until the integration loads in actual HA, all 19 entities are checked, reload works, ZIP replacement refreshes, and a missing ZIP makes readings unavailable.

The GitHub Actions suite compiles the integration and runs synthetic parser regression tests. These tests do **not** replace HA runtime tests. Run locally with `python -m unittest discover -s tests -v`.

## Privacy

Never upload an unredacted Fuelio ZIP, raw CSV or GPX, registration data, precise GPS coordinates, Drive credentials or raw diagnostics to a public issue. `.gitignore` offers an extra safeguard, but always inspect staged files before commits.
