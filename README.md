# HA-Fuelio 🚙

Read-only Home Assistant custom integration for [Fuelio](https://www.fuel.io/). **Experimental beta (`v0.1.0-beta.3`)**: sensor integration only; keep Drivvo as a fallback while validating the workflow.

## What it does

- Parses one vehicle per metric Fuelio sync ZIP with `Vehicle`, `Log`, `Costs` and `TripLog` sections.
- Exposes 19 aggregate sensors: trip counts, distance, travel time, fuel-ups, litres, fuel costs, other spending, dates, odometer and more.
- Reads a private ZIP from inside the actual HA configuration folder about every five minutes. This integration never writes to Fuelio, Drivvo or the ZIP.
- Newly configured entries/devices use a generic `Fuelio vehicle` display name; raw vehicle names, registrations, VINs, trip details and GPS coordinates are not stored in summary snapshots or exposed as sensor attributes.

**UI:** built-in configuration form plus standard sensors. A dedicated Lovelace dashboard, custom card, trip list and map are **not** included. Automatic Google Drive/Dropbox download, individual trip entities, multi-vehicle CSVs, nonmetric exports and historical recorder backfill are not yet supported.

## Installation / upgrade

1. In HACS, add `https://github.com/Jocke1970/HA-Fuelio` as a custom **Integration** repository if needed; enable prereleases and select `v0.1.0-beta.3`. Never select beta.1 (invalid HACS package). Existing users should **upgrade**, not delete/re-add the integration.
2. Leave the private ZIP at `/config/fuelio/vehicle-1-sync.csv.zip`, or the equivalent path under HA's actual config directory. Do not create an extra nested `/config/config/` directory. The integration accepts the relative path `fuelio/vehicle-1-sync.csv.zip` during *new* configuration.
3. Restart Home Assistant after installing/upgrading. New users: Settings → Devices & services → Add integration → Fuelio and provide the ZIP path. Existing users: keep the config entry and check for the same 19 sensor entities without duplicates.
4. Compare values with Fuelio, especially latest nonempty reported consumption (which may correctly remain `unknown` if no reading exists). Keep Drivvo until verified.

Manual install alternative: copy `custom_components/fuelio/` from the release into HA's corresponding directory, then restart; do not replace or publish the private ZIP.

## Data interpretation

- Fuelio's `TripDist` is metres (converted to km); `TripDuration` is seconds (converted to hours).
- `TripCost` is **estimated**, shown separately and never added to actual fuel + other spending.
- Future-dated expense records are counted separately and excluded from actual spend; template and income records are excluded.
- `Last reported fuel consumption` selects the newest **nonempty recorded reading**, even when the latest fill-up has no consumption. It is not a lifetime average or calculated guess. If none exists, HA reports `unknown`.
- ZIP history does **not** backfill HA Recorder. Totals can decrease if older records change or are deleted.
- Only metric exports (`DistUnit=0`, `FuelUnit=0`) are supported; currency is labelled SEK based on the configured Fuelio sample, not a verified ISO export field.

## Privacy and preserving existing IDs

**Existing config-entry titles and entity IDs containing a plate or vehicle identifier are not renamed automatically.** Unique IDs are stable so dashboards, automations and history are not silently broken. If desired, manually rename the existing Fuelio integration/device/entities in HA after checking references. Old Recorder history, backups and screenshots do not get cleaned automatically.

Fuelio ZIP/CSV/GPX exports can contain exact location history, vehicle identifiers and private notes. Never commit real exports, credentials or unredacted diagnostics to public GitHub issues. Review staged files even with `.gitignore` present.

## Beta verification and development flow

On beta.2, an actual HA installation showed 19 registered sensors. Temporarily removing the ZIP made sensors `unavailable`, and restoring it made readings return. A later 19-entity report was supplied; an explicit unload/reload result is not independently established. Those observations do **not** prove beta.3 upgrade behavior or refresh after replacing the ZIP with changed contents.

Required before stable: test beta.3 HACS update without duplicate entities, consumption and naming behavior, entry reload/unload, changed-ZIP refresh, error/recovery and comparison with Fuelio. Keep `main` unchanged until verified.

Development follows **`dev` → PR → `beta` prerelease → HA testing → PR → `main` stable**. GitHub Actions compiles Python and runs synthetic parser, metadata and naming-contract tests; those are not full HA runtime tests. Run `python -m unittest discover -s tests -v` from the repository root.
