#!/usr/bin/env python3
"""
TREXIMA Launcher Script

Simple launcher for the TREXIMA application.
Run this file to start TREXIMA.
"""

import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from trexima import run_app

if __name__ == "__main__":
    run_app()
