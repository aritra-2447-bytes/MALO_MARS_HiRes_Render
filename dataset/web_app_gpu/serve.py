#!/usr/bin/env python3
"""
High-Performance Multi-Threaded HTTP Server for GPU Accelerated Mars Map Viewer
"""
import http.server
import socketserver
import sys
import os
import urllib.parse

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8083
GPU_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.dirname(GPU_DIR)
WEB_APP_DIR = os.path.join(DATASET_DIR, "web_app")

FAVICON_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <circle cx="32" cy="32" r="30" fill="#c1440e"/>
  <ellipse cx="32" cy="30" rx="26" ry="12" fill="#e06c3a" opacity="0.6"/>
  <ellipse cx="32" cy="12" rx="14" ry="4" fill="#ffffff" opacity="0.75"/>
</svg>"""

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=GPU_DIR, **kwargs)

    def translate_path(self, path):
        # Clean path and unquote
        parsed = urllib.parse.urlsplit(path).path
        clean_path = os.path.normpath(urllib.parse.unquote(parsed))

        # 1. Alias /web_app_gpu/ -> GPU_DIR
        if clean_path == "/web_app_gpu" or clean_path == "\\web_app_gpu":
            return os.path.join(GPU_DIR, "index.html")
        if clean_path.startswith("/web_app_gpu/") or clean_path.startswith("\\web_app_gpu\\"):
            rel = clean_path[len("/web_app_gpu/"):].lstrip("/\\")
            return os.path.join(GPU_DIR, rel)

        # 2. Alias /web_app/ -> WEB_APP_DIR
        if clean_path == "/web_app" or clean_path == "\\web_app":
            return os.path.join(WEB_APP_DIR, "index.html")
        if clean_path.startswith("/web_app/") or clean_path.startswith("\\web_app\\"):
            rel = clean_path[len("/web_app/"):].lstrip("/\\")
            return os.path.join(WEB_APP_DIR, rel)

        # 3. Direct tile requests /5_r_c.jpg or /tiles/5_r_c.jpg
        basename = os.path.basename(clean_path)
        if basename.startswith("5_") and basename.endswith(".jpg"):
            tile_path = os.path.join(DATASET_DIR, basename)
            if os.path.exists(tile_path):
                return tile_path

        # 4. Mosaic requests: check web_app_gpu first, then fallback to web_app
        if basename == "mars_mola_level5_mosaic.jpg":
            gpu_mosaic = os.path.join(GPU_DIR, "mars_mola_level5_mosaic.jpg")
            if os.path.exists(gpu_mosaic):
                return gpu_mosaic
            orig_mosaic = os.path.join(WEB_APP_DIR, "mars_mola_level5_mosaic.jpg")
            if os.path.exists(orig_mosaic):
                return orig_mosaic

        # Default handling relative to GPU_DIR
        return super().translate_path(path)

    def do_GET(self):
        # Serve favicon directly to prevent 404 errors in browser consoles
        if self.path in ("/favicon.ico", "/favicon.svg"):
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Content-Length", str(len(FAVICON_SVG)))
            self.send_header("Cache-Control", "public, max-age=86400")
            self.end_headers()
            self.wfile.write(FAVICON_SVG)
            return

        # Redirect bare directory paths
        if self.path in ("/web_app_gpu", "/web_app_gpu/"):
            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
            return
        if self.path == "/web_app":
            self.send_response(302)
            self.send_header("Location", "/web_app/")
            self.end_headers()
            return

        super().do_GET()

    def do_HEAD(self):
        if self.path in ("/favicon.ico", "/favicon.svg"):
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Content-Length", str(len(FAVICON_SVG)))
            self.send_header("Cache-Control", "public, max-age=86400")
            self.end_headers()
            return
        super().do_HEAD()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

if __name__ == '__main__':
    with ThreadingHTTPServer(("", PORT), Handler) as httpd:
        print(f"Mars GPU Accelerated Explorer serving at: http://localhost:{PORT}")
        print(f"Serving directory: {GPU_DIR}")
        print(f"Dataset root: {DATASET_DIR}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
