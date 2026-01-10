# -*- mode: python ; coding: utf-8 -*-
# =============================================================================
# TREXIMA PyInstaller Spec File
# Builds standalone Windows executable
# =============================================================================

import os
import sys

block_cipher = None

# Get the directory containing this spec file
SPEC_DIR = os.path.dirname(os.path.abspath(SPECPATH))

a = Analysis(
    ['run_trexima.py'],
    pathex=[SPEC_DIR],
    binaries=[],
    datas=[
        # Required UI assets
        ('appicon.png', '.'),
        ('bg.png', '.'),
        ('done.png', '.'),
        # Include the entire trexima package
        ('trexima', 'trexima'),
    ],
    hiddenimports=[
        # SAP OData client
        'pyodata',
        'pyodata.v2',
        'pyodata.v2.model',
        'pyodata.v2.service',
        # XML parsing
        'bs4',
        'lxml',
        'lxml.etree',
        'lxml._elementpath',
        # Excel
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
        'openpyxl.workbook',
        'openpyxl.worksheet',
        # Localization
        'babel',
        'babel.numbers',
        'babel.dates',
        # GUI
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'ttkthemes',
        'easygui',
        # Utilities
        'dateutil',
        'dateutil.parser',
        # Requests/HTTP
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude web/server modules (not needed for desktop)
        'flask',
        'flask_cors',
        'flask_sqlalchemy',
        'flask_migrate',
        'flask_socketio',
        'gunicorn',
        'gevent',
        'gevent-websocket',
        'eventlet',
        'python-socketio',
        'python-engineio',
        # Exclude cloud/BTP modules
        'sap_xssec',
        'cfenv',
        'boto3',
        'botocore',
        's3transfer',
        # Exclude database modules
        'psycopg2',
        'psycopg2-binary',
        'sqlalchemy',
        'alembic',
        # Exclude test modules
        'pytest',
        'unittest',
        # Exclude dev tools
        'pip',
        'setuptools',
        'wheel',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TREXIMA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress executable (smaller size)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='appicon.png',  # Application icon
)
