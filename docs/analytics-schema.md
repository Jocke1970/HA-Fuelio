# Fuelio analytics schema — 2026.11.0b1

This is the aggregate-only parsing contract. The historical beta.6 logged-trip-distance formula is **obsolete**; the old six entity ID slugs retain `_logged_km` solely for registry compatibility, while the actual denominator is now observed odometer distance.

## Cost categories and expense inclusion

- Optional section `CostCategories`: join `Costs.CostTypeID` to `CostCategories.CostTypeID`, display `Name` only in aggregate totals. Missing or unmatched category IDs are `Uncategorized`. Each category output is limited to 20 rows (19 plus combined `Other categories`). Internal IDs, cost titles, notes and raw individual rows are not exposed.
- `Costs` records with `isTemplate=1` or `isIncome=1` are excluded *before* counting/spending. Future-dated non-template/non-income rows are tracked as upcoming, not booked. In the latest real-HA test, a legitimately paid recurring parking expense was manually marked `isTemplate=1`, so beta.8 excluded it from both category and expense totals. This is the **current implementation**, not proof of the correct desired accounting semantics. Avoid blindly summing templates: doing so could double-count planned or repeated costs. Observe an actual recurrence/export before changing the parser.
- Actual/booked period totals = fuel-up payments + included non-fuel expenses dated within the calendar period. A transaction dated in the future is not current spending.

## Distance and trips

- ODO checkpoints originate from `Log.Odo (km)` and `TripLog.StartOdo` / `TripLog.EndOdo`, associated with trip `StartDate` / `EndDate` when present. For each calendar month/year, use highest ODO on the latest day strictly preceding the period as baseline, then highest ODO on the latest day inside the period. Without a prior checkpoint, use the first in-period day's lowest reading and set `odo_coverage: partial_start`. No valid difference/rollback => `None`, never a fabricated ratio. Lifetime uses first imported day's minimum and latest day's maximum. This reflects observed checkpoint allocation, not exact midnight kilometres.
- `TripLog.TripDist` is metres, summed /1000 as `logged_trip_km` and as the separate legacy `trip_distance_km` summaries. The selected-month `trip_count` is the number of logged trips, and `average_trip_km = sum(TripDist)/trip_count`; an absent trip count gives `None`. Do not add logged kilometres to the ODO difference or expect the measures to be identical.

## Measured fuel economy and range basis

HA-Fuelio now calculates an independent **full→full measured consumption** from the aggregate-safe Fuelio `Log` fields. A full primary-tank fill opens a measurement window. Partial fills after it are banked; the next full fill closes the window. Consumption is `100 × summed litres / odometer distance`. The overall and recent averages are distance/fuel weighted, not arithmetic means of per-fill consumption values.

A window is excluded when Fuelio marks `Missed` or `ExcludeDistance` inside the window, when tank/fuel-type continuity is broken, or when basic plausibility checks fail (non-positive/very large distance, impossible fuel volume, or implausible L/100 km). Only aggregate counts and statistics are retained. Raw fill-up rows, station/GPS, notes and identifiers are not exposed to Home Assistant.

The existing range forecast attributes now include an `economy` object with: `measured_windows`, `weighted_consumption_l_per_100km`, `recent_consumption_l_per_100km`, `recent_window_count`, `latest_window_l_per_100km`, `trend` (`increasing`/`stable`/`decreasing` in L/100 km), `trend_slope`, `anomalous_windows`, `excluded_windows`, `confidence` and `basis=full_to_full`.

Automatic range consumption uses the recent measured full→full value when at least one valid measured window exists. Otherwise it falls back to the existing latest-up-to-two positive Fuelio-reported consumption values. A persisted manual range calibration still overrides both automatic sources until a genuinely newer primary-tank fill-up is observed.

## Two independent cost models

1. **Booked SEK/ODO km**: period booked fuel expenditure / observed period ODO km, and (booked fuel + included non-fuel expenditure) / the same km. Six existing sensors expose fuel and total for this month, year, lifetime; their stable internal keys/entity IDs have historical `_logged_km` names, while display names clarify the ODO basis. No positive ODO delta means ratio `None`/`unknown`.
2. **Estimated cost of consumed fuel**: for each observed ODO interval, obtain at its **start date** the last up-to-two positive reported L/100 km values and latest valid positive fuel unit price known then. `rate_SEK_per_km = mean(L/100km) * unit_price_SEK_per_L / 100`. `estimated_fuel = sum(interval_ODOM_km * start_rate)` over all intervals for which rates are known. Missing rate for **any** positive interval makes the *whole-period* estimate unavailable. One consumption reading is allowed but marked limited; a later tanking never reprices earlier kilometres. `estimated_total = estimated_fuel + included booked non-fuel expenditure`, **not** plus purchased fuel again. The estimated cost per km uses observed period ODO km.

Both models allocate incomplete checkpoint-boundary coverage as observed *delperiod* rather than exact calendar mileage. Dates have day precision for this calculation; same-day tank-up/travel order, residual fuel and true per-trip consumption are unknown.

## Home Assistant output and bounds

`Monthly cost breakdown` main state = current month's booked fuel + non-fuel spending. Attributes include:

- `months`: newest 120 monthly aggregates, each with `month`, `fuel`, `other`, `total`, `km`, `odo_coverage`, optional `odo_start_on`/`odo_end_on`, `logged_trip_km`, `trip_count`, `average_trip_km`, `litres`, `fuel_ups`, `fuel_per_logged_km`, `total_per_logged_km` (legacy field names; ODO denominators), `categories`, `estimated_fuel`, `estimated_total`, `estimated_fuel_per_km`, `estimated_total_per_km`, `estimate_coverage` and `estimate_rate_samples`.
- `years`: newest 40 yearly aggregates with corresponding costs, purchased litres, trip counts, ODO distances, categories and estimated/booked metrics. Each year also exposes `average_reported_consumption`, `reported_consumption_samples`, `average_fuel_price` (booked fuel spend ÷ purchased litres), `fuel_price_samples`, `fuel_price_min`, `fuel_price_max`, `consumption_min` and `consumption_max`.
- `categories_all`: aggregate since import start, bounded category names/amounts; `lifetime_odometer_km`, `lifetime_odo_coverage`, `estimated_lifetime`, `latest_two_consumption`, `latest_two_consumption_count`, `history_truncated`, `months_limit`.

The top overview shows the current month/year regardless of the historical month selected in the Costs dropdown; the Costs section uses the chosen month. Zero and unavailable metrics must not be conflated. The estimated all-import `TripCost` is a separate legacy value and is **not** actual booked spending.

## Privacy and release gate

Only synthetic fixtures belong in public GitHub. No real ZIP, individual expenses, plate, VIN, GPS/route, personal notes, exact private checkpoint history or credentials. The beta.8 dashboard has rendered successfully with 36 active sensors in real HA; fine-grained ODO versus TripDist alignment, estimation accuracy, and recurring-template treatment are still to be validated. See [beta.8 validation](../BETA8_VALIDATION.md).
