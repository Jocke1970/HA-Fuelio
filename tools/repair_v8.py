"""Update the one-time patch to match the final released beta.7 frontend."""
from pathlib import Path
file = Path(__file__).with_name('apply_v8.py')
s = file.read_text(encoding='utf-8')
old = '${odoNote}`)}'
new = '${odoNote(nowMonth)}`)}'
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new, 1)
old = '["Körsträcka denna månad", decimal(nowMonth?.km, "km"), odoNote],'
new = '["Körsträcka denna månad", decimal(nowMonth?.km, "km"), odoNote(nowMonth)],'
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new, 1)
file.write_text(s, encoding='utf-8')
print('Adjusted beta.7 frontend anchor and ODO date helper.')
