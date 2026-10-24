import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

urls = [
    'https://trek.nasa.gov/mars/trekarcgis/rest/services/SIM3292_Global_Geology/MapServer/legend?f=pjson',
    'https://trek.nasa.gov/mars/trekarcgis/rest/services/SIM3292_Global_Geology/MapServer/layers?f=pjson',
    'https://trek.nasa.gov/mars/trekarcgis/rest/services/SIM3292_Global_Geology/MapServer?f=pjson'
]

for url in urls:
    print("Testing:", url)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print("Success! Keys:", list(data.keys()))
            if 'layers' in data:
                print("Layers:", len(data['layers']))
                for l in data['layers'][:5]:
                    print("  Layer:", l.get('layerName') or l.get('name'))
                    if 'legend' in l:
                        print("    Legend items:", len(l['legend']))
                        for it in l['legend'][:5]:
                            print("     ", it.get('label'), it.get('values'))
            with open('data/trek_legend.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            break
    except Exception as e:
        print("Failed:", e)
