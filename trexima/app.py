#!/usr/bin/env python3
"""
TREXIMA Application Entry Point

Run this file to start the TREXIMA application.

Usage:
    python -m trexima.app
    python app.py
"""

import sys
import os

# Ensure the parent directory is in the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trexima.orchestrator import Orchestrator


def main():
    """Main entry point for the application."""
    print("Starting TREXIMA - Translation Export & Import Management Accelerator...")

    try:
        orchestrator = Orchestrator()
        orchestrator.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
