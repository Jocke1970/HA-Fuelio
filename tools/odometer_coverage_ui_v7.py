"""Final one-time UI adjustment: visually mark incomplete odometer periods."""
from pathlib import Path

def swap(path, before, after):
    p=Path(path)
    s=p.read_text(encoding='utf-8')
    assert s.count(before)==1, (path, before[:55], s.count(before))
    p.write_text(s.replace(before,after), encoding='utf-8')

js='custom_components/fuelio/www/ha-fuelio-card.js'
swap(js, '''      const odoNote = nowMonth?.odo_coverage === "partial_start" ? "Delmånad: första tillgängliga avläsning" :
        nowMonth?.odo_start_on && nowMonth?.odo_end_on ? `${nowMonth.odo_start_on} → ${nowMonth.odo_end_on}` : "Avläsningar saknas";
''', '''      const odoNote = (period) => period?.odo_coverage === "partial_start" ?
        `Delperiod: ${period.odo_start_on || "första avläsning"} → ${period.odo_end_on || "senaste avläsning"}` :
        period?.odo_start_on && period?.odo_end_on ? `${period.odo_start_on} → ${period.odo_end_on}` : "Avläsningar saknas";
''')
swap(js, '''`${decimal(nowMonth?.km, "km denna månad")} · ${odoNote}`''', '''`${decimal(nowMonth?.km, "km denna månad")} · ${odoNote(nowMonth)}`''')
swap(js, '''        ${this._tile("⛽", "Bränsle · månad", decimal(selected?.fuel_per_logged_km, "kr/km"))}
        ${this._tile("💳", "Totalt · månad", decimal(selected?.total_per_logged_km, "kr/km"))}
        ${this._tile("⛽", `Bränsle · ${currentYear}`, decimal(selectedYear?.fuel_per_logged_km, "kr/km"))}
        ${this._tile("💳", `Totalt · ${currentYear}`, decimal(selectedYear?.total_per_logged_km, "kr/km"))}
''', '''        ${this._tile("⛽", "Bränsle · månad", decimal(selected?.fuel_per_logged_km, "kr/km"), odoNote(selected))}
        ${this._tile("💳", "Totalt · månad", decimal(selected?.total_per_logged_km, "kr/km"), odoNote(selected))}
        ${this._tile("⛽", `Bränsle · ${currentYear}`, decimal(selectedYear?.fuel_per_logged_km, "kr/km"), odoNote(selectedYear))}
        ${this._tile("💳", `Totalt · ${currentYear}`, decimal(selectedYear?.total_per_logged_km, "kr/km"), odoNote(selectedYear))}
''')
test='tests/test_cost_frontend.mjs'
swap(test, '''  months: [{ month: '2026-09', fuel: 1000, other: 200, total: 1200, km: 100, litres: 47.5, fuel_ups: 1,
''', '''  months: [{ month: '2026-09', fuel: 1000, other: 200, total: 1200, km: 100, litres: 47.5, odo_coverage: 'partial_start', odo_start_on: '2026-09-05', odo_end_on: '2026-09-20', fuel_ups: 1,
''')
swap(test, '''assert.match(html, /Kostnad per avläst ODO-kilometer/);
''', '''assert.match(html, /Kostnad per avläst ODO-kilometer/);
assert.match(html, /Delperiod: 2026-09-05/);
''')
print('Partial odometer period now visible in header and monthly/yearly SEK-km tiles.')
