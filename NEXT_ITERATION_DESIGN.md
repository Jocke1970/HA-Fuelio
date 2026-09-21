# Next Fuelio iteration — agreed specification (development only)

## Preserve contracts
Keep all 36 existing unique IDs/entity keys and installed registrations, ZIP location, read-only operation, privacy-safe aggregates, and `dev → beta → main` release gates. Do not merge or tag before synthetic CI; require real HA validation before stable. The previously released beta.7 remains a reference.

## Four-panel always-current overview
1. **Odometer:** current reading; ODO difference for the current month, current calendar year, and since the first imported ODO reading. A period's last observed reading substitutes for a missing reading at month-end; show observed checkpoint dates and mark partial coverage.
2. **Fuel:** most recently reported consumption, volume filled this month, and volume filled this year. Distinguish fuel purchased from fuel consumed.
3. **Booked expenditure:** current-month and current-year fuel + other actual expenses, unaffected by historic month selection.
4. **Estimated driving cost per km:** current month and year calculated using the time-aware model below; label as estimates rather than recorded cash outflow. Do not use the old `fuel_cost / odo_km` sensor as a driving-consumption estimate.
Use responsive nested panels; provide guidance for using a wider Lovelace parent view without forcing card width outside its allocated column.

## Historical month selection
Show the selected month's observed ODO difference, count of trips in TripLog and average length of a logged trip (sum TripDist / count); explain that average uses logged trip km while period driving distance uses ODO checkpoints. Keep categorized spending, prices and fill-up counts. Keep the whole-export TripCost estimate separate from actual monthly spending.

## Two clearly different accounting models
* **Booked expenses:** actual payment dates; preserve existing six odometer-based ratios and unique IDs for backward compatibility, label unmistakably as booked SEK per observed ODO-km.
* **Estimated consumed-fuel cost:** compute a running rate `average(last up to two positive reported L/100 km values available as of interval start) * latest positive refuel unit price available as of interval start / 100`. Integrate positive ODO checkpoint deltas assigned to calendar periods. At a refuel checkpoint, the new reading applies only to following distance; no late tank-up reprices earlier intervals. No earlier rate => unknown for a period unless complete rate-covered distance can be established. A one-value fallback is marked as limited evidence. Costs are approximate: only date-level ordering is currently known, tank composition/actual per-trip consumption are unknown. Estimated total cost = estimated consumed fuel + booked non-fuel expenses in the same period. Do not double-count booked fuel with estimated consumed fuel.
* Preserve explicit missing/partial coverage markers, zero-distance => unavailable ratios, and guard odometer rollback. Keep aggregate attributes bounded and free of trips/GPS/VIN/plate/notes/raw vehicle records.

## Validation
Synthetic cross-month ODO boundary, varying refuel prices, pre/post-refuel interval calculation, two-reading average, no retroactive repricing, insufficient rate, one-value fallback, zero km, replacement ZIP behavior, category mapping, 36 stable IDs, four-panel UI, selected historic month not changing header, and frontend security/read-only regressions. No real user ZIP in the public repository.
