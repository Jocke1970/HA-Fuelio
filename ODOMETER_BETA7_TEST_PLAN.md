# Beta.7 ODO and overview real-HA test plan

Use only your private local Fuelio ZIP. Never commit/export source records or vehicle identifiers to GitHub.

- Existing integration: upgrade in HACS and restart HA; keep existing config entry and original sensor IDs. Expect exactly 36 Fuelio sensors, no duplicates. Optional missing ODO periods can yield unknown legitimately.
- Frontend: re-copy bundled `www/ha-fuelio-card.js` to HA `/config/www/ha-fuelio-card.js`, update one existing JS module resource to `?v=0.1.0-beta.7`, hard refresh. Verify card version beta.7.
- Header: latest odometer plus CURRENT month's observed ODO distance in first tile, this month's litres in second, actual cost in third, total SEK/ODO km in fourth. Choose an old month below; the header must continue displaying the current month.
- Verify month kilometres against the final reading before month start and final reading within month; a refuel or OBD trip can supply a checkpoint. If prior checkpoint missing, period `odo_coverage=partial_start` and UI must visibly say `Delperiod`. If no valid difference, ratio unknown and card dash; never divide by zero.
- Check month/year/import-lifetime six SEK/km figures; no TripDist sum as denominator. Legacy `_logged_km` entity IDs must stay unchanged, although human-facing labels now state ODO.
- Ensure month cost category sums match actual expense totals; the estimated TripCost is outside month costs and labelled whole-export estimate.
- Replace local ZIP with a valid backup containing a new tanking or trip, check updated litres, ODO distance and cost/km on next polling cycle. Failed/missing local ZIP still triggers unavailable and restores when returned.
- This beta does NOT implement Drive auto-download or exact midnight odometer snapshots. Calendar allocation is only as precise as timestamped source checkpoints. Keep `main` unchanged until user confirms real results.
