"""One-time frontend regression and README updates. Remove after applying."""
from pathlib import Path
R = Path(__file__).resolve().parents[1]
def replace(path, before, after):
    file = R / path
    source = file.read_text(encoding='utf-8')
    count = source.count(before)
    if count != 1:
        raise AssertionError((path, before[:100], count))
    file.write_text(source.replace(before, after, 1), encoding='utf-8')

F = 'tests/test_cost_frontend.mjs'
replace(F,
  "fuel_per_logged_km: 10, total_per_logged_km: 12, categories: [{ name: 'Parkering', amount: 200 }] }],",
  "fuel_per_logged_km: 10, total_per_logged_km: 12, estimated_fuel: 70, estimated_total: 270, estimated_total_per_km: 2.7, estimate_coverage: 'one_consumption_value', trip_count: 2, average_trip_km: 15, categories: [{ name: 'Parkering', amount: 200 }] }],")
replace(F,
  "fuel_per_logged_km: 10, total_per_logged_km: 11, categories: [{ name: 'Parkering', amount: 200 }] }],",
  "fuel_per_logged_km: 10, total_per_logged_km: 11, estimated_fuel: 150, estimated_total: 350, estimated_total_per_km: 1.75, litres: 91, trip_count: 5, categories: [{ name: 'Parkering', amount: 200 }] }],")
replace(F,
  "categories_all: [{ name: 'Parkering', amount: 200 }]",
  "categories_all: [{ name: 'Parkering', amount: 200 }], estimated_lifetime: { estimated_fuel: 150, estimated_total: 350 }, lifetime_odometer_km: 205, latest_two_consumption: 5.55, latest_two_consumption_count: 2")
replace(F, "assert.match(html, /Mätarställning \\/ denna månads körsträcka/);",
  "assert.match(html, /Körsträcka denna månad/);\nassert.match(html, /Sedan importstart/);\nassert.match(html, /91 L/);\nassert.match(html, /2,7 kr\\/km/);\nassert.match(html, /Månadsstatistik/);\nassert.match(html, /Genomsnitt\\/resa/);\nassert.match(html, /15 km/);\nassert.match(html, /70,00 kr/);")
replace(F, "assert.match(html, /Kostnad\\/km denna månad/);", "assert.match(html, /Beräknad körkostnad\\/km/);")
replace(F, "assert.match(html, /Kostnad per avläst ODO-kilometer/);",
  "assert.match(html, /Bokförda utgifter per avläst ODO-kilometer/);")

# Prove that choosing an older month does not affect the top four current
# panels, while historic month data and the selected-month counter do change.
T = 'tests/test_frontend.mjs'
replace(T,
  'assert.equal(card._month, "2026-08");',
  'assert.equal(card._month, "2026-08");\nassert.match(card.shadowRoot.innerHTML, /Bokförda utgifter/);')

README = R / 'README.md'
readme = README.read_text(encoding='utf-8')
readme += '''\n\n## Development candidate: time-aware estimates and four-panel overview (not released)\n\nSee `NEXT_ITERATION_DESIGN.md`. The always-current overview groups odometer/month/year/import-km, latest consumption plus current/year litres, booked current/year expenditure, and **estimated** current/year driving cost per km. Historical month selection shows observed ODO distance, count of logged trips, and mean logged trip length. Booked cost/ODO-km remains a distinct measure in the Costs section; preserve its six legacy unique IDs.\n\nEstimates use the up-to-two latest *past* positive reported consumption readings and latest *past* positive fuel unit price as of each ODO interval's beginning. Post-refuel driving can use the new reading; earlier intervals are never repriced. A one-reading fallback is labelled limited, missing rates suppress the full-period estimate, and imprecise calendar boundaries are labelled. Estimate = sum(ODO interval km × applicable estimated SEK/km); estimated total = estimated fuel + actual non-fuel expenses in the period, without double-counting purchased fuel. Fuel bought is distinct from fuel consumed. Data is date-granular, so same-day sequencing is approximate. A user-reported real HA test and Fuelio comparison is required before release or stable promotion.\n'''
README.write_text(readme, encoding='utf-8')
print('Updated synthetic frontend regression and documented v8 semantics.')
