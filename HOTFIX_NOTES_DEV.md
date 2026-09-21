# beta.5 card entity-ID hotfix

Observed from beta.4 HA screenshots: only last fuel price displayed; other existing sensors, monthly totals and all records were blank. Root cause: JS looked up Python `SensorEntityDescription.key` instead of actual Home Assistant name-generated `entity_id`. Existing sensor IDs retained a prior vehicle prefix while new beta.4 sensor IDs may have generic vehicle-name prefix.

Fix: map all backend keys to name-derived slugs, then resolve within the matching Fuelio device through `hass.entities` registry and stable unique IDs where available. Support original YAML vehicle hint, even if the monthly-cost entity itself has a different prefix; no entity ID migrations.

Verification: 20 parser/metadata/record tests; original frontend smoke test; new DOM-free cross-prefix frontend regression test including a separate second device, changed custom ID, month history and dated record; JS syntax. GitHub Actions final dev CI green. Real HA testing remains required. Upgrade integration to beta.5, restart, re-copy `www/ha-fuelio-card.js` to `/config/www/`, update Lovelace resource query to `?v=0.1.0-beta.5`, reload browser and compare readings. Main remains unchanged.
