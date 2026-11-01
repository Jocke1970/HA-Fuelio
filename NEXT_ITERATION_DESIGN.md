# Beta.8 design specification — implemented test candidate

**Status: code implemented and published as `v0.1.0-beta.8`; real HA smoke test passed on 2026-09-22, detailed semantics still under validation.** This file records the agreed design, not a future implementation promise. The current operational checklist and anomalies live in [BETA8_VALIDATION.md](BETA8_VALIDATION.md); actual installation instructions and supported features live in [README.md](README.md).

## Preserve contracts

Keep all 36 existing unique IDs/entity keys and installed registrations, ZIP location, read-only operation, privacy-safe aggregates and `dev → beta → main` release gates. Do not promote to `main` without real HA validation. Preserve user-registered entity IDs even where their old slugs no longer describe the current ODO-based denominators. The previously released beta.7 remains a reference.

## Four-panel always-current overview

1. **Odometer:** current reading; ODO difference for current month, current calendar year and since the first imported ODO reading. A period's last observed reading substitutes for a missing reading at month-end; show checkpoint dates and mark partial coverage.
2. **Fuel:** most recently reported consumption, volume filled this month/year, and the mean of up to two latest valid reported consumption readings. Fuel purchased is separate from fuel consumed.
3. **Booked expenditure:** current-month and current-year fuel + other included actual expenses, independent of historical month selection.
4. **Estimated driving cost per km:** current month/year using the time-aware model below; label as estimates rather than recorded cash outflow. Do not use the old `fuel_cost / odo_km` sensor as an estimate of driving fuel consumption.

Use responsive nested panels within the width allocated by the Lovelace parent view. Wider cards need a compatible dashboard layout; the frontend cannot safely force width outside its parent column.

## Historical month selection

The selected month displays observed ODO difference, count of TripLog trips, and average length of a **logged** trip (`sum TripDist / count`). ODO distance and logged-trip distance serve different purposes. Keep categorized spending, price extrema and fill-up counts. Whole-export `TripCost` stays separate from actual month spending.

## Two accounting models, not one

- **Booked expenses:** actual payment dates; preserve the existing six odometer-denominator ratios and their unique IDs for backward compatibility. Label as booked expenditure per observed ODO km.
- **Estimated consumed-fuel cost:** estimate a running fuel SEK/km for each ODO interval from the mean of the latest up to two positive L/100 km readings and latest valid positive price **available at the interval's start**. Multiply by positive ODO delta and sum by period. The next refuelling affects later intervals only; a late tanking does not reprice past driving. No previous rate means whole-period estimate unknown when positive distance is unpriced. One reported value is permitted but marked as limited. Zero or invalid ODO distance cannot yield a ratio. Dates are currently only resolved to calendar-day precision, so same-day sequencing, tank composition and exact per-trip fuel consumption remain uncertain.
- **Estimated total:** estimated consumed-fuel cost + booked included **non-fuel** spending in the corresponding period, without double-counting booked fuel. Keep unavailable/partial coverage explicit and bounded, identifier-free aggregate attributes.

## Validation and newly identified follow-up

Synthetic tests cover cross-month ODO boundary, varying tanking prices, pre/post-refuel intervals, two-reading average, no retroactive repricing, missing rate, one-reading fallback, zero km, replacement ZIP, category mapping, 36 stable IDs, four-panel UI, historical month not changing overview and read-only frontend safety. The beta.8 CI suite is green and the real HA card reports 36 available sensors.

**Still open after the 2026-09-22 user test:** reconcile the small difference between observed ODO kilometres and summed TripDist without forcibly equating them; compare estimated intervals to source data; determine how to count a *paid* parking entry that has `isTemplate=1` in a recurring Fuelio definition (current beta excludes it), using the next expected parking/export on 2026-09-25; verify ZIP replacement and integration reload with no duplicate entities. Automatic Drive download is a separate future workstream. No real user ZIP or identifiers belong in public GitHub.
