#!/usr/bin/env python3
"""
Mars Unified High-Resolution 3D & 2D Surface Map Server
Optimized for zero-dependency execution locally and on Render.com deployment.

Features:
- Progressive texture pipeline (2K instant preview -> 4K sharp -> 8K master texture)
- Astronaut EVA Route Planner & Minetti Metabolic Cost / Traversability Hazard engine
- Proxies NASA PDS ODE REST API (/live2) for products, browse images & footprints
- Proxies NASA PDS GDS REST API (/livegds) for MOLA PEDR granular altimetry
- Range-request enabled tile server for 2,048 Level 5 tiles & mosaics
- High-precision IAU landmark geodetic dataset
"""

import sys
import os

# Ensure the project root is in sys.path for package imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import http.server
import socketserver
import json
import urllib.parse
import mimetypes

from server.core.handlers import APIHandler
from server.core.tile_server import translate_path, get_project_dirs

def get_port():
    if "PORT" in os.environ:
        try:
            return int(os.environ["PORT"])
        except ValueError:
            pass
    for arg in sys.argv[1:]:
        if arg.isdigit():
            return int(arg)
    return 8083

PORT = get_port()
CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))

# Pre-compute directory paths
DIRS = get_project_dirs(CURRENT_FILE_DIR)

FAVICON_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <circle cx="32" cy="32" r="30" fill="#c1440e"/>
  <ellipse cx="32" cy="30" rx="26" ry="12" fill="#e06c3a" opacity="0.6"/>
  <ellipse cx="32" cy="12" rx="14" ry="4" fill="#ffffff" opacity="0.75"/>
</svg>"""


class MarsHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.api_handler = APIHandler(CURRENT_FILE_DIR)
        super().__init__(*args, directory=DIRS["PUBLIC_DIR"], **kwargs)

    def do_OPTIONS(self):
        # CORS preflight
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        try:
            parsed = urllib.parse.urlsplit(self.path)
            path = parsed.path
            query = urllib.parse.parse_qs(parsed.query)

            # Favicon
            if path in ("/favicon.ico", "/favicon.svg"):
                self.send_response(200)
                self.send_header("Content-Type", "image/svg+xml")
                self.send_header("Content-Length", str(len(FAVICON_SVG)))
                self.send_header("Cache-Control", "public, max-age=86400")
                self.end_headers()
                self.wfile.write(FAVICON_SVG)
                return

            # API Routes
            api_result = self.api_handler.route_request(path, query)
            if api_result is not None:
                # Handle binary stream responses (e.g. NASA browse imagery)
                if isinstance(api_result, dict) and "data" in api_result and isinstance(api_result["data"], bytes):
                    status_code = api_result.get("status_code", 200)
                    mime_type = api_result.get("mime", "image/jpeg")
                    raw_data = api_result["data"]
                    self.send_response(status_code)
                    self.send_header("Content-Type", mime_type)
                    self.send_header("Content-Length", str(len(raw_data)))
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Cache-Control", "public, max-age=86400")
                    self.end_headers()
                    self.wfile.write(raw_data)
                    return

                self.send_json_response(api_result)
                return

            # Static file serving via translate_path
            fs_path = translate_path(path, DIRS)
            if fs_path and os.path.exists(fs_path):
                self.serve_file(fs_path)
                return

            # Fallback to index.html for SPA routing
            if path in ("/", ""):
                fs_path = os.path.join(DIRS["PUBLIC_DIR"], "index.html")
                if os.path.exists(fs_path):
                    self.serve_file(fs_path)
                    return

            self.send_error(404, "Not Found")
        except Exception as e:
            print(f"[ERROR] Exception in do_GET: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            try:
                self.send_error(500, f"Internal Server Error: {e}")
            except:
                pass

    def serve_file(self, fs_path):
        """Serve a file with proper headers and range request support."""
        try:
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(fs_path)
            if mime_type is None:
                mime_type = "application/octet-stream"

            file_size = os.path.getsize(fs_path)

            # Handle Range requests for video/audio/large files
            range_header = self.headers.get("Range")
            if range_header and file_size > 1024 * 1024:  # Only for files > 1MB
                self.handle_range_request(fs_path, file_size, mime_type, range_header)
            else:
                self.send_response(200)
                self.send_header("Content-Type", mime_type)
                self.send_header("Content-Length", str(file_size))
                self.send_header("Cache-Control", "public, max-age=3600")
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                with open(fs_path, "rb") as f:
                    self.wfile.write(f.read())
        except Exception as e:
            self.send_error(500, f"Internal Server Error: {e}")

    def handle_range_request(self, fs_path, file_size, mime_type, range_header):
        """Handle HTTP Range requests for progressive loading."""
        try:
            range_match = range_header.replace("bytes=", "").split("-")
            start = int(range_match[0]) if range_match[0] else 0
            end = int(range_match[1]) if range_match[1] else file_size - 1
            start = max(0, min(start, file_size - 1))
            end = max(start, min(end, file_size - 1))
            content_length = end - start + 1

            self.send_response(206)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(content_length))
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()

            with open(fs_path, "rb") as f:
                f.seek(start)
                remaining = content_length
                while remaining > 0:
                    chunk_size = min(8192, remaining)
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
        except Exception:
            self.send_error(500, "Range Request Error")

    def send_json_response(self, data, status_code=200):
        if isinstance(data, dict) and data.get("status_code"):
            status_code = data.pop("status_code")
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "public, max-age=600")
        self.end_headers()
        self.wfile.write(body)


class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def run():
    print(f"============================================================")
    print(f"  MARS UNIFIED 3D GLOBE & 2D SURFACE MAP ENGINE")
    print(f"  Live NASA ODE (/live2) & GDS (/livegds) Integrated")
    print(f"  Serving on: http://0.0.0.0:{PORT}")
    print(f"  Public Dir: {DIRS['PUBLIC_DIR']}")
    print(f"  Data Dir:   {DIRS['DATA_DIR']}")
    print(f"  Tiles Dir:  {DIRS['TILES_DIR']}")
    print(f"============================================================")
    server = ThreadingServer(("0.0.0.0", PORT), MarsHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Mars Map Server...")
        server.server_close()


if __name__ == "__main__":
    run()