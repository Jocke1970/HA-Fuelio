# HA-Fuelio developer documentation

**Current source/release baseline: `v0.1.0-beta.8` (test prerelease, not stable).** Read the [root README](../README.md) first for current installation, available features and limitations.

## Current documentation

- [Beta.8 real HA validation and open findings](../BETA8_VALIDATION.md) — tested functionality, recurring paid parking/template ambiguity, ODO-versus-trip discrepancy, remaining checks and release gate.
- [Current analytics schema and cost semantics](analytics-schema.md) — categories, observed odometer distances, booked SEK/km, time-aware estimated driving costs, bounded attributes.
- [ODO checkpoint algorithm](../ODOMETER_ALGORITHM.md) — beta.7 baseline retained in beta.8.
- [Beta.8 design specification](../NEXT_ITERATION_DESIGN.md) — implemented design and known precision limits; no longer a future feature request.
- [Release notes](../RELEASE_NOTES.md) — historical beta changes; current release at the top.

## Historical material (not current instructions)

- [Beta.6 test plan](../ANALYTICS_TEST_PLAN.md) and [beta.6 status](beta6-status.md): retained as historical checkpoints; beta.6's logged-trip-distance ratio is superseded by ODO distance in beta.7 and later.
- [Beta.7 ODO test plan](../ODOMETER_BETA7_TEST_PLAN.md): useful historical algorithm tests, not the current beta.8 checklist.

Only synthetic test fixtures belong in public GitHub. Never commit Fuelio backup files, identifiable screenshots, vehicle identifiers, route data or credentials. Development and publication proceed `dev → beta → main`; do not promote stable until unresolved real-data issues are checked.
