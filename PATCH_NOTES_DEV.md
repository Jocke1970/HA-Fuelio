# Development patch after v0.1.0-beta.2

Status: **development only**. Do not release or merge to `main` until real Home Assistant checks pass.

## Changes

- Discard raw `Vehicle.Name` during CSV parsing and use a generic `Fuelio vehicle` name for new HA config entries and devices.
- Keep existing entity unique IDs unchanged, and intentionally avoid automatic renaming of existing config entries/entity IDs to prevent breaking users' automations and dashboards. Existing plate-based IDs must be reviewed and renamed by the user in HA if desired.
- Choose the most recent nonempty, real fuel-consumption reading. If every tanking record lacks consumption, the sensor stays `unknown`; no fabricated average.
- Add synthetic tests for identifier privacy, consumption fallback, no-reading behavior, local ZIP replacement and missing-file error.

## Still to verify in running HA

- No entity duplication after upgrade; entry/device display names and old IDs behave as documented.
- Sensor value comparison, especially consumption, using a private Fuelio export.
- ZIP replacement refresh in ~5 min; missing ZIP yields unavailable; recovery after file returns.
- Config entry reload and unload. Do not promote to stable until these pass.

Privacy: never commit real Fuelio backups, registration numbers, GPS data or secrets.
