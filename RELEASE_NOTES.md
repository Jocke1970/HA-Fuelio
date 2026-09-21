# HA-Fuelio v0.1.0-beta.1 🚙

**Experimental prerelease for real Home Assistant smoke testing.** This version has not yet been verified in a running Home Assistant installation. Please keep Drivvo in place during testing.

## Included

- Read-only import from one metric Fuelio sync CSV inside a ZIP file on the Home Assistant configuration filesystem.
- Config flow (Settings → Devices & services → Add integration → Fuelio) and 19 aggregate sensors: trips, distances, fuel, cost, odometer and relevant dates.
- Automatic local ZIP reread approximately every five minutes. No changes are written back to the ZIP or Fuelio.
- Synthetic parser regression tests and GitHub Actions; the parser was also checked against a private real-world ZIP without committing personal records.
- Sensitive trip coordinates, registration details and raw records are not exposed as entity attributes.

## Not included

- No dedicated Lovelace dashboard, custom card or interactive trip map. The configuration form and native sensor entities are the only UI.
- No automatic Google Drive or Dropbox download: place and replace the ZIP manually for now.
- No trip-by-trip entities, recorder history backfill or support for nonmetric exports.

## Installation for beta testing

1. In HACS add `https://github.com/Jocke1970/HA-Fuelio` as a custom **Integration** repository and select version `v0.1.0-beta.1` if offered. Alternatively, copy `custom_components/fuelio/` from this release to `/config/custom_components/fuelio/`.
2. Copy your private Fuelio sync ZIP into `/config/fuelio/vehicle-1-sync.csv.zip` (create the `fuelio` directory first). Never publish the ZIP or a raw log.
3. Restart Home Assistant and go to Settings → Devices & services → Add integration → Fuelio.
4. Enter `fuelio/vehicle-1-sync.csv.zip` and compare resulting sensor values against Fuelio.

Only one vehicle per ZIP, metric exports and SEK-labeled costs are supported in this prerelease. HACS distribution and running-HA setup have not yet been smoke-tested. If HACS cannot find a prerelease, use the manual install path for this test.

## Test checklist before stable promotion

- Config flow, startup, reload and removal in a running HA instance.
- All 19 entities: correct units/values, empty optional consumption, future-dated costs.
- Replace ZIP and verify refresh within about five minutes; remove ZIP to verify unavailable status.
- Confirm the ZIP and any credentials stay private. No promotion to `main` until beta testing passes.
