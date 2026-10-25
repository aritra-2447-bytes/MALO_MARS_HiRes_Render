#!/usr/bin/env python3
import sys
import os
import mimetypes

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from server.core.tile_server import translate_path, get_project_dirs

CURRENT_FILE_DIR = os.path.join(PROJECT_ROOT, "server")
DIRS = get_project_dirs(CURRENT_FILE_DIR)
print("DIRS:", DIRS)

result = translate_path("/", DIRS)
print("Root:", result, "exists:", os.path.exists(result))

mime_type, _ = mimetypes.guess_type(result)
print("Mime type:", mime_type)

try:
    with open(result, "rb") as f:
        data = f.read()
    print("File size:", len(data))
except Exception as e:
    print("Error reading file:", e)
