"""Update beta.7 docs and smoke tests; no private backup required."""
from pathlib import Path

def swap(path, before, after, count=1):
    f = Path(path)
    content = f.read_text(encoding='utf-8')
    assert content.count(before) == count, (path, before[:65], content.count(before))
    f.write_text(content.replace(before, after), encoding='utf-8')

p = 'tests/test_cost_frontend.mjs'
swap(p, '/0\\.1\\.0-beta\\.6/', '/0\\.1\\.0-beta\\.7/')
swap(p, '''  months: [{ month: '2026-09', fuel: 1000, other: 200, total: 1200, km: 100, fuel_ups: 1,
''', '''  months: [{ month: '2026-09', fuel: 1000, other: 200, total: 1200, km: 100, litres: 47.5, fuel_ups: 1,
''')
swap(p, '''assert.match(html, /Antal tankningar/);
''', '''assert.match(html, /Antal tankningar/);
assert.match(html, /Mätarställning \\/ denna månads körsträcka/);
assert.match(html, /47,5 L/);
assert.match(html, /1\\s?200,00 kr/);
assert.match(html, /Kostnad\\/km denna månad/);
assert.match(html, /Kostnad per avläst ODO-kilometer/);
''')

p = 'README.md'
swap(p, '**Beta.6 is a development candidate until the GitHub prerelease is published.**', '**Beta.7 is a development candidate; beta.6 is published and tested in HA.**')
swap(p, '- **36 sensors in beta.6:**', '- **36 sensors in beta.7:**')
swap(p, '- Six **SEK per logged km** sensors:', '- Six **SEK per odometer km** sensors:')
swap(p, '''Each period has fuel, other and total expenditure, logged trip km, fill-up count, both per-km ratios and category totals.''', '''Each period has fuel, other and total expenditure, ODO-difference km, litres, trip-distance cross-check, checkpoint dates/coverage, fill-up count, both per-km ratios and category totals.''')
start = '### Critical interpretation of kr/km\n\n'
end = '\n## Install or upgrade\n'
f=Path(p); s=f.read_text(encoding='utf-8'); assert s.count(start)==1 and s.count(end)==1
front, tail=s.split(start,1); _,rear=tail.split(end,1)
update='''### Critical interpretation of kr/km

`Fuel SEK/ODO km = fuel expenditure booked in the period / odometer checkpoint difference for that calendar period`.

`Total SEK/ODO km = (fuel + actual non-fuel expenditure) / the same ODO difference`.

A checkpoint is a tanking `Odo (km)` or OBD trip `StartOdo`/`EndOdo` with its date. For the calendar start, take the latest checkpoint strictly before that first day, then the latest in-period checkpoint as the end. If no earlier reading exists, use the first in-period reading and mark `odo_coverage: partial_start`: only the observable part is measured. If readings are absent or contradictory, km/ratios are unknown, not zero. This is observed distance allocated to calendar periods, *not exact midnight odometer readings*. `logged_trip_km` is a cross-check, never added to ODO difference. A fuel-up may book costs for fuel consumed before its transaction date. Estimated TripCost is never counted as actual expenditure.
'''
f.write_text(front+update+end+rear,encoding='utf-8')
swap(p, 'For beta.6, check for 36 entities', 'For beta.7, check for 36 entities')
swap(p, '/local/ha-fuelio-card.js?v=0.1.0-beta.6', '/local/ha-fuelio-card.js?v=0.1.0-beta.7')
swap(p, 'automatic Google Drive/Dropbox sync, full odometer-based cost/km,', 'automatic Google Drive/Dropbox sync,')
swap(p, 'Beta.6 requires new real tests for 36 sensor count, actual categories, month selection, period ratios and replacement ZIP refreshing.', 'Beta.6 passed 36-sensor/card/category display tests. Beta.7 requires real tests for odometer distances, four-tile current-month overview, cost/km, historic month selection and changed ZIP refresh.')
print('README and frontend tests updated for odometer beta.7.')
