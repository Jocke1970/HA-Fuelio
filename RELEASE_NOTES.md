# HA-Fuelio v0.1.0-beta.2 🚙

**Experimental HACS installation fix.** The initial `v0.1.0-beta.1` release is missing `hacs.json` in its tagged source, causing HACS to reject that version. Install `v0.1.0-beta.2` instead. This integration has not yet been smoke-tested inside a running Home Assistant. Keep Drivvo during verification.

## Fixed

- Include root `hacs.json` **in the selected prerelease tag**. HACS reads this file from the selected version during download, not only from the repository default branch.
- Add CI regression tests for `hacs.json`, integration folder and manifest structure.
- Guard future beta releases against missing HACS metadata and release notes that do not match the manifest version.

## Included

- Read-only import of one metric Fuelio sync CSV ZIP that you place locally inside Home Assistant's config directory.
- Native configuration form and 19 aggregate sensors covering trips, total and monthly distance, travel time, fuel-ups, litres, fuel spending, other expenditure, dates and odometer.
- Local ZIP read approximately every five minutes; no writes to Fuelio, the ZIP or Drivvo.
- No individual trip records, GPS coordinates, vehicle registration, VIN or raw notes in sensor attributes.

## Not included

- No ready-made Lovelace dashboard, custom frontend card or route map. Only the configuration form and standard sensors.
- No automatic Google Drive / Dropbox retrieval. You must place/replace the ZIP manually.
- No historic recorder backfill, nonmetric exports or multi-vehicle CSV parsing.

## Beta installation

1. In HACS, use `https://github.com/Jocke1970/HA-Fuelio` as a custom **Integration** repository and select `v0.1.0-beta.2` (enable prerelease versions when necessary). If HACS has cached beta.1, reload the repository/version list; remove and re-add this *custom repository* only if needed. Do not delete or reset the HACS integration itself.
2. Alternatively, install manually by copying `custom_components/fuelio/` from this release to `/config/custom_components/fuelio/`.
3. Put your private Fuelio sync ZIP in `/config/fuelio/vehicle-1-sync.csv.zip`; create the folder first. Never commit the ZIP to GitHub.
4. Restart HA, then Settings → Devices & services → Add integration → Fuelio. Enter `fuelio/vehicle-1-sync.csv.zip`.
5. Compare the entities with Fuelio. Keep Drivvo working until results are verified.

**Limitations:** one vehicle per ZIP, metric Fuelio exports, costs labelled SEK. The first beta's source code is not otherwise changed by this HACS packaging fix.

## Checks before stable

- Verify HACS downloads beta.2 and HA can configure/start/reload/unload the integration.
- Compare all 19 sensors with Fuelio, including future-dated expenses and missing consumption.
- Verify ZIP replacement refresh and missing-backup unavailable behavior.
- Never upload unredacted vehicle backups, GPS records or credentials to public GitHub issues.
- Do not promote to `main` before real Home Assistant beta checks pass.
