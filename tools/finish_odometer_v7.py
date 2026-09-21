"""One-time test/docs amendments for odometer semantics; fabricated input only."""
from pathlib import Path

def replace(file, before, after, n=1):
    path = Path(file)
    value = path.read_text(encoding='utf-8')
    assert value.count(before) == n, (file, before[:70], value.count(before))
    path.write_text(value.replace(before, after), encoding='utf-8')

replace('tests/test_cost_frontend.mjs', '/0\\.1\\.0-beta\\.6/', '/0\\.1\\.0-beta\\.7/')
replace('tests/test_cost_frontend.mjs', '''  months: [{ month: '2026-09', fuel: 1000, other: 200, total: 1200, km: 100, fuel_ups: 1,
''', '''  months: [{ month: '2026-09', fuel: 1000, other: 200, total: 1200, km: 100, litres: 47.5, fuel_ups: 1,
''')
replace('tests/test_cost_frontend.mjs', '''assert.match(html, /Antal tankningar/);
''', '''assert.match(html, /Antal tankningar/);
assert.match(html, /Mätarställning \\/ denna månads körsträcka/);
assert.match(html, /47,5 L/);
assert.match(html, /1\\s?200,00 kr/);
assert.match(html, /Kostnad\\/km denna månad/);
assert.match(html, /Kostnad per avläst ODO-kilometer/);
''')
# The entity naming is deliberately stable but old slugs still say logged km.
replace('README.md', '''**Beta.6 period analytics:**''', '''**Beta.7 odometer and overview correction (dev candidate, not released until CI and beta release):** All six SEK/km calculations now use dated ODO checkpoints from tankings and OBD StartOdo/EndOdo, never the sum of TripDist. Last checkpoint before a month's/year's start anchors the interval; when absent, the first reading within the period is used and marked `partial_start`. Period distance is observed and approximate around the calendar boundary, not an exact midnight measurement. Missing or contradictory readings yield unknown. The monthly breakdown contains observed `km`, `litres`, `logged_trip_km` for cross-check, and ODO checkpoint dates/coverage; the new four-tile overview shows current ODO + month distance, month litres, month actual spend and month total SEK/ODO-km. The selected historical month changes only the Costs section. Existing 36 unique sensor IDs, including legacy `_logged_km` entity IDs, remain unchanged for backwards compatibility; sensor display names and UI explain odometer basis. The whole-export trip-cost estimate moves out of the month spending tiles. Refresh the JS and resource to `?v=0.1.0-beta.7` once released. No Drive sync or stable main promotion.\n\n**Beta.6 period analytics:**''')
replace('README.md', '''**`dev` contains an experimental candidate for `v0.1.0-beta.6`; the most recently released beta is `v0.1.0-beta.3`.**''', '''**`dev` contains a candidate for `v0.1.0-beta.7`; beta.6 is the last verified in-HA version.**''')
replace('README.md', '''**28 sensors on dev:**''', '''**36 sensors on dev:**''')
replace('README.md', '''**Not yet available:** automatic Google Drive/Dropbox sync, individual trip/route entities, map, service intervals, tank level, range, precise expense categories such as 'service', nonmetric exports, recorder backfill or multiple vehicles within a single CSV.''', '''**Not yet available:** automatic Google Drive/Dropbox sync, individual trip/route entities, map, service intervals, tank level, range, nonmetric exports, recorder backfill or multiple vehicles within a single CSV. `CostCategories` category names are now supported for cost aggregates.''')
replace('README.md', '''For beta.5 testing, choose `v0.1.0-beta.6` only once that release exists.''', '''For the next beta.7 test, choose `v0.1.0-beta.7` only once that release exists.''')
replace('README.md', '''On beta.5, check for **28 Fuelio sensors**''', '''On beta.7, check for **36 Fuelio sensors**''')
replace('README.md', '''(19 original + 8 records + 1 monthly)''', '''(19 original + 8 records + 1 monthly + 8 period analytics)''')
replace('README.md', '''This card determines the vehicle's other sensor IDs from the common prefix of the `monthly_cost_breakdown` entity.''', '''This card resolves the vehicle's other sensors via the entity/device registry using stable unique IDs; old and new entity-name prefixes can coexist.''')
replace('README.md', '''frontend version (`0.1.0-dev.1` during this initial preview)''', '''frontend version (`0.1.0-beta.7` in the candidate)''')
replace('README.md', '''The monthly selector groups all valid costs other than fuel as **Övriga utgifter**. It cannot distinguish service from parking unless Fuelio exposes and we validate reliable categories.''', '''The monthly selector groups all valid costs other than fuel as **Övriga utgifter** and splits these by `CostCategories` when category IDs are available. Monthly/yearly/all cost/km denominators are dated odometer checkpoint differences, not TripDist sums. An incomplete first month/year is labelled `partial_start`; exact midnight figures are not implied.''')
print('Frontend regression and README references amended.')
