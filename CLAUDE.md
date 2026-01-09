# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TREXIMA (Translation Export & Import Management Accelerator) is a tool for managing translations in SAP SuccessFactors configurations. It extracts translations from SF data models to Excel workbooks and imports updated translations back.

## Architecture

This is a full-stack application with two interfaces:

### Backend (Python/Flask)
```
trexima/
├── config.py              # Configuration classes (AppPaths, AppState, ExportConfig, etc.)
├── orchestrator.py        # Desktop app workflow coordinator (Tkinter callbacks)
├── core/
│   ├── odata_client.py          # SAP SF OData API client
│   ├── datamodel_processor.py   # XML data model parsing
│   ├── translation_extractor.py # Extract translations to Excel
│   └── translation_importer.py  # Import translations from Excel
├── io/
│   ├── xml_handler.py     # XML file operations
│   ├── excel_handler.py   # Excel workbook operations (openpyxl)
│   └── csv_handler.py     # CSV file operations
├── models/                # Data classes (DataModel, TranslationEntry, etc.)
├── ui/                    # Tkinter desktop GUI
└── web/
    ├── app.py             # Flask app factory with WSGI entry point
    ├── models.py          # SQLAlchemy models (User, Project, ProjectFile)
    ├── auth.py            # SAP BTP XSUAA authentication
    ├── storage.py         # S3-compatible Object Store integration
    ├── websocket.py       # Socket.IO for real-time progress
    ├── routes.py          # Legacy API routes
    ├── constants.py       # SF endpoints, EC objects, FO types, locales
    └── blueprints/
        ├── auth_bp.py     # /api/auth endpoints
        ├── projects_bp.py # /api/projects CRUD and file management
        ├── export_bp.py   # /api/projects/{id}/export workflow
        ├── import_bp.py   # /api/projects/{id}/import workflow
        └── admin_bp.py    # /api/admin system management
```

### Frontend (React/TypeScript)
```
trexima-frontend/
└── src/
    ├── api/           # Axios API client with auth interceptors
    ├── store/         # Zustand state management (auth, project stores)
    ├── pages/
    │   ├── LoginPage.tsx    # XSUAA authentication
    │   ├── Dashboard.tsx    # Project list (max 3 projects)
    │   ├── ProjectPage.tsx  # 5-section workflow (files, connection, config, export, import)
    │   └── AdminPage.tsx    # System statistics
    └── components/project/
        ├── FileUploadZone.tsx    # Drag-drop XML upload
        ├── ConnectionConfig.tsx  # SF endpoint configuration
        ├── ExportConfig.tsx      # Locale/object selection (40+ locales, 20+ EC objects)
        ├── ExportSummary.tsx     # Review and start export
        ├── ImportSummary.tsx     # Upload workbook, select worksheets, import
        └── ProgressOverlay.tsx   # Real-time WebSocket progress
```

## Common Commands

### Backend Development
```bash
# Start Flask web server (with WebSocket support)
python run_web.py
python run_web.py --port 8080 --debug

# Start desktop GUI
python run_trexima.py

# Run backend tests
pytest tests/
pytest tests/small/  # Unit tests only
```

### Frontend Development
```bash
cd trexima-frontend

# Development server
npm run dev

# Build for production
npm run build

# Run tests
npm run test
npm run test:watch
npm run test:coverage

# Lint
npm run lint
```

### Database Migrations
```bash
# Initialize migrations (first time only)
flask db init

# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade
```

### Testing
```bash
# Unit tests
pytest tests/

# End-to-end tests (requires SF credentials)
python tests/test_e2e.py        # Small test: 2 data models, 3 languages
python tests/test_max.py        # MAX test: 4 data models, 17 languages

# API connectivity test
python tests/test_api_small.py
```

### Deployment (SAP BTP Cloud Foundry)
```bash
# Deploy to BTP
./deploy.sh

# Create required services
./create-services.sh

# Setup roles
./setup-roles.sh
```

## Key Integration Points

### SAP SuccessFactors OData API
- Authentication via company ID + username + password
- Endpoints configured in `trexima/web/constants.py` (60+ datacenters)
- Client implementation in `trexima/core/odata_client.py`

### Database
- SQLAlchemy with PostgreSQL (production) or SQLite (development)
- Models in `trexima/web/models.py`
- Auto-configured from VCAP_SERVICES on BTP

### File Storage
- S3-compatible Object Store (production) or filesystem (development)
- Implementation in `trexima/web/storage.py`
- Auto-configured from VCAP_SERVICES on BTP

### WebSocket
- Socket.IO for real-time export/import progress
- Implementation in `trexima/web/websocket.py`
- Frontend connects via socket.io-client

## Data Model Types

The application processes four types of SF data models:
- **SDM**: Succession Data Model
- **CDM**: Corporate Data Model
- **CSF-SDM**: Country-Specific Fields for SDM
- **CSF-CDM**: Country-Specific Fields for CDM

## Environment Configuration

Copy `.env.template` to `.env` for local development. Key variables:
- `SECRET_KEY`: Required in production, auto-generated if not set
- `DATABASE_URL`: PostgreSQL connection string (defaults to SQLite)
- `AUTH_ENABLED`: Set to `false` for local development without XSUAA
- `CORS_ORIGINS`: Comma-separated list of allowed origins (defaults to localhost)
- `S3_ACCESS_KEY`, `S3_SECRET_KEY`: Required for S3 storage (optional for development)
- `WORKBOOK_PASSWORD`: Optional password for Excel workbook protection

Production environment is configured via Cloud Foundry manifest (`manifest.yml`) and bound BTP services (PostgreSQL, Object Store, XSUAA).
