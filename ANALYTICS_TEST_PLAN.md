# Beta.6 real Home Assistant validation

This file contains no private ZIP content, license plate, GPS records or raw expense IDs.

1. Update an existing beta.5 integration without deleting/readding it. Expect **36 sensors** (28 previous + 8 new), no duplicates, existing entity IDs unchanged. Use Jinja Ninja with expected count 36.
2. Copy the new JS to `/config/www/ha-fuelio-card.js`, update the single module resource URL to `/local/ha-fuelio-card.js?v=0.1.0-beta.6`, refresh, verify frontend version.
3. Check category rows against the private local ZIP: `Costs.CostTypeID` → `CostCategories.CostTypeID` → `Name`. Exclude income, templates, future expenses. Missing/mismatched IDs become `Okategoriserat`. Sum of non-fuel categories must equal `other` for the period. Do not post raw rows, identifiers, notes or ZIP publicly.
4. Select each available month; check fuel spending, other spending, distance of *logged trips*, fill-up count, fuel cost/km, total cost/km, and year totals. Year should follow the selected month. Since-start values include all imported history. If logged km = 0, both ratios must be unknown/`—`.
5. Replace the private ZIP safely with a valid newer backup; within the coordinator's next ~5-minute refresh, expect changed refuelling cost, category totals and kr/km (without restart or duplicates). When Fuelio changes no data, values should remain stable.
6. Compare historical cost/km only against ratios calculated using Fuelio's **logged TripLog distance for the same calendar period**, not odometer movement or a fuel-tank interval. Incomplete trip recording and cash-basis refuelling can bias the ratio; do not label it whole-vehicle cost per km.
7. Validate same-device entity ID lookup when 19 older entities have an old registration prefix and 17 new entities have a generic prefix; verify no cross-vehicle readings.
8. Confirm ZIP errors still become `unavailable` and recover after the file is restored. Stable `main` is off limits until successful real HA verification.
