import json
import base64
import io
import sys
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

trek_data = json.load(open('data/trek_legend.json', 'r', encoding='utf-8'))
legend = trek_data['layers'][0]['legend']

units_data = json.load(open('data/sim3292_full_analysis.json', 'r', encoding='utf-8'))
units = units_data['geologic_units']
units_by_name = {u['name'].strip().lower(): u for u in units}

# Also handle common aliases
name_aliases = {
    'amazonian and hesperian volcanic': 'amazonian and hesperian volcanic',
    'amazonian volcanic edifice': 'amazonian volcanic edifice'
}

print(f"Total legend items: {len(legend)}")
results = []
for item in legend:
    label = item['label'].strip()
    img_bytes = base64.b64decode(item['imageData'])
    img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
    
    # get center pixel or dominant color
    colors = img.getcolors(maxcolors=1000)
    # sort by count
    colors.sort(key=lambda x: x[0], reverse=True)
    dom_count, dom_rgb = colors[0]
    hex_color = f"#{dom_rgb[0]:02x}{dom_rgb[1]:02x}{dom_rgb[2]:02x}"
    
    matched_unit = units_by_name.get(label.lower())
    sym = matched_unit['symbol'] if matched_unit else '??'
    
    results.append({
        'symbol': sym,
        'label': label,
        'hex': hex_color,
        'rgb': list(dom_rgb)
    })
    print(f"{sym:8} | {hex_color} | {label}")

with open('data/legend_44_exact.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

print("\nSaved exact 44 legend items to data/legend_44_exact.json")
