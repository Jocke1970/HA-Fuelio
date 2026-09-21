# HA-Fuelio 🚙

Read-only Home Assistant custom integration for Fuelio. **Experimental beta (`v0.1.0-beta.2`) — not yet verified inside a running Home Assistant.** Keep Drivvo in place until values match. The previous `beta.1` has a HACS packaging error and must not be selected.

## Included

- Native configuration flow via Settings → Devices & services → Add integration → Fuelio.
- 19 summary sensors for one vehicle per metric Fuelio ZIP: trip totals, distance, travel time, fuel volume and expenses, odometer, dates and more.
- Local ZIP re-read approximately every 5 minutes. The ZIP path must reside within HA's configuration directory, including after resolving symbolic links.
- Read-only: Fuelio, Drivvo and the backup are never modified. Raw GPS, VIN, plate number and trip details are not published as entity attributes.
- HACS-compatible repository metadata (`hacs.json`) in beta.2's tagged source; CI tests verify its presence.

**UI scope:** built-in setup form and sensor entities only. No Lovelace dashboard, custom card, trip list or map yet.

**Not yet implemented:** automatic Google Drive or Dropbox backup fetch, recorder history backfill, nonmetric exports and multiple vehicles in a single ZIP. The currency is labelled SEK and must be verified against your Fuelio setup.

## Install v0.1.0-beta.2

1. In HACS add `https://github.com/Jocke1970/HA-Fuelio` as a custom **Integration** repository if not already added. Select `v0.1.0-beta.2` (enable prereleases if necessary). Do not choose `v0.1.0-beta.1`, which lacks `hacs.json`. If the old list persists, refresh the repository/version list; remove and re-add this custom repo only if necessary, without resetting HACS itself.
2. Alternatively copy `custom_components/fuelio/` from the beta.2 release into HA's `/config/custom_components/fuelio/`.
3. Place your Fuelio sync ZIP at `/config/fuelio/vehicle-1-sync.csv.zip` (create folder first). Do not publish this private file.
4. Restart Home Assistant; go to Settings → Devices & services → Add integration → **Fuelio**.
5. Enter `fuelio/vehicle-1-sync.csv.zip`, or the corresponding absolute path inside HA's configuration folder. Compare the values with Fuelio.

For HA deployments using a config path other than `/config`, use the real configuration folder. Later ZIP replacements should be atomic at the same path. The integration polls local storage; it does **not** download backups itself.

## Data interpretation

- Trip distance is in metres in the export and converted to km. Duration is seconds converted to hours.
- Fuelio's trip cost is **estimated**, shown separately and never added to actual fuel + other expenses.
- Future expenses are counted separately, excluded from current spending. Templates and income are excluded.
- Last consumption reflects the latest recorded figure, not a fabricated lifetime average. Missing data remains unavailable.
- Old ZIP data does not backfill the HA recorder; corrected historical totals can decrease.
- Only metric exports (`DistUnit=0`, `FuelUnit=0`) currently work. Other units explicitly fail validation.

## Branch and release policy

`dev` → PR → `beta` → real HA beta smoke test → PR → `main` (stable). The GitHub Actions suite compiles the Python integration, runs synthetic parser and HACS metadata tests, and publishes marked beta prereleases. These checks do not replace live Home Assistant tests. **Main stays unchanged until testing passes.**

## Privacy

Real Fuelio ZIP/CSV/GPX files may contain precise location history, plate numbers, notes and VINs. Do not commit or attach any unredacted backup, Drive credentials or raw diagnostics to a public GitHub issue. `.gitignore` is additional protection, not a substitute for checking staged files.
