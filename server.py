#!/usr/bin/env python3
"""
Mars Unified High-Resolution 3D & 2D Surface Map Server
Root entrypoint for local execution and Render.com deployment.
"""
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from server.server import run

if __name__ == "__main__":
    run()
