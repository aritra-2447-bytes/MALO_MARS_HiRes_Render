import os
import sys
import threading
import time
import socket
import urllib.request
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 65)
print("E2E PLAYWRIGHT HEADLESS BROWSER VERIFICATION")
print("=" * 65)

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_dir)

from server.server import MarsHandler, ThreadingServer

# Bind to ephemeral port
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(("127.0.0.1", 0))
    test_port = s.getsockname()[1]

httpd = ThreadingServer(("127.0.0.1", test_port), MarsHandler)
server_thread = threading.Thread(target=httpd.serve_forever)
server_thread.daemon = True
server_thread.start()
time.sleep(0.3)

base_url = f"http://127.0.0.1:{test_port}"
console_messages = []
console_errors = []

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        def on_console(msg):
            console_messages.append(f"[{msg.type}] {msg.text}")
            if msg.type == 'error':
                console_errors.append(msg.text)

        page.on('console', on_console)

        # ------------------------------------------------------------------
        # 1. Test index.html (3D Map & Rover Traverse Elevation Graph)
        # ------------------------------------------------------------------
        print(f"\n[Test 1] Navigating to {base_url}/ ...")
        page.goto(f"{base_url}/", wait_until="networkidle", timeout=15000)
        time.sleep(1.0) # allow Three.js & route planner to draw

        # Check chart canvas
        chart_canvas = page.locator('#eva-canvas-chart')
        assert chart_canvas.is_visible(), "Canvas #eva-canvas-chart is not visible!"
        bbox = chart_canvas.bounding_box()
        print(f"  Chart bounding box: {bbox}")
        assert bbox and bbox['width'] > 100, f"Chart width too small: {bbox}"
        assert bbox and bbox['height'] > 30, f"Chart height too small: {bbox}"

        # Verify canvas pixel data isn't blank
        is_blank = page.evaluate("""() => {
            const cvs = document.getElementById('eva-canvas-chart');
            const ctx = cvs.getContext('2d');
            const data = ctx.getImageData(0, 0, cvs.width, cvs.height).data;
            for (let i = 3; i < data.length; i += 4) {
                if (data[i] > 0) return false;
            }
            return true;
        }""")
        assert not is_blank, "Canvas #eva-canvas-chart is blank!"
        print("  PASS: Canvas #eva-canvas-chart rendered non-empty graph data!")

        # Check Legend drawer toggle and colors
        page.locator('#btn-menu-toggle').click()
        time.sleep(0.2)
        page.locator('#btn-toggle-geology').click()
        time.sleep(0.2)
        page.locator('#btn-geologic-legend').click()
        time.sleep(0.3)

        legend_drawer = page.locator('#globe-legend-drawer')
        assert legend_drawer.is_visible(), "Legend drawer did not open!"
        print("  PASS: Geological legend drawer opened successfully.")

        # Check swatches in drawer
        swatch_count = page.locator('#globe-legend-drawer .unit-color-box').count()
        print(f"  Found {swatch_count} unit swatch items in legend drawer.")
        assert swatch_count >= 15, "Insufficient swatches in legend drawer!"

        # Verify mNh swatch color in drawer
        mnh_style = page.locator('.legend-unit-item:has-text("mNh") .unit-color-box').get_attribute('style')
        print(f"  mNh swatch style: {mnh_style}")
        assert 'rgb(205, 157, 128)' in mnh_style or '#cd9d80' in mnh_style, f"mNh color incorrect: {mnh_style}"

        # ------------------------------------------------------------------
        # 2. Test geology_atlas.html & Chronology Button
        # ------------------------------------------------------------------
        print(f"\n[Test 2] Navigating to {base_url}/geology_atlas.html ...")
        page.goto(f"{base_url}/geology_atlas.html", wait_until="networkidle", timeout=15000)
        time.sleep(0.5)

        # Check Chronology button
        chronology_btn = page.locator('a:has-text("Chronology (Table.pdf)")')
        assert chronology_btn.is_visible(), "Chronology button not visible in geology_atlas.html!"
        href = chronology_btn.get_attribute('href')
        print(f"  Chronology button href: {href}")
        assert 'Table.pdf' in href, f"Chronology button does not link to Table.pdf: {href}"

        # Click or navigate directly to Table.pdf to verify HTTP download
        with page.expect_response(lambda response: "Table.pdf" in response.url) as response_info:
            page.goto(f"{base_url}/Table.pdf")
        pdf_response = response_info.value
        assert pdf_response.status == 200, f"Table.pdf response status: {pdf_response.status}"
        assert "application/pdf" in pdf_response.headers.get("content-type", ""), "Wrong content-type"
        print(f"  PASS: Table.pdf resolved with status {pdf_response.status} ({pdf_response.headers.get('content-type')})")

        browser.close()

except Exception as e:
    print(f"\nBrowser test failed: {e}")
    if console_errors:
        print("\nBrowser console errors captured:")
        for err in console_errors:
            print("  ", err)
    raise
finally:
    httpd.shutdown()

print("\n" + "=" * 65)
print("E2E PLAYWRIGHT BROWSER VERIFICATION PASSED COMPLETELY!")
print("=" * 65)
