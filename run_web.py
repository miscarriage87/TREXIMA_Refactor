#!/usr/bin/env python3
"""
TREXIMA Web Application Launcher

Run this file to start the TREXIMA web interface.

Usage:
    python run_web.py
    python run_web.py --port 8080
    python run_web.py --debug
"""

# IMPORTANT: Eventlet monkey-patching must happen BEFORE any other imports
# This ensures all standard library modules (socket, threading, etc.) are patched
# to work cooperatively with eventlet's green threads
import eventlet
eventlet.monkey_patch()

import sys
import os
import argparse

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from trexima.web.app import run_web_app


def main():
    parser = argparse.ArgumentParser(
        description='TREXIMA Web Application'
    )
    parser.add_argument(
        '--host',
        default=os.environ.get('HOST', '0.0.0.0'),
        help='Host to bind to (default: 0.0.0.0 or $HOST)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=int(os.environ.get('PORT', '5000')),
        help='Port to listen on (default: 5000 or $PORT)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        default=os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes'),
        help='Enable debug mode'
    )

    args = parser.parse_args()

    run_web_app(
        host=args.host,
        port=args.port,
        debug=args.debug
    )


if __name__ == '__main__':
    main()
