"""One-time prerelease metadata update after all development tests passed."""
from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
manifest_file = root / 'custom_components/fuelio/manifest.json'
manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
assert manifest['version'] == '0.1.0-beta.7', manifest['version']
manifest['version'] = '0.1.0-beta.8'
manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
card_file = root / 'custom_components/fuelio/www/ha-fuelio-card.js'
card = card_file.read_text(encoding='utf-8')
assert card.count('0.1.0-beta.7') == 2, card.count('0.1.0-beta.7')
card_file.write_text(card.replace('0.1.0-beta.7', '0.1.0-beta.8'), encoding='utf-8')
test_file = root / 'tests/test_cost_frontend.mjs'
test = test_file.read_text(encoding='utf-8')
assert test.count('beta\\.7') == 1, test.count('beta\\.7')
test_file.write_text(test.replace('beta\\.7', 'beta\\.8'), encoding='utf-8')
notes_file = root / 'RELEASE_NOTES.md'
notes = notes_file.read_text(encoding='utf-8')
assert notes.startswith('# HA-Fuelio v0.1.0-beta.7')
notes = '''# HA-Fuelio v0.1.0-beta.8 🚙

Experimental time-aware consumed-fuel costing and vehicle overview. Keep beta.7 as a known reference until real Home Assistant validation.

- New responsive four-group current-period overview: latest odometer plus current month/year/since-import ODO distance; latest reported fuel consumption, litres bought this month/year, last up-to-two reported consumption mean; actual booked spending this month/year; estimated driving total SEK/km this month/year. Historical month selection changes only the Costs content, not the current overview.
- Selected historic month now displays observed ODO distance, logged TripLog trip count, and mean LOGGED trip length. These two kilometre measures are explicitly different.
- Monthly, yearly and lifetime aggregate attributes add estimated consumed-fuel spending and estimated consumed-fuel/total SEK per ODO-km. For each observed odometer interval, use at most the two most recent positive reported L/100km readings and latest valid price known at its START; the next refuel changes only subsequent intervals. Estimated total = estimated fuel + actual non-fuel expense, never add booked fuel twice. Incomplete fuel-price/consumption coverage yields unavailable period estimates; single-reading fallback is marked limited. Daily timestamp precision and tank mixing remain limitations.
- Existing six booked cash-outlay-per-ODO-km sensors remain separate and keep their established unique IDs/entity IDs (including old `logged_km` slugs). No new sensors: still **36 total**. Existing CostCategories, ZIP path and read-only privacy constraints remain.
- 33 synthetic Python tests and four frontend smoke/regression tests pass on dev, including late refuel does not reprice earlier travel, missing data, one consumption reading and month selector not changing overview. Real HA and Fuelio value comparison required before stable main promotion. Google Drive automatic download is not included.

Upgrade integration in HACS, restart HA, re-copy `/config/custom_components/fuelio/www/ha-fuelio-card.js` to `/config/www/ha-fuelio-card.js`, update the EXISTING single JavaScript resource to `/local/ha-fuelio-card.js?v=0.1.0-beta.8`, and hard-refresh. Keep current YAML, config entry and private ZIP. Check that frontend version says beta.8 and exactly 36 sensors remain. The new estimated cost/km can show — if historical measurements are insufficient; this is intentional, not zero.

''' + notes
notes_file.write_text(notes, encoding='utf-8')
readme_file = root / 'README.md'
readme = readme_file.read_text(encoding='utf-8')
readme = readme.replace('**Beta.6 is a development candidate until the GitHub prerelease is published.**',
                        '**Beta.8 is an experimental prerelease awaiting real Home Assistant validation.**')
readme = readme.replace('`/local/ha-fuelio-card.js?v=0.1.0-beta.6`', '`/local/ha-fuelio-card.js?v=0.1.0-beta.8`')
readme = readme.replace('Development candidate: time-aware estimates and four-panel overview (not released)',
                        'Beta.8: time-aware estimates and four-panel overview (experimental)')
readme_file.write_text(readme, encoding='utf-8')
print('Prepared manifest, card, release notes, docs and smoke-test version for beta.8.')
