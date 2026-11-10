# HA-Fuelio developer documentation

**Current test prerelease: `2026.11.3b5` on `beta`; stable `2026.11.2` remains on `main`.** Read the [root README](../README.md) first for current installation, available features and limitations.

## Current documentation

`2026.11.3b5` is the **accepted/frozen desktop layout**: six always-visible KPIs, the full-width Tank & range panel, then a single responsive two-column grid with 11 expandable sections. Collapsed sections show icon and title only; the opened section spans both columns and hides its original row partner until closed. Only one section is open at a time. Version information is always the final full-width tile. Narrow cards use one column. The independent mobile card is unchanged.

`2026.11.2` adds OBD fuel-left calibration with optional range/average-consumption consistency checks while retaining legacy range-only calibration.

`2026.11.1` adds English/Swedish Home Assistant translations and an options flow for enabling/disabling the calendar platform (default enabled for existing entries). Repository documentation remains English-only.

- [Beta.8 real HA validation and open findings](../BETA8_VALIDATION.md) — **historical** validation of recurring-cost/template ambiguity and ODO-versus-trip discrepancies; not the current release checklist.
- [Current analytics schema and cost semantics](analytics-schema.md) — measured full→full fuel economy, range-basis precedence, categories, observed odometer distances, booked SEK/km, time-aware estimated driving costs and bounded attributes.
- [Fuelio calendar model](calendar.md) — sanitized cost title/note fields, timed TripLog journeys, separate 256-event bounds, exclusions and read-only semantics.
- [ODO checkpoint algorithm](../ODOMETER_ALGORITHM.md) — beta.7 baseline retained in beta.8.
- [Beta.8 design specification](../NEXT_ITERATION_DESIGN.md) — historical baseline and known precision limits, superseded by the current UI description above.
- [Release notes](../RELEASE_NOTES.md) — chronological release history, newest prerelease at the top.

## Historical material (not current instructions)

- [Beta.6 test plan](../ANALYTICS_TEST_PLAN.md) and [beta.6 status](beta6-status.md): retained as historical checkpoints; beta.6's logged-trip-distance ratio is superseded by ODO distance in beta.7 and later.
- [Beta.7 ODO test plan](../ODOMETER_BETA7_TEST_PLAN.md): useful historical algorithm tests, not the current beta.8 checklist.

**UI freeze:** changes to the 11-section layout require an explicit new design decision; bug fixes and data correctness work remain allowed. The screenshots used for acceptance are not stored in this public repository. 

**Release checks:** before installing a beta, verify that HACS lists the actual GitHub prerelease tag, not just a new `beta` branch commit. Manifest, bundled desktop/mobile card versions and release notes must match. In an already-open HA browser, a footer showing an earlier version can indicate a cached frontend; check the loaded resource and reload the dashboard before concluding the release is wrong.

Only synthetic test fixtures belong in public GitHub. Never commit Fuelio backup files, identifiable screenshots, vehicle identifiers, route data or credentials. Development and publication proceed `dev → beta → main`; do not promote stable until unresolved real-data issues are checked. Stable tags/releases are created only after the exact `main` commit has passed the normal test workflow and the manifest, README, developer docs, card versions and first release-notes heading all agree on the stable version.
