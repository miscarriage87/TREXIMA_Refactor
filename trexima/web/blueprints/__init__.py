"""
TREXIMA v2.0 - API Blueprints

This package contains all Flask blueprints for the TREXIMA API.
"""

from flask import Blueprint

# Blueprint instances will be imported from their respective modules
# after they are created

__all__ = [
    'auth_bp',
    'projects_bp',
    'files_bp',
    'export_bp',
    'import_bp',
    'admin_bp'
]
