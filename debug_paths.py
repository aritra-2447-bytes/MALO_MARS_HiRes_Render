#!/usr/bin/env python3
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from server.core.tile_server import translate_path, get_project_dirs

CURRENT_FILE_DIR = os.path.join(PROJECT_ROOT, "server")
DIRS = get_project_dirs(CURRENT_FILE_DIR)

print("Root path:", translate_path("/", DIRS))
print("index.html:", translate_path("/index.html", DIRS))
print("tile:", translate_path("/tiles/5_0_0.jpg", DIRS))
print("favicon:", translate_path("/favicon.svg", DIRS))
print("web_app_2d:", translate_path("/web_app_2d", DIRS))
