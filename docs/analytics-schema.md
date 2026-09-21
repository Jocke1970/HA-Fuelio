# Fuelio cost analytics schema, beta.6

This describes the parsing contract without any private backup records.

The earlier user-provided Fuelio export contains `CostCategories` with columns `CostTypeID`, `Name`, `priority`, `color`, `guid`, `lastupdated`; `Costs` includes `CostTypeID`, `Date`, `Cost`, `isTemplate` and `isIncome`. The join is exact by `CostTypeID`. The parser ignores private IDs after lookup, publishes only category-name/amount aggregates, and falls back to `Okategoriserat` for absent/mismatched categories. It excludes templates, income and future expenses. The six-expense replacement ZIP currently installed in HA was not available for direct inspection, so category values from that newer export require an actual HA test.

Ratios for month, year and full imported history use (fuel cost)/(logged TripLog distance) and (fuel plus actual nonfuel costs)/(logged TripLog distance) respectively, restricted to the same calendar period. Distance is from `TripDist` in metres divided by 1000. No positive logged distance means unavailable ratio (`None`/`unknown`), never zero. These are expenditure per **logged** km, not an odometer-derived full-vehicle operating cost, and fuel cost is booked when refuelling occurs.

Month selector attributes: `months` up to 120 entries containing month, fuel, other, total, km, fuel_ups, two ratios, and a bounded category aggregate. Also `years` up to 40 entries and `categories_all`. Category rows capped to 20 with overflow summed as `Övriga kategorier`. No raw expense rows, notes, routes, plate, VIN, category internal IDs or GPS fields are surfaced.
