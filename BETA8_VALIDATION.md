# HA-Fuelio beta.8 — real Home Assistant validation

**Status on 2026-09-22:** published beta.8; real UI and sensor smoke test **passed**, detailed data semantics **partially verified**. This is not a stable release and is not approved for `main`. Preserve the existing config entry, private Fuelio ZIP, and all 36 sensor unique IDs. Do not commit real ZIPs, trip/GPS data, VIN, plate, notes, credentials or private receipts.

## Verified observations in the user's HA

- Frontend identifies itself as `0.1.0-beta.8`. The four grouped overview panels, fuel/record sections, historical month selector, categories, month-specific trip stats, and separate estimated versus booked spending are visible.
- Jinja-Ninja lists **36 expected / 36 registered, 36 OK, 0 unknown and 0 unavailable**, with no duplicate sensors reported. Its bottom-line text still emits an incorrect 'different sensor count' warning even when both numbers are 36; this is a **template condition defect**, not an HA-Fuelio sensor-count failure. Jinja-Ninja itself is not changed by beta.8.
- Current-month/annual booked spending adds up to booked fuel + included non-fuel costs. Estimated total adds estimated consumed fuel + included non-fuel costs, not fuel purchases again. The displayed ratios and individual currency totals are mutually consistent at their rounding precision. This checks arithmetic consistency, **not** independent correctness against every Fuelio source row.
- September's logged-trip count and summed `TripDist` agree with the source app's trip statistics to display precision. Observed ODO distance differs slightly from summed logged trips; these are intentionally distinct measurements and their individual checkpoint allocation has not been audited.
- Cost-category mapping renders the user's corrected category for a newly reclassified parking item. Eight historical extrema and reported consumption continue to display.

## Confirmed recurring-cost behavior / unresolved business rule

A parking payment that was actually made was subsequently marked recurring/template by the user. The **local private ZIP is confirmed to contain the row** with `isTemplate=1` and `isIncome=0`. The beta.8 parser skips `isTemplate=1` rows, explaining its disappearance from expense count, booked totals and the parking category. This is **not** a missing ZIP file, ZIP-refresh failure, category-join bug or proof of a missing payment in Fuelio. The app still shows the paid entry. A future recurring parking row is also visible in the app.

**Open decision:** how Fuelio represents a realized instance versus the recurring rule in future backups. Inspect the next normal parking event/export on Friday **2026-09-25**. Only then decide whether to adapt parsing (e.g., distinguish template from realized instance using reliable export fields); never indiscriminately count all templates because that risks double counting planned charges. No patch was made for this anomaly.

## Remaining real-HA tests

1. Compare latest private ZIP checkpoint dates/values with the ODO distance for selected month, year and lifetime; specifically investigate the small observed-ODO versus summed-trip delta without requiring equality. No exact midnight readings are promised; first imported period uses `partial_start`.
2. Compare the time-aware interval fuel estimates to the source app's available consumption and refuelling timestamps. Verify late refuelling affects only following ODO intervals. Missing prior price/consumption legitimately yields `—`; one usable consumption report is limited evidence. Day-level ordering and tank mixing mean estimates are approximate.
3. Check the next recurring parking event's source export flags versus paid versus scheduled status. Validate expense totals, monthly categories and future-expense counter after the new ZIP is imported. A screenshot alone cannot prove how every source row is flagged.
4. Replace the ZIP **atomically** with new data and ensure poll updates within about five minutes, then verify reload/restart recovers with 36 unchanged sensors and no duplicates. The earlier missing ZIP and replacement behavior had separate tests, but this complete beta.8 flow still needs real verification.
5. Confirm the historical month selector changes only Costs, while four-panel overview stays on current month/year. This has synthetic regression coverage and screenshot observations; explicit interaction switching test is still useful.

## Tests and release policy

The beta.8 source passed **33 Python unit tests**, four frontend smoke/regression tests and Python/JavaScript syntax checks in GitHub CI. Tests use synthetic fixtures only. Service schedules, fuel level/range, actual consumption per trip and automatic Google Drive sync do not exist in beta.8. Follow `dev → PR → beta → real HA validation → PR → main`; do **not** promote stable on synthetic tests or a partly verified dashboard alone.
