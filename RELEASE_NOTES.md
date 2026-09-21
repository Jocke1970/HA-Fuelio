# HA-Fuelio v0.1.0-beta.5 🚙

**Experimental frontend hotfix for beta.4.** Beta.4 screenshot showed the most recent litre price but blank older summaries, month history and record tiles. The card wrongly assumed `SensorEntityDescription.key` equals the generated Home Assistant entity ID, and wrongly assumed pre-existing and new entities always share the same prefix.

## Fixed
- Map all 28 backend keys to their actual name-derived entity-ID suffixes; resolve entities using Home Assistant's read-only entity registry and the configured vehicle's `device_id`. Keep one vehicle's entities separated from other Fuelio vehicles, even when their generated prefixes differ.
- Accept the original dashboard YAML `entity: sensor.mmk912_monthly_cost_breakdown` as a vehicle hint when that newly generated ID differs, provided the old fuel price entity still exists. You may alternatively configure the actual monthly breakdown entity ID. Do not rename any entities for this fix.
- Card version and resource cache-buster `0.1.0-beta.5`; Python manifest bumped but backend aggregation logic and the original 28 sensor unique IDs are unchanged.
- Regression tests exercise the real beta.3 name-derived IDs, the new generic-prefix IDs, monthly cost attributes, record dates, isolation from an unrelated vehicle and the existing synthetic frontend test.

## Upgrade and install frontend again
1. Update the existing HACS Fuelio integration to `v0.1.0-beta.5`, restart Home Assistant; do not remove/re-add the integration or replace the private ZIP.
2. Run in HA terminal: `mkdir -p /config/www && cp /config/custom_components/fuelio/www/ha-fuelio-card.js /config/www/ha-fuelio-card.js && ls -lh /config/www/ha-fuelio-card.js`.
3. Change the existing single Lovelace JavaScript module resource to `/local/ha-fuelio-card.js?v=0.1.0-beta.5`. Refresh the browser fully.
4. Keep the existing YAML `type: custom:ha-fuelio-card`, `entity: sensor.mmk912_monthly_cost_breakdown`, `title: Fuelio · Bilöversikt`. If the dashboard was configured with another vehicle, use an existing or actual new `monthly_cost_breakdown` entity for that vehicle.
5. Check 28 registered sensors and all fields; compare extrema and month totals with your private Fuelio export. A legitimately absent individual reported consumption may still show `—`.

No backend service calls, Google Drive sync, service intervals, tank level or range are added. This is a prerelease. Keep the known beta.4 tag and stable `main` unchanged until real HA testing.
