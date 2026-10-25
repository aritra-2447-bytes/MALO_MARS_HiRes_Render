import json
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Backup
shutil.copy('data/sim3292_full_analysis.json', 'data/sim3292_full_analysis.json.bak')
print("Backed up sim3292_full_analysis.json -> sim3292_full_analysis.json.bak")

exact = json.load(open('data/legend_44_exact.json', 'r', encoding='utf-8'))
exact_map = {e['symbol']: e for e in exact}

analysis = json.load(open('data/sim3292_full_analysis.json', 'r', encoding='utf-8'))
for unit in analysis['geologic_units']:
    sym = unit['symbol']
    if sym in exact_map:
        old_c = unit.get('color')
        new_c = exact_map[sym]['hex']
        unit['color'] = new_c
        print(f"Updated {sym:6}: {old_c} -> {new_c} ({unit['name']})")

with open('data/sim3292_full_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(analysis, f, indent=2)

print("\nsim3292_full_analysis.json successfully updated with exact tile colors.")
