# Fuelio analytics schema — beta.8 (2026-09-22)

This is the aggregate-only parsing contract. The historical beta.6 logged-trip-distance formula is **obsolete**; the old six entity ID slugs retain `_logged_km` solely for registry compatibility, while the actual denominator is now observed odometer distance.

## Cost categories and expense inclusion

- Optional section `CostCategories`: join `Costs.CostTypeID` to `CostCategories.CostTypeID`, display `Name` only in aggregate totals. Missing or unmatched category IDs are `Okategoriserat`. Each category output is limited to 20 rows (19 plus combined `Övriga kategorier`). Internal IDs, cost titles, notes and raw individual rows are not exposed.
- `Costs` records with `isTemplate=1` or `isIncome=1` are excluded *before* counting/spending. Future-dated non-template/non-income rows are tracked as upcoming, not booked. In the latest real-HA test, a legitimately paid recurring parking expense was manually marked `isTemplate=1`, so beta.8 excluded it from both category and expense totals. This is the **current implementation**, not proof of the correct desired accounting semantics. Avoid blindly summing templates: doing so could double-count planned or repeated costs. Observe an actual recurrence/export before changing the parser.
- Actual/booked period totals = fuel-up payments + included non-fuel expenses dated within the calendar period. A transaction dated in the future is not current spending.

## Distance and trips

- ODO checkpoints originate from `Log.Odo (km)` and `TripLog.StartOdo` / `TripLog.EndOdo`, associated with trip `StartDate` / `EndDate` when present. For each calendar month/year, use highest ODO on the latest day strictly preceding the period as baseline, then highest ODO on the latest day inside the period. Without a prior checkpoint, use the first in-period day's lowest reading and set `odo_coverage: partial_start`. No valid difference/rollback => `None`, never a fabricated ratio. Lifetime uses first imported day's minimum and latest day's maximum. This reflects observed checkpoint allocation, not exact midnight kilometres.
- `TripLog.TripDist` is metres, summed /1000 as `logged_trip_km` and as the separate legacy `trip_distance_km` summaries. The selected-month `trip_count` is the number of logged trips, and `average_trip_km = sum(TripDist)/trip_count`; an absent trip count gives `None`. Do not add logged kilometres to the ODO difference or expect the measures to be identical.

## Two independent cost models

1. **Booked SEK/ODO km**: period booked fuel expenditure / observed period ODO km, and (booked fuel + included non-fuel expenditure) / the same km. Six existing sensors expose fuel and total for this month, year, lifetime; their stable internal keys/entity IDs have historical `_logged_km` names, while display names clarify the ODO basis. No positive ODO delta means ratio `None`/`unknown`.
2. **Estimated cost of consumed fuel**: for each observed ODO interval, obtain at its **start date** the last up-to-two positive reported L/100 km values and latest valid positive fuel unit price known then. `rate_SEK_per_km = mean(L/100km) * unit_price_SEK_per_L / 100`. `estimated_fuel = sum(interval_ODOM_km * start_rate)` over all intervals for which rates are known. Missing rate for **any** positive interval makes the *whole-period* estimate unavailable. One consumption reading is allowed but marked limited; a later tanking never reprices earlier kilometres. `estimated_total = estimated_fuel + included booked non-fuel expenditure`, **not** plus purchased fuel again. The estimated cost per km uses observed period ODO km.

Both models allocate incomplete checkpoint-boundary coverage as observed *delperiod* rather than exact calendar mileage. Dates have day precision for this calculation; same-day tank-up/travel order, residual fuel and true per-trip consumption are unknown.

## Home Assistant output and bounds

`Monthly cost breakdown` main state = current month's booked fuel + non-fuel spending. Attributes include:

- `months`: newest 120 monthly aggregates, each with `month`, `fuel`, `other`, `total`, `km`, `odo_coverage`, optional `odo_start_on`/`odo_end_on`, `logged_trip_km`, `trip_count`, `average_trip_km`, `litres`, `fuel_ups`, `fuel_per_logged_km`, `total_per_logged_km` (legacy field names; ODO denominators), `categories`, `estimated_fuel`, `estimated_total`, `estimated_fuel_per_km`, `estimated_total_per_km`, `estimate_coverage` and `estimate_rate_samples`.
- `years`: newest 40 yearly aggregates with corresponding costs, purchased litres, trip counts, ODO distances, categories and estimated/booked metrics.
- `categories_all`: aggregate since import start, bounded category names/amounts; `lifetime_odometer_km`, `lifetime_odo_coverage`, `estimated_lifetime`, `latest_two_consumption`, `latest_two_consumption_count`, `history_truncated`, `months_limit`.

The top overview shows the current month/year regardless of the historical month selected in the Costs dropdown; the Costs section uses the chosen month. Zero and unavailable metrics must not be conflated. The estimated all-import `TripCost` is a separate legacy value and is **not** actual booked spending.

## Privacy and release gate

Only synthetic fixtures belong in public GitHub. No real ZIP, individual expenses, plate, VIN, GPS/route, personal notes, exact private checkpoint history or credentials. The beta.8 dashboard has rendered successfully with 36 active sensors in real HA; fine-grained ODO versus TripDist alignment, estimation accuracy, and recurring-template treatment are still to be validated. See [beta.8 validation](../BETA8_VALIDATION.md).
