# HA-Fuelio v0.1.0-beta.3 🚙

**Experimental bugfix prerelease for existing beta.2 installations.** The initial HACS installation succeeded in a real Home Assistant instance with 19 sensors. With the ZIP temporarily renamed, the sensors became unavailable; restoring the ZIP restored their readings. The new beta.3 code and its upgrade behavior still require a real HA test. Keep Drivvo until the figures and update workflow are verified.

## Fixed

- Stop retaining Fuelio `Vehicle.Name` in the parsed aggregate snapshot: it may contain a license plate. Newly configured entries and devices now receive the generic name `Fuelio vehicle` instead of a vehicle identifier.
- The optional consumption sensor now uses the most recent **nonempty value actually recorded by Fuelio** when the latest fuel-up has a blank reading. If there is no recorded consumption anywhere, it remains `unknown`; no estimate or synthetic average is presented.
- Regression tests for identifying-name avoidance, no-reading/older-reading cases, stable entity unique IDs, local ZIP replacement and missing-file parsing. Python compilation and synthetic tests run in GitHub Actions.

## Existing installations: important

- **Upgrade the existing Fuelio integration; do not delete/re-add it.** Entity unique IDs stay unchanged; existing plate-based entity IDs, old config-entry titles and stored registry names are deliberately **not** automatically renamed. This protects your existing references. If you want to remove identifying names, rename the entry/device/entities manually in Home Assistant after checking dashboards and automations. Earlier history, backups and screenshots are not scrubbed automatically.
- Your current private ZIP stays at `/config/fuelio/vehicle-1-sync.csv.zip` (or the equivalent location inside the actual HA config directory). No new ZIP export or configuration is required solely for this update.

## Install or update

1. In HACS, open the existing Fuelio repository and select `v0.1.0-beta.3` (enable prereleases if necessary). Do not select beta.1, whose release tag lacks `hacs.json`.
2. Restart Home Assistant after downloading. Do **not** remove or reconfigure the existing Fuelio integration.
3. In Developer Tools → States, confirm the same 19 Fuelio sensor entities remain, without duplicates; compare totals and, where source data exists, the last reported consumption with Fuelio.
4. Verify the integration can reload and still shows 19 entities. Keep the private backup ZIP out of public logs, issues and GitHub commits.

Manual alternative: copy `custom_components/fuelio/` from this release into HA's existing `/config/custom_components/fuelio/` folder, overwriting the earlier integration files, then restart HA. Do not replace your private ZIP.

## Current functionality and limits

Read-only, one metric Fuelio sync CSV ZIP per configured vehicle, 19 summary sensors, refresh about every five minutes; fuel spending and other actual expenses are separate from **estimated** trip costs. No dedicated Lovelace dashboard, automatic Google Drive/Dropbox download, individual trip entities, map, historical recorder backfill, multi-vehicle CSV parsing or nonmetric exports yet. Currency is labelled SEK based on the configured example; no independent ISO currency code has been verified from the export.

## Remaining checks before stable

- Beta.3 upgrade in a running HA installation: no duplicate entities, privacy naming as documented, correct consumption value or legitimate `unknown`, reload/unload behavior.
- Replace the ZIP with a new valid export at the same path and verify values refresh; recheck missing-ZIP unavailable/recovery with beta.3 when appropriate.
- Compare all aggregate values with Fuelio; do not promote to `main` until verified.
