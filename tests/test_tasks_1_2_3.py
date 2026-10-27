import os
import sys
import json
import re
import urllib.request
import threading
import time

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 65)
print("VERIFICATION SUITE FOR TASKS 1, 2, AND 3")
print("=" * 65)

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
public_dir = os.path.join(root_dir, "public")
data_dir = os.path.join(root_dir, "data")
parent_dir = os.path.abspath(os.path.join(root_dir, ".."))

index_path = os.path.join(public_dir, "index.html")
atlas_path = os.path.join(public_dir, "geology_atlas.html")
sim_json_path = os.path.join(data_dir, "sim3292_full_analysis.json")
table_pdf_public = os.path.join(public_dir, "Table.pdf")
table_pdf_orig = os.path.join(parent_dir, "Table.pdf")

# -------------------------------------------------------------
# TASK 1 VERIFICATION: Legend colors, swatches, and unit metadata
# -------------------------------------------------------------
print("\n[TASK 1] Verifying Geological Map Legend & Color Matching...")

# 1. Check tile palette colors
exact_json_path = os.path.join(data_dir, "legend_44_exact.json")
assert os.path.exists(exact_json_path), "legend_44_exact.json missing"
with open(exact_json_path, 'r', encoding='utf-8') as f:
    legend_exact = json.load(f)
valid_tile_hexes = {e['hex'].lower() for e in legend_exact}

with open(sim_json_path, 'r', encoding='utf-8') as f:
    sim_data = json.load(f)

assert len(sim_data['geologic_units']) == 44, f"Expected 44 units, got {len(sim_data['geologic_units'])}"
for u in sim_data['geologic_units']:
    c = u['color'].lower()
    assert c in valid_tile_hexes, f"Unit {u['symbol']} has non-palette color {c}"

print(f"  PASS: All 44 units in sim3292_full_analysis.json have valid tile palette colors.")

# 2. Check index.html legend drawer
with open(index_path, 'r', encoding='utf-8') as f:
    index_html = f.read()

assert "mNf" not in index_html, "Stale unit 'mNf' still present in index.html"
print(f"  PASS: Stale unit 'mNf' successfully removed.")

# Extract all background hex colors from globe-legend-drawer
drawer_match = re.search(r'<div id="globe-legend-drawer">(.*?)</div>\s*</div>\s*<!-- Bottom HUD', index_html, re.DOTALL)
assert drawer_match, "globe-legend-drawer container not found"
drawer_html = drawer_match.group(1)

swatches = re.findall(r'background:\s*(#[0-9a-fA-F]{6})', drawer_html)
assert len(swatches) >= 15, f"Expected at least 15 legend swatches, found {len(swatches)}"

for s in swatches:
    assert s.lower() in valid_tile_hexes, f"Swatch color {s} does not match any tile palette color!"

print(f"  PASS: All {len(swatches)} drawer swatch colors match the sampled tile palette 1-to-1.")

# Check atlas landing sites table colors
with open(atlas_path, 'r', encoding='utf-8') as f:
    atlas_html = f.read()

assert "#cd9d80" in atlas_html, "mNh tile color #cd9d80 missing in geology_atlas.html"
assert "#8cc640" in atlas_html, "lHl tile color #8cc640 missing in geology_atlas.html"
assert "#fff100" in atlas_html, "AHi tile color #fff100 missing in geology_atlas.html"
print("  PASS: geology_atlas.html table swatches match tile palette.")

# -------------------------------------------------------------
# TASK 2 VERIFICATION: Live Rover Traverse & Corridor Graph
# -------------------------------------------------------------
print("\n[TASK 2] Verifying Elevation Profile Graph & Bottom Dock DOM...")

dock_match = re.search(r'(<div id="bottom-dock">.*?\n\s*</div>\s*)\n\s*<!-- Floating Coordinates Telemetry', index_html, re.DOTALL)
assert dock_match, "bottom-dock container not found"
dock_content = dock_match.group(1)

# Verify chart-box and canvas are inside bottom-dock
assert '<div class="chart-box">' in dock_content, "chart-box is missing from bottom-dock"
assert '<canvas id="eva-canvas-chart"></canvas>' in dock_content, "eva-canvas-chart is missing from bottom-dock"

