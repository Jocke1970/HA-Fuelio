# Beta.8 real Home Assistant checklist

This prerelease is **not** stable. Keep the existing config entry, Fuelio private ZIP, and all 36 unique IDs. Do not commit real ZIPs or VIN/plates/trip GPS.

1. Install beta.8 in HACS, restart Home Assistant, copy the card JS to `/config/www/ha-fuelio-card.js` and update the **existing** sole JS resource URL to `/local/ha-fuelio-card.js?v=0.1.0-beta.8`; hard-refresh. Verify frontend shows beta.8.
2. Verify Jinja-Ninja finds exactly 36 sensors, with no duplicates, and old odometer-km sensor IDs still unchanged.
3. In the four-panel overview check odometer and observed ODO distance month/year/import; Fuelio-reported consumption and purchased litres month/year; booked expenses month/year; estimated consumed-fuel driving SEK/km month/year. `—` for unpriced historical intervals means missing prior readings, not zero.
4. Select August (or any earlier month) under Costs. Header **must stay on current calendar month**. The selected month must display its own ODO distance, TripLog trip count, mean TripDist/recorded trip, categories, estimated fuel/total driving spending, and separately booked costs per observed ODO km.
5. Check the first imported period is marked partial when no previous odometer checkpoint exists. Verify latest month ODO delta against Fuelio data (a final reading exactly on the last day is not required).
6. Compare with Fuelio's receipts and trip statistics: booked monthly spending can differ from estimated consumed fuel. A late-month tank-up must change actual cash totals but not retroactively reprice prior driving. Price and consumption are day-granular; same-day event order, residual fuel in the tank and actual per-trip fuel use are not known.
7. Replace the private ZIP atomically with new data and check results update within the normal local polling interval; then reload integration and verify no duplicate entities.

No automatic Google Drive download, full vehicle service module, per-trip actual consumption, or stable main promotion in beta.8.
