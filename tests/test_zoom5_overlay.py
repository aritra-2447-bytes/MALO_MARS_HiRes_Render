import os
import sys
import urllib.request
import threading
import time
import socket

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_dir)
from server.server import MarsHandler, ThreadingServer

# 1. Start test server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(('127.0.0.1', 0))
    test_port = s.getsockname()[1]

httpd = ThreadingServer(('127.0.0.1', test_port), MarsHandler)
server_thread = threading.Thread(target=httpd.serve_forever)
server_thread.daemon = True
server_thread.start()
time.sleep(0.3)

base_url = f"http://127.0.0.1:{test_port}"

# 2. Test live tile access
req = urllib.request.Request(f"{base_url}/zoom_5/15_32.jpg")
with urllib.request.urlopen(req) as resp:
    assert resp.status == 200
    data = resp.read()
    assert len(data) > 0
print(f"PASS: HTTP GET /zoom_5/15_32.jpg returned 200 OK ({len(data)} bytes)")

# 3. Test 4K and 8K texture composites
for tex in ['mars_zoom5_grayscale_4k.jpg', 'mars_zoom5_grayscale_8k.jpg']:
    req = urllib.request.Request(f"{base_url}/textures/{tex}")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = resp.read()
        assert len(data) > 0
    print(f"PASS: HTTP GET /textures/{tex} returned 200 OK ({len(data)} bytes)")

# 4. Test missing tile returns 404 cleanly
try:
    req = urllib.request.Request(f"{base_url}/zoom_5/99_99.jpg")
    with urllib.request.urlopen(req) as resp:
        print("FAIL: Expected 404 for missing tile!")
        sys.exit(1)
except urllib.error.HTTPError as e:
    assert e.code == 404
    print("PASS: HTTP GET /zoom_5/99_99.jpg cleanly returned 404 Not Found")

# 5. Check index.html elements
with open(os.path.join(root_dir, 'public', 'index.html'), 'r', encoding='utf-8') as f:
    html = f.read()

assert 'id="btn-toggle-geo-zoom5"' in html
assert 'id="chk-geo-zoom5-blend"' in html
assert 'id="slider-geo-zoom5"' in html
assert 'id="lbl-geo-zoom5-pct"' in html
assert 'geoZoom5OverlayMesh' in html
assert 'mainZoom5OverlayMesh' in html
assert 'mars_zoom5_grayscale_4k.jpg' in html
print("PASS: All public/index.html UI and Three.js overlay elements verified.")

# 6. Check web_app_2d elements
with open(os.path.join(root_dir, 'web_app_2d', 'index.html'), 'r', encoding='utf-8') as f:
    html_2d = f.read()

assert 'id="layer-zoom5"' in html_2d
assert 'id="zoom5-opacity-slider"' in html_2d
assert 'id="zoom5-opacity-val"' in html_2d
assert 'zoom5Layer' in html_2d
print("PASS: All web_app_2d/index.html UI and Leaflet overlay elements verified.")

print("\nALL AUTOMATED ZOOM_5 VERIFICATIONS PASSED!")