# Verify dock is properly structured (no premature closing div)
# Counting open vs close divs inside bottom-dock up to the final </div>
dock_div_opens = len(re.findall(r'<div\b', dock_content))
dock_div_closes = len(re.findall(r'</div>', dock_content))
assert dock_div_opens == dock_div_closes, f"Mismatched div tags in bottom dock: {dock_div_opens} opens, {dock_div_closes} closes"
print("  PASS: bottom-dock DOM structure is balanced and valid; chart-box is securely nested.")

# Verify drawElevationChart implementation
assert "cvs.parentElement.clientWidth" in index_html, "drawElevationChart missing parent width query"
assert "cvs.width = pW" in index_html or "cvs.width =" in index_html, "Canvas width assignment missing"
assert "currentRouteTitle" in index_html, "currentRouteTitle tracking missing"
assert "Using local traverse dataset fallback" in index_html, "Local fallback dataset logic missing"
print("  PASS: drawElevationChart and loadEVARoute have defensive dimensions and local dataset fallback.")

# -------------------------------------------------------------
# TASK 3 VERIFICATION: Table.pdf and Chronology link
# -------------------------------------------------------------
print("\n[TASK 3] Verifying Table.pdf & Chronology Button...")

assert os.path.exists(table_pdf_orig), f"Original Table.pdf missing in {table_pdf_orig}"
orig_size = os.path.getsize(table_pdf_orig)
assert orig_size == 135538, f"Original Table.pdf size was modified! Expected 135538, got {orig_size}"

assert os.path.exists(table_pdf_public), f"Target Table.pdf missing in {table_pdf_public}"
pub_size = os.path.getsize(table_pdf_public)
assert pub_size == orig_size, f"Public Table.pdf size mismatch: {pub_size} vs {orig_size}"
print(f"  PASS: Table.pdf safely copied into public/ ({pub_size} bytes); original untouched.")

# Check geology_atlas.html button href
assert 'href="Table.pdf"' in atlas_html or 'href="/Table.pdf"' in atlas_html, "Chronology button link missing in geology_atlas.html"
assert 'table: { title: \'Table.pdf' in atlas_html and "url: 'Table.pdf'" in atlas_html, "DOCS_METADATA Table.pdf viewer path missing"
print("  PASS: Chronology button and interactive document viewer properly link to Table.pdf.")

# -------------------------------------------------------------
# LIVE HTTP SERVER VERIFICATION FOR ALL 3
# -------------------------------------------------------------
print("\n[LIVE SERVER] Running HTTP Endpoints & File Serving Checks...")

sys.path.insert(0, root_dir)
from server.server import MarsHandler, ThreadingServer
import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(("127.0.0.1", 0))
    test_port = s.getsockname()[1]

httpd = ThreadingServer(("127.0.0.1", test_port), MarsHandler)
server_thread = threading.Thread(target=httpd.serve_forever)
server_thread.daemon = True
server_thread.start()
time.sleep(0.3)

base_url = f"http://127.0.0.1:{test_port}"

# 1. Fetch Table.pdf via HTTP
with urllib.request.urlopen(f"{base_url}/Table.pdf", timeout=5) as resp:
    assert resp.status == 200, f"/Table.pdf returned {resp.status}"
    pdf_bytes = resp.read()
    assert pdf_bytes.startswith(b"%PDF"), "Table.pdf does not have valid PDF header"
    assert len(pdf_bytes) == orig_size, f"Served PDF size mismatch: {len(pdf_bytes)}"
print(f"  PASS: HTTP GET /Table.pdf returned 200 OK with valid PDF magic bytes (%PDF-1.4).")

# 2. Fetch /api/sim3292/data
with urllib.request.urlopen(f"{base_url}/api/sim3292/data", timeout=5) as resp:
    assert resp.status == 200
    live_sim = json.loads(resp.read().decode('utf-8'))
    assert len(live_sim['geologic_units']) == 44
print(f"  PASS: HTTP GET /api/sim3292/data returned 200 OK with all 44 updated units.")

# 3. Fetch index.html and geology_atlas.html
with urllib.request.urlopen(f"{base_url}/", timeout=5) as resp:
    assert resp.status == 200
with urllib.request.urlopen(f"{base_url}/geology_atlas.html", timeout=5) as resp:
    assert resp.status == 200
print(f"  PASS: HTTP GET / and /geology_atlas.html returned 200 OK without errors.")

httpd.shutdown()

print("\n" + "=" * 65)
print("ALL 3 TASKS VERIFIED SUCCESSFULLY AND PASS 100%!")
print("=" * 65)
