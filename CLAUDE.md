# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TREXIMA (Translation Export & Import Management Accelerator) is a tool for managing translations in SAP SuccessFactors configurations. It extracts translations from SF data models to Excel workbooks and imports updated translations back.

## Architecture

Full-stack application with two interfaces:

### Backend (Python 3.9+ / Flask)
- **Entry points**: `run_web.py` (Flask server), `run_trexima.py` (Tkinter desktop GUI)
- **Core processing**: `trexima/core/` - OData client, XML parsing, translation extraction/import
- **Web layer**: `trexima/web/` - Flask blueprints, SQLAlchemy models, S3 storage, WebSocket
- **Desktop GUI**: `trexima/ui/` - Tkinter interface with `trexima/orchestrator.py` as workflow coordinator

### Frontend (React 19 / TypeScript / Vite)
- **State**: Zustand stores in `src/store/`
- **API**: Axios client with auth interceptors in `src/api/`
- **Pages**: Dashboard (max 3 projects), ProjectPage (5-section workflow), AdminPage
- **Real-time**: Socket.IO for export/import progress

## Common Commands

### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Start Flask server (port 5000 default)
python run_web.py
python run_web.py --port 8080 --debug

# Start desktop GUI
python run_trexima.py

# Run all backend tests
pytest tests/

# Run specific test file
pytest tests/small/test_export_api.py -v

# Run single test function
pytest tests/small/test_export_api.py::test_function_name -v

# E2E tests (requires SF credentials)
python tests/test_e2e.py        # 2 data models, 3 languages
python tests/test_max.py        # 4 data models, 17 languages
```

### Frontend
```bash
cd trexima-frontend

# Install and run dev server (Vite, port 5173)
npm install
npm run dev

# Build
npm run build

# Tests (Vitest)
npm run test              # Single run
npm run test:watch        # Watch mode
npm run test:coverage     # With coverage

# Lint
npm run lint
```

### Database Migrations
```bash
flask db migrate -m "Description"
flask db upgrade
```

### Deployment (SAP BTP Cloud Foundry)
```bash
./deploy.sh           # Deploy to BTP
./create-services.sh  # Create required services
./setup-roles.sh      # Setup XSUAA roles
```

## Key Integration Points

### SAP SuccessFactors OData API
- Auth: company ID + username + password
- 60+ datacenter endpoints in `trexima/web/constants.py`
- Client: `trexima/core/odata_client.py`

### BTP Services (auto-configured from VCAP_SERVICES)
- **Database**: PostgreSQL (prod) / SQLite (dev) - models in `trexima/web/models.py`
- **Storage**: S3-compatible Object Store - `trexima/web/storage.py`
- **Auth**: XSUAA - `trexima/web/auth.py`

### WebSocket
- Socket.IO for real-time progress updates
- Server: `trexima/web/websocket.py`
- Client: socket.io-client

## Data Model Types

- **SDM**: Succession Data Model
- **CDM**: Corporate Data Model
- **CSF-SDM/CSF-CDM**: Country-Specific Fields

## Environment Setup

Copy `.env.template` to `.env` for local development:
- `AUTH_ENABLED=false` - Disable XSUAA for local dev
- `DATABASE_URL` - Defaults to SQLite
- `CORS_ORIGINS` - Frontend origins (localhost:3000, localhost:5173)

## Test Fixtures

Backend tests use pytest fixtures in `tests/conftest.py`:
- `app` - Flask test app with in-memory SQLite
- `client` - Test client
- `mock_user`, `mock_admin_user` - User fixtures
- `mock_project` - Project fixture
- `mock_storage`, `mock_socketio` - Service mocks
