#!/usr/bin/env python3
"""
Simple HTTP Server for Mars 2D Level 5 Map Viewer (Leaflet)
"""
import http.server
import socketserver
import sys
import os

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8082
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

PARENT_DIR = os.path.dirname(DIRECTORY)

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def translate_path(self, path):
        clean = path.split('?', 1)[0].split('#', 1)[0]
        if clean.startswith('/zoom_5/'):
            return os.path.join(PARENT_DIR, 'zoom_5', clean[len('/zoom_5/'):])
        if clean.startswith('/tiles/'):
            return os.path.join(PARENT_DIR, 'tiles', clean[len('/tiles/'):])
        if clean.startswith('/sim3292_tiles/'):
            return os.path.join(PARENT_DIR, 'public', 'sim3292_tiles', clean[len('/sim3292_tiles/'):])
        if clean.startswith('/lib/'):
            return os.path.join(PARENT_DIR, 'public', 'lib', clean[len('/lib/'):])
        if clean.startswith('/data/'):
            return os.path.join(PARENT_DIR, 'data', clean[len('/data/'):])
        if clean.startswith('/textures/'):
            return os.path.join(PARENT_DIR, 'public', 'textures', clean[len('/textures/'):])
        return super().translate_path(path)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Mars 2D Level 5 Viewer serving at: http://localhost:{PORT}")
        print(f"Serving directory: {DIRECTORY}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")