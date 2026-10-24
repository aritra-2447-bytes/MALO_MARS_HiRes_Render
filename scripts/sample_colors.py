import json
import os
import sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
data_path = 'data/sim3292_full_analysis.json' if os.path.exists('data/sim3292_full_analysis.json') else 'MALO_MARS_HiRes_Render/data/sim3292_full_analysis.json'
data = json.load(open(data_path, 'r', encoding='utf-8'))
units = data['geologic_units']

palette_hex = [
    '#0089d0', '#009cb2', '#009ccb', '#43a2ae', '#6da69f', '#6e6e6e', '#81adbd', '#8882bd',
    '#8cc63f', '#8d8e82', '#99d4bf', '#9bb4be', '#9fb39f', '#a0a498', '#a62c4e', '#aae1fa',
    '#b27ab5', '#b5aaa6', '#b9875f', '#bda633', '#bdc032', '#c9242c', '#cc7c59', '#cc9e8f',
    '#ccb0a6', '#cd9d81', '#ceae88', '#ccc2bf', '#dcd5d2', '#daf2fd', '#e0b024', '#e9e4d8',
    '#eaccaf', '#eed112', '#f36f23', '#f8aa9e', '#f8956a', '#fabeb7', '#fba61c', '#feeaba',
    '#ffcb06', '#ffd700', '#ffdda3', '#fff100'
]

def hex2rgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)])

pal_rgb = [hex2rgb(h) for h in palette_hex]

print("=== Unit matching to nearest tile palette color ===")
assigned = {}
for u in units:
    u_rgb = hex2rgb(u['color'])
    dists = [np.linalg.norm(u_rgb - p) for p in pal_rgb]
    best_idx = np.argmin(dists)
    best_color = palette_hex[best_idx]
    assigned[u['symbol']] = best_color
    print(f"{u['symbol']:8} curr={u['color']:8} -> tile_pal={best_color:8} dist={dists[best_idx]:.1f} {u['name']}")

# Check if 1-to-1 or duplicates
unique_assigned = set(assigned.values())
print(f"\nUnique assigned palette colors: {len(unique_assigned)} / {len(palette_hex)}")
unassigned = [p for p in palette_hex if p not in unique_assigned]
print(f"Unassigned palette colors ({len(unassigned)}): {unassigned}")
