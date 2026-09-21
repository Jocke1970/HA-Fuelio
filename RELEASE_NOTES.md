# HA-Fuelio v0.1.0-beta.8 🚙

Experimental time-aware consumed-fuel costing and vehicle overview. Keep beta.7 as a known reference until real Home Assistant validation.

- New responsive four-group current-period overview: latest odometer plus current month/year/since-import ODO distance; latest reported fuel consumption, litres bought this month/year, last up-to-two reported consumption mean; actual booked spending this month/year; estimated driving total SEK/km this month/year. Historical month selection changes only the Costs content, not the current overview.
- Selected historic month now displays observed ODO distance, logged TripLog trip count, and mean LOGGED trip length. These two kilometre measures are explicitly different.
- Monthly, yearly and lifetime aggregate attributes add estimated consumed-fuel spending and estimated consumed-fuel/total SEK per ODO-km. For each observed odometer interval, use at most the two most recent positive reported L/100km readings and latest valid price known at its START; the next refuel changes only subsequent intervals. Estimated total = estimated fuel + actual non-fuel expense, never add booked fuel twice. Incomplete fuel-price/consumption coverage yields unavailable period estimates; single-reading fallback is marked limited. Daily timestamp precision and tank mixing remain limitations.
- Existing six booked cash-outlay-per-ODO-km sensors remain separate and keep their established unique IDs/entity IDs (including old `logged_km` slugs). No new sensors: still **36 total**. Existing CostCategories, ZIP path and read-only privacy constraints remain.
- 33 synthetic Python tests and four frontend smoke/regression tests pass on dev, including late refuel does not reprice earlier travel, missing data, one consumption reading and month selector not changing overview. Real HA and Fuelio value comparison required before stable main promotion. Google Drive automatic download is not included.

Upgrade integration in HACS, restart HA, re-copy `/config/custom_components/fuelio/www/ha-fuelio-card.js` to `/config/www/ha-fuelio-card.js`, update the EXISTING single JavaScript resource to `/local/ha-fuelio-card.js?v=0.1.0-beta.8`, and hard-refresh. Keep current YAML, config entry and private ZIP. Check that frontend version says beta.8 and exactly 36 sensors remain. The new estimated cost/km can show — if historical measurements are insufficient; this is intentional, not zero.

# HA-Fuelio v0.1.0-beta.7 🚙

Odometer semantics and overview fix for real-HA testing.

- Calculate month/year/import-lifetime fuel and actual-total SEK/km using ODO checkpoints from Fuelio fuel-ups and OBD trip StartOdo/EndOdo, not sum of TripDist. For each calendar period, last observation before period start is the baseline; end is latest observation inside period. If no pre-period checkpoint exists, start at the earliest in-period reading and mark `odo_coverage: partial_start`. No usable readings or rollback yields `unknown` rather than invented distance.
- Monthly breakdown attributes include `km` (observed odometer difference), `litres`, `logged_trip_km` (sanity check), and checkpoint dates/coverage. Category amounts and bounded aggregates remain. 36 unique sensor keys and IDs retained, including legacy `_logged_km` entity IDs; human-facing names clarify odometer basis.
- Header shows odometer plus current-month ODO delta, current-month litres, current-month actual expenditure and total SEK/ODO-km. It never follows the historical cost month selector. Fuel consumption/price remain in the Fuel section. Move whole-export estimated trip cost to its own explicitly non-actual summary.
- No automatic Drive download or stable main promotion. A nearest checkpoint can lie before the calendar boundary; these are observed-distance period allocations, not exact midnight readings. Validate against private Fuelio and real HA.

Upgrade HACS, reboot HA, re-copy card JS into `/config/www/ha-fuelio-card.js`, change the EXISTING sole module resource to `/local/ha-fuelio-card.js?v=0.1.0-beta.7` and hard refresh. Keep YAML and local ZIP unchanged. Verify 36 sensors and test monthly transitions.
# HA-Fuelio v0.1.0-beta.6 🚙

Experimental period analytics release based on the beta.5 dashboard tests.

- Add six read-only SEK/km sensors: fuel and all actual spending for current calendar month, calendar year, and full imported history. Denominator is **logged trip km in the SAME period**, not total vehicle mileage. No logged km yields `unknown`, not zero. A new valid ZIP updates ratios on the existing five-minute polling cycle.
- Add current month and year fill-up count sensors; lifetime fill-up count remains existing stable sensor. Future-dated fill-ups are not counted.
- Parse optional `CostCategories` (`CostTypeID` → `Name`) and join actual `Costs.CostTypeID`; exclude templates, incomes and future expenses. Unknown category ID or missing section is `Okategoriserat`. Expose only aggregated name/amount, never private cost titles, notes, category internal IDs or raw rows.
- Monthly cost breakdown attributes now include logged km, fuel-ups, both cost/km ratios and category totals; add year aggregates and lifetime category totals. Attribute summaries are capped (120 months, 40 years, 20 category rows per group), with excess names combined under `Övriga kategorier`.
- The card shows per-category expenses, six period cost/km tiles, and a separate month/year/lifetime fill-up section; no false whole-vehicle cost/km claim. Four-column mode now requires >=850px.
- Preserve the existing 28 sensor IDs and unique IDs; eight new sensors bring the integration to **36 sensors**. Existing ZIP paths remain unchanged.

Upgrade the integration in HACS and restart. Re-copy `custom_components/fuelio/www/ha-fuelio-card.js` to `/config/www/ha-fuelio-card.js`, update the SINGLE Lovelace resource to `/local/ha-fuelio-card.js?v=0.1.0-beta.6`, then hard refresh. Keep existing card YAML. Compare categories and cost/km with your private Fuelio backup in real HA before stable promotion. `main` remains unchanged.
