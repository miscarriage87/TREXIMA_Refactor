# TREXIMA v4.0 - Comprehensive Planning Document

## Executive Summary

This document describes the complete transformation of TREXIMA from a basic web application to an enterprise-grade, multi-user platform with project management, persistent storage, and a modern React-based single-page application (SPA) frontend.

**Target Audience**: This document is designed to be consumed by Claude (Sonnet 4.5 or Opus) for implementation guidance.

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Target Architecture](#2-target-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Authentication & Authorization](#4-authentication--authorization)
5. [Database Schema](#5-database-schema)
6. [Object Storage Structure](#6-object-storage-structure)
7. [API Design](#7-api-design)
8. [WebSocket Events](#8-websocket-events)
9. [Frontend Architecture](#9-frontend-architecture)
10. [UI/UX Specifications](#10-uiux-specifications)
11. [SuccessFactors API Endpoints](#11-successfactors-api-endpoints)
12. [ODATA Object Categories](#12-odata-object-categories)
13. [Implementation Tasks](#13-implementation-tasks)
14. [Security Considerations](#14-security-considerations)
15. [Deployment Configuration](#15-deployment-configuration)
16. [Testing Strategy](#16-testing-strategy)

---

## 1. Current State Analysis

### 1.1 Existing Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Current TREXIMA v3.0                 │
├─────────────────────────────────────────────────────────┤
│  Frontend: Vanilla JS + Jinja2 Templates                │
│  Backend: Flask (single process, no persistence)        │
│  Storage: Temporary files only (lost on restart)        │
│  Auth: None                                             │
│  State: In-memory globals in routes.py                  │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Key Limitations

- No user authentication
- No persistent storage (files lost on app restart)
- Single-user design (global state conflicts)
- No project management
- Basic UI without real-time updates
- No admin capabilities

---

## 2. Target Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         TREXIMA v4.0 Architecture                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────┐ │
│  │   Browser    │────▶│   React SPA  │────▶│   WebSocket Connection   │ │
│  │   (Client)   │     │   (Vite)     │     │   (Real-time updates)    │ │
│  └──────────────┘     └──────────────┘     └──────────────────────────┘ │
│         │                    │                         │                 │
│         ▼                    ▼                         ▼                 │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     Flask Backend (API)                           │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │   │
│  │  │   Auth     │  │  Projects  │  │  Export    │  │  Import    │  │   │
│  │  │  Blueprint │  │  Blueprint │  │  Blueprint │  │  Blueprint │  │   │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐                  │   │
│  │  │   Admin    │  │  WebSocket │  │  Storage   │                  │   │
│  │  │  Blueprint │  │  Handler   │  │  Service   │                  │   │
│  │  └────────────┘  └────────────┘  └────────────┘                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│         │                    │                         │                 │
│         ▼                    ▼                         ▼                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────┐ │
│  │  SAP BTP     │     │  PostgreSQL  │     │   Object Store           │ │
│  │  XSUAA       │     │  (Metadata)  │     │   (Files)                │ │
│  └──────────────┘     └──────────────┘     └──────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| React SPA | User interface, state management, WebSocket client |
| Flask API | REST endpoints, business logic orchestration |
| WebSocket | Real-time progress updates, notifications |
| XSUAA | Authentication, token validation |
| PostgreSQL | User data, project metadata, configuration |
| Object Store | XML files, Excel workbooks, generated outputs |

---

## 3. Technology Stack

### 3.1 Backend Additions

```python
# requirements.txt additions
flask-socketio>=5.3.0      # WebSocket support
flask-sqlalchemy>=3.1.0    # ORM for PostgreSQL
psycopg2-binary>=2.9.0     # PostgreSQL driver
cfenv>=0.5.3               # Cloud Foundry environment parsing
sap-xssec>=4.0.0           # XSUAA token validation
python-jose>=3.3.0         # JWT handling
boto3>=1.28.0              # S3-compatible Object Store client
gevent>=23.0.0             # Async worker for WebSocket
gevent-websocket>=0.10.1   # WebSocket transport
```

### 3.2 Frontend Stack

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "zustand": "^4.4.0",
    "@tanstack/react-query": "^5.0.0",
    "socket.io-client": "^4.7.0",
    "axios": "^1.6.0",
    "react-dropzone": "^14.2.0",
    "lucide-react": "^0.292.0",
    "tailwindcss": "^3.3.0",
    "clsx": "^2.0.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.0"
  }
}
```

### 3.3 BTP Services Required

| Service | Purpose | Plan |
|---------|---------|------|
| XSUAA | Authentication | application |
| PostgreSQL | Database | trial or standard |
| Object Store | File storage | s3-standard |

---

## 4. Authentication & Authorization

### 4.1 XSUAA Integration Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  User    │────▶│  React   │────▶│  XSUAA   │────▶│  Flask   │
│  Browser │     │  App     │     │  OAuth2  │     │  Backend │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                │                │
     │  1. Access App │                │                │
     │───────────────▶│                │                │
     │                │  2. Redirect   │                │
     │                │  to XSUAA      │                │
     │                │───────────────▶│                │
     │  3. Login Page │                │                │
     │◀───────────────────────────────│                │
     │  4. Credentials│                │                │
     │───────────────────────────────▶│                │
     │                │  5. Auth Code  │                │
     │                │◀───────────────│                │
     │                │  6. Exchange   │                │
     │                │  for Token     │                │
     │                │───────────────▶│                │
     │                │  7. JWT Token  │                │
     │                │◀───────────────│                │
     │                │                │  8. API Call   │
     │                │                │  with Token    │
     │                │────────────────────────────────▶│
     │                │                │  9. Validate   │
     │                │                │  Token         │
     │                │                │◀──────────────▶│
     │                │                │  10. Response  │
     │                │◀────────────────────────────────│
```

### 4.2 User Roles

| Role | Scope | Capabilities |
|------|-------|--------------|
| `user` | Standard | Create/manage own projects (max 3), export/import |
| `admin` | Administrator | View/manage all users and projects, system settings |

### 4.3 xs-security.json Configuration

```json
{
  "xsappname": "trexima",
  "tenant-mode": "dedicated",
  "scopes": [
    { "name": "$XSAPPNAME.user", "description": "Standard user access" },
    { "name": "$XSAPPNAME.admin", "description": "Administrator access" }
  ],
  "role-templates": [
    {
      "name": "User",
      "description": "Standard TREXIMA user",
      "scope-references": ["$XSAPPNAME.user"]
    },
    {
      "name": "Admin",
      "description": "TREXIMA administrator",
      "scope-references": ["$XSAPPNAME.user", "$XSAPPNAME.admin"]
    }
  ],
  "role-collections": [
    {
      "name": "TREXIMA_User",
      "role-template-references": ["$XSAPPNAME.User"]
    },
    {
      "name": "TREXIMA_Admin",
      "role-template-references": ["$XSAPPNAME.Admin"]
    }
  ],
  "oauth2-configuration": {
    "redirect-uris": ["https://*.cfapps.*.hana.ondemand.com/**"]
  }
}
```

### 4.4 Backend Token Validation

```python
# trexima/web/auth.py
from functools import wraps
from flask import request, jsonify, g
from sap import xssec
import os

def get_xsuaa_service():
    """Get XSUAA service credentials from VCAP_SERVICES."""
    vcap = json.loads(os.environ.get('VCAP_SERVICES', '{}'))
    return vcap.get('xsuaa', [{}])[0].get('credentials', {})

def require_auth(f):
    """Decorator to require valid JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing authorization token'}), 401

        token = auth_header[7:]
        xsuaa_creds = get_xsuaa_service()

        try:
            security_context = xssec.create_security_context(token, xsuaa_creds)
            g.user_id = security_context.get_logon_name()
            g.user_email = security_context.get_email()
            g.is_admin = security_context.check_scope(f"{xsuaa_creds['xsappname']}.admin")
        except Exception as e:
            return jsonify({'error': 'Invalid token', 'details': str(e)}), 401

        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    """Decorator to require admin scope."""
    @wraps(f)
    @require_auth
    def decorated(*args, **kwargs):
        if not g.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated
```

---

## 5. Database Schema

### 5.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PostgreSQL Schema                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐         ┌──────────────────────┐                  │
│  │    users     │         │      projects        │                  │
│  ├──────────────┤         ├──────────────────────┤                  │
│  │ id (PK)      │────────▶│ id (PK)              │                  │
│  │ xsuaa_id     │         │ user_id (FK)         │                  │
│  │ email        │         │ name                 │                  │
│  │ display_name │         │ description          │                  │
│  │ is_admin     │         │ status               │                  │
│  │ created_at   │         │ config (JSONB)       │                  │
│  │ last_login   │         │ created_at           │                  │
│  └──────────────┘         │ updated_at           │                  │
│                           │ last_accessed_at     │                  │
│                           └──────────────────────┘                  │
│                                    │                                 │
│                                    │                                 │
│                           ┌────────┴────────┐                       │
│                           ▼                 ▼                       │
│              ┌──────────────────┐  ┌──────────────────┐             │
│              │  project_files   │  │ generated_files  │             │
│              ├──────────────────┤  ├──────────────────┤             │
│              │ id (PK)          │  │ id (PK)          │             │
│              │ project_id (FK)  │  │ project_id (FK)  │             │
│              │ file_type        │  │ file_type        │             │
│              │ original_name    │  │ filename         │             │
│              │ storage_key      │  │ storage_key      │             │
│              │ file_size        │  │ file_size        │             │
│              │ uploaded_at      │  │ created_at       │             │
│              └──────────────────┘  │ expires_at       │             │
│                                    │ downloaded_count │             │
│                                    └──────────────────┘             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 SQLAlchemy Models

```python
# trexima/web/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import uuid

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    xsuaa_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

    projects = db.relationship('Project', backref='owner', lazy='dynamic',
                               cascade='all, delete-orphan')

    MAX_PROJECTS = 3  # Hard-coded limit

class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='draft')  # draft, configured, exported, imported
    config = db.Column(db.JSON, default=dict)  # Stores all project configuration
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed_at = db.Column(db.DateTime, default=datetime.utcnow)

    files = db.relationship('ProjectFile', backref='project', lazy='dynamic',
                           cascade='all, delete-orphan')
    generated_files = db.relationship('GeneratedFile', backref='project', lazy='dynamic',
                                      cascade='all, delete-orphan')

class ProjectFile(db.Model):
    __tablename__ = 'project_files'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False, index=True)
    file_type = db.Column(db.String(50), nullable=False)  # sdm, cdm, ec_sdm, ec_cdm, picklist
    original_name = db.Column(db.String(255), nullable=False)
    storage_key = db.Column(db.String(512), nullable=False)  # Object Store key
    file_size = db.Column(db.BigInteger)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class GeneratedFile(db.Model):
    __tablename__ = 'generated_files'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False, index=True)
    file_type = db.Column(db.String(50), nullable=False)  # workbook, xml_sdm, xml_cdm, etc.
    filename = db.Column(db.String(255), nullable=False)
    storage_key = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.BigInteger)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=90))
    downloaded_count = db.Column(db.Integer, default=0)

# Project configuration JSON structure
PROJECT_CONFIG_SCHEMA = {
    "sf_connection": {
        "endpoint_url": str,      # Selected SF API endpoint
        "company_id": str,
        "username": str,
        "password": str,          # Encrypted
        "connected": bool,
        "last_connected_at": str
    },
    "languages": {
        "selected": list,         # List of locale codes
        "available": list         # Discovered from instance
    },
    "odata_objects": {
        "ec_fields": list,        # Selected EC field objects
        "foundation_objects": list,
        "mdf_objects": list,
        "picklists": {
            "legacy": list,
            "mdf": list
        }
    },
    "fo_translations": list,      # Selected FO translation types
    "export_options": {
        "include_empty": bool,
        "sheet_per_model": bool
    },
    "last_saved_at": str
}
```

---

## 6. Object Storage Structure

### 6.1 Bucket Organization

```
trexima-storage/
├── users/
│   └── {user_id}/
│       └── projects/
│           └── {project_id}/
│               ├── uploads/
│               │   ├── sdm_{timestamp}_{original_name}.xml
│               │   ├── cdm_{timestamp}_{original_name}.xml
│               │   ├── ec_sdm_{timestamp}_{original_name}.xml
│               │   ├── ec_cdm_{timestamp}_{original_name}.xml
│               │   └── picklist_{timestamp}_{original_name}.csv
│               └── generated/
│                   ├── workbook_{timestamp}.xlsx
│                   ├── import_sdm_{timestamp}.xml
│                   ├── import_cdm_{timestamp}.xml
│                   └── import_picklist_{timestamp}.csv
└── temp/
    └── {session_id}/
        └── {temporary_files}
```

### 6.2 Storage Service Implementation

```python
# trexima/web/storage.py
import boto3
from botocore.config import Config
import os
import json
from datetime import datetime

class ObjectStorageService:
    def __init__(self):
        vcap = json.loads(os.environ.get('VCAP_SERVICES', '{}'))
        objectstore = vcap.get('objectstore', [{}])[0].get('credentials', {})

        self.bucket = objectstore.get('bucket')
        self.client = boto3.client(
            's3',
            endpoint_url=objectstore.get('host'),
            aws_access_key_id=objectstore.get('access_key_id'),
            aws_secret_access_key=objectstore.get('secret_access_key'),
            region_name=objectstore.get('region', 'us-east-1'),
            config=Config(signature_version='s3v4')
        )

    def upload_file(self, file_obj, key: str, content_type: str = None) -> dict:
        """Upload a file to Object Store."""
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type

        self.client.upload_fileobj(file_obj, self.bucket, key, ExtraArgs=extra_args)

        # Get file size
        response = self.client.head_object(Bucket=self.bucket, Key=key)
        return {
            'key': key,
            'size': response['ContentLength'],
            'etag': response['ETag']
        }

    def download_file(self, key: str) -> bytes:
        """Download a file from Object Store."""
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response['Body'].read()

    def get_download_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a pre-signed download URL."""
        return self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': key},
            ExpiresIn=expires_in
        )

    def delete_file(self, key: str):
        """Delete a file from Object Store."""
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def delete_prefix(self, prefix: str):
        """Delete all files with a given prefix."""
        paginator = self.client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            if 'Contents' in page:
                objects = [{'Key': obj['Key']} for obj in page['Contents']]
                self.client.delete_objects(
                    Bucket=self.bucket,
                    Delete={'Objects': objects}
                )

    def generate_key(self, user_id: str, project_id: str,
                     category: str, file_type: str, original_name: str) -> str:
        """Generate a storage key for a file."""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        safe_name = original_name.replace(' ', '_')
        return f"users/{user_id}/projects/{project_id}/{category}/{file_type}_{timestamp}_{safe_name}"
```

---

## 7. API Design

### 7.1 API Endpoint Overview

| Category | Method | Endpoint | Description |
|----------|--------|----------|-------------|
| **Auth** | GET | `/api/auth/user` | Get current user info |
| **Auth** | POST | `/api/auth/logout` | Logout (clear session) |
| **Projects** | GET | `/api/projects` | List user's projects |
| **Projects** | POST | `/api/projects` | Create new project |
| **Projects** | GET | `/api/projects/{id}` | Get project details |
| **Projects** | PUT | `/api/projects/{id}` | Update project |
| **Projects** | DELETE | `/api/projects/{id}` | Delete project |
| **Projects** | POST | `/api/projects/{id}/save` | Save project state |
| **Files** | POST | `/api/projects/{id}/files` | Upload file(s) |
| **Files** | DELETE | `/api/projects/{id}/files/{file_id}` | Delete uploaded file |
| **Connection** | POST | `/api/projects/{id}/connect` | Test SF connection |
| **Connection** | GET | `/api/projects/{id}/locales` | Get available locales |
| **Connection** | GET | `/api/projects/{id}/objects` | Get available ODATA objects |
| **Export** | POST | `/api/projects/{id}/export` | Generate translation workbook |
| **Export** | GET | `/api/projects/{id}/export/status` | Get export progress |
| **Download** | GET | `/api/projects/{id}/download/{file_id}` | Download generated file |
| **Import** | POST | `/api/projects/{id}/import` | Import translations |
| **Import** | GET | `/api/projects/{id}/import/status` | Get import progress |
| **Import** | POST | `/api/projects/{id}/import/preview` | Preview import results |
| **Admin** | GET | `/api/admin/users` | List all users |
| **Admin** | GET | `/api/admin/users/{id}` | Get user details |
| **Admin** | DELETE | `/api/admin/users/{id}` | Delete user |
| **Admin** | GET | `/api/admin/projects` | List all projects |
| **Admin** | DELETE | `/api/admin/projects/{id}` | Delete any project |
| **Admin** | GET | `/api/admin/stats` | System statistics |

### 7.2 Request/Response Examples

#### Create Project
```http
POST /api/projects
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "name": "SAP Implementation Q1 2024",
  "description": "Translation project for ACME Corp SF implementation"
}
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "SAP Implementation Q1 2024",
  "description": "Translation project for ACME Corp SF implementation",
  "status": "draft",
  "config": {},
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "files": {
    "sdm": null,
    "cdm": null,
    "ec_sdm": null,
    "ec_cdm": null,
    "picklist": null
  }
}
```

#### Upload Files
```http
POST /api/projects/{id}/files
Authorization: Bearer {jwt_token}
Content-Type: multipart/form-data

files[]: (binary) Succession-Data-Model.xml
files[]: (binary) Corporate-Data-Model.xml
files[]: (binary) Picklist-Values.csv
```

Response:
```json
{
  "uploaded": [
    {
      "id": "file-uuid-1",
      "file_type": "sdm",
      "original_name": "Succession-Data-Model.xml",
      "file_size": 2456789,
      "uploaded_at": "2024-01-15T10:35:00Z"
    },
    {
      "id": "file-uuid-2",
      "file_type": "cdm",
      "original_name": "Corporate-Data-Model.xml",
      "file_size": 1234567,
      "uploaded_at": "2024-01-15T10:35:00Z"
    },
    {
      "id": "file-uuid-3",
      "file_type": "picklist",
      "original_name": "Picklist-Values.csv",
      "file_size": 567890,
      "uploaded_at": "2024-01-15T10:35:00Z"
    }
  ],
  "project_files": {
    "sdm": { "id": "file-uuid-1", "name": "Succession-Data-Model.xml" },
    "cdm": { "id": "file-uuid-2", "name": "Corporate-Data-Model.xml" },
    "ec_sdm": null,
    "ec_cdm": null,
    "picklist": { "id": "file-uuid-3", "name": "Picklist-Values.csv" }
  }
}
```

#### Test Connection
```http
POST /api/projects/{id}/connect
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "endpoint_url": "https://api4.successfactors.com/odata/v2",
  "company_id": "SFCPART000377",
  "username": "API_USER",
  "password": "SecurePassword123"
}
```

Response (Success):
```json
{
  "success": true,
  "message": "Connection established successfully",
  "instance_info": {
    "company_id": "SFCPART000377",
    "datacenter": "DC4 (Ashburn)",
    "api_version": "2.0"
  },
  "available_locales": [
    {"code": "en_US", "name": "English (US)", "default": true},
    {"code": "de_DE", "name": "German (Germany)"},
    {"code": "fr_FR", "name": "French (France)"}
  ]
}
```

Response (Failure):
```json
{
  "success": false,
  "error": "Authentication failed",
  "details": "Invalid username or password for company SFCPART000377",
  "suggestion": "Please verify your credentials and try again"
}
```

---

## 8. WebSocket Events

### 8.1 Event Types

```python
# WebSocket event definitions
WEBSOCKET_EVENTS = {
    # Server -> Client
    'progress_update': {
        'project_id': str,
        'operation': str,      # 'export' | 'import' | 'connect'
        'step': int,
        'total_steps': int,
        'step_name': str,
        'percent': float,      # 0-100
        'message': str,
        'details': dict        # Optional additional info
    },
    'operation_complete': {
        'project_id': str,
        'operation': str,
        'success': bool,
        'result': dict,
        'error': str           # If success=false
    },
    'project_saved': {
        'project_id': str,
        'saved_at': str
    },
    'error': {
        'code': str,
        'message': str,
        'details': dict
    },

    # Client -> Server
    'subscribe_project': {
        'project_id': str
    },
    'unsubscribe_project': {
        'project_id': str
    },
    'cancel_operation': {
        'project_id': str,
        'operation': str
    }
}
```

### 8.2 WebSocket Implementation

```python
# trexima/web/websocket.py
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import g

socketio = SocketIO(cors_allowed_origins="*", async_mode='gevent')

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    # Auth is handled via token in connection params
    emit('connected', {'message': 'Connected to TREXIMA'})

@socketio.on('subscribe_project')
def handle_subscribe(data):
    """Subscribe to project updates."""
    project_id = data.get('project_id')
    join_room(f'project_{project_id}')
    emit('subscribed', {'project_id': project_id})

@socketio.on('unsubscribe_project')
def handle_unsubscribe(data):
    """Unsubscribe from project updates."""
    project_id = data.get('project_id')
    leave_room(f'project_{project_id}')

def emit_progress(project_id: str, operation: str, step: int,
                  total_steps: int, step_name: str, percent: float,
                  message: str, details: dict = None):
    """Emit progress update to project subscribers."""
    socketio.emit('progress_update', {
        'project_id': project_id,
        'operation': operation,
        'step': step,
        'total_steps': total_steps,
        'step_name': step_name,
        'percent': percent,
        'message': message,
        'details': details or {}
    }, room=f'project_{project_id}')

def emit_complete(project_id: str, operation: str, success: bool,
                  result: dict = None, error: str = None):
    """Emit operation complete event."""
    socketio.emit('operation_complete', {
        'project_id': project_id,
        'operation': operation,
        'success': success,
        'result': result,
        'error': error
    }, room=f'project_{project_id}')
```

### 8.3 Progress Tracking Steps

#### Export Operation Steps
```python
EXPORT_STEPS = [
    (1, "Initializing", "Setting up export environment"),
    (2, "Loading Data Models", "Parsing uploaded XML files"),
    (3, "Connecting to API", "Establishing OData connection"),
    (4, "Fetching Locales", "Retrieving active languages"),
    (5, "Extracting EC Fields", "Processing Employee Central fields"),
    (6, "Extracting Foundation Objects", "Processing FO translations"),
    (7, "Extracting MDF Objects", "Processing MDF definitions"),
    (8, "Fetching Picklists", "Retrieving picklist values"),
    (9, "Generating Workbook", "Creating Excel file"),
    (10, "Finalizing", "Saving and preparing download")
]
```

#### Import Operation Steps
```python
IMPORT_STEPS = [
    (1, "Initializing", "Setting up import environment"),
    (2, "Loading Workbook", "Reading translation workbook"),
    (3, "Validating Data", "Checking data integrity"),
    (4, "Analyzing Changes", "Detecting modified translations"),
    (5, "Generating XML Files", "Creating data model files"),
    (6, "Connecting to API", "Establishing OData connection"),
    (7, "Updating Picklists", "Pushing picklist translations"),
    (8, "Updating FO Translations", "Pushing FO translations"),
    (9, "Finalizing", "Completing import process")
]
```

---

## 9. Frontend Architecture

### 9.1 Project Structure

```
trexima-frontend/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── main.tsx                 # Entry point
│   ├── App.tsx                  # Root component with routing
│   ├── index.css                # Global styles (Tailwind)
│   │
│   ├── components/              # Reusable UI components
│   │   ├── ui/                  # Base UI elements
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Select.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   ├── Spinner.tsx
│   │   │   └── Toast.tsx
│   │   ├── layout/              # Layout components
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── MainLayout.tsx
│   │   ├── auth/                # Auth components
│   │   │   └── ProtectedRoute.tsx
│   │   └── project/             # Project-specific components
│   │       ├── FileUploadZone.tsx
│   │       ├── DataModelBucket.tsx
│   │       ├── ConnectionConfig.tsx
│   │       ├── LanguageSelector.tsx
│   │       ├── ObjectSelector.tsx
│   │       ├── ExportSummary.tsx
│   │       ├── ImportPreview.tsx
│   │       └── ProgressOverlay.tsx
│   │
│   ├── pages/                   # Page components
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx    # Project overview
│   │   ├── ProjectPage.tsx      # Main project workflow
│   │   ├── AdminPage.tsx        # Admin dashboard
│   │   └── NotFoundPage.tsx
│   │
│   ├── stores/                  # Zustand state stores
│   │   ├── authStore.ts
│   │   ├── projectStore.ts
│   │   └── uiStore.ts
│   │
│   ├── hooks/                   # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useProject.ts
│   │   ├── useWebSocket.ts
│   │   └── useProgress.ts
│   │
│   ├── services/                # API & WebSocket services
│   │   ├── api.ts               # Axios instance & interceptors
│   │   ├── authService.ts
│   │   ├── projectService.ts
│   │   ├── adminService.ts
│   │   └── websocketService.ts
│   │
│   ├── types/                   # TypeScript types
│   │   ├── auth.ts
│   │   ├── project.ts
│   │   ├── api.ts
│   │   └── websocket.ts
│   │
│   └── utils/                   # Utility functions
│       ├── constants.ts
│       ├── formatters.ts
│       └── validators.ts
│
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

### 9.2 State Management (Zustand)

```typescript
// src/stores/projectStore.ts
import { create } from 'zustand';
import { Project, ProjectFile, ProjectConfig } from '../types/project';

interface ProjectState {
  // Current project
  currentProject: Project | null;
  projects: Project[];

  // File upload state
  uploadedFiles: {
    sdm: ProjectFile | null;
    cdm: ProjectFile | null;
    ec_sdm: ProjectFile | null;
    ec_cdm: ProjectFile | null;
    picklist: ProjectFile | null;
  };

  // Connection state
  isConnected: boolean;
  connectionError: string | null;

  // Available options (from API)
  availableLocales: Locale[];
  availableObjects: ODataObjectCategory[];

  // Selected options
  selectedLocales: string[];
  selectedObjects: SelectedObjects;
  selectedFOTranslations: string[];

  // Progress state
  currentOperation: 'export' | 'import' | null;
  progress: ProgressState | null;

  // Auto-save state
  lastSavedAt: Date | null;
  hasUnsavedChanges: boolean;
  isSaving: boolean;

  // Actions
  setCurrentProject: (project: Project) => void;
  setProjects: (projects: Project[]) => void;
  updateUploadedFile: (type: string, file: ProjectFile | null) => void;
  setConnectionStatus: (connected: boolean, error?: string) => void;
  setAvailableLocales: (locales: Locale[]) => void;
  setAvailableObjects: (objects: ODataObjectCategory[]) => void;
  toggleLocale: (locale: string) => void;
  toggleObject: (category: string, objectId: string) => void;
  toggleFOTranslation: (type: string) => void;
  setProgress: (progress: ProgressState | null) => void;
  markSaved: () => void;
  markUnsaved: () => void;
  reset: () => void;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  // Initial state
  currentProject: null,
  projects: [],
  uploadedFiles: {
    sdm: null,
    cdm: null,
    ec_sdm: null,
    ec_cdm: null,
    picklist: null,
  },
  isConnected: false,
  connectionError: null,
  availableLocales: [],
  availableObjects: [],
  selectedLocales: ['en_US'], // English US always selected
  selectedObjects: { ec_fields: [], foundation_objects: [], mdf_objects: [], picklists: [] },
  selectedFOTranslations: [],
  currentOperation: null,
  progress: null,
  lastSavedAt: null,
  hasUnsavedChanges: false,
  isSaving: false,

  // Actions implementation...
}));
```

### 9.3 WebSocket Hook

```typescript
// src/hooks/useWebSocket.ts
import { useEffect, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { useProjectStore } from '../stores/projectStore';
import { useAuthStore } from '../stores/authStore';

let socket: Socket | null = null;

export function useWebSocket(projectId: string | null) {
  const { token } = useAuthStore();
  const { setProgress } = useProjectStore();

  useEffect(() => {
    if (!token || !projectId) return;

    // Initialize socket connection
    socket = io(import.meta.env.VITE_API_URL, {
      auth: { token },
      transports: ['websocket']
    });

    // Subscribe to project
    socket.emit('subscribe_project', { project_id: projectId });

    // Handle progress updates
    socket.on('progress_update', (data) => {
      if (data.project_id === projectId) {
        setProgress({
          step: data.step,
          totalSteps: data.total_steps,
          stepName: data.step_name,
          percent: data.percent,
          message: data.message,
          details: data.details
        });
      }
    });

    // Handle operation complete
    socket.on('operation_complete', (data) => {
      if (data.project_id === projectId) {
        setProgress(null);
        // Handle completion...
      }
    });

    return () => {
      socket?.emit('unsubscribe_project', { project_id: projectId });
      socket?.disconnect();
      socket = null;
    };
  }, [token, projectId]);

  const cancelOperation = useCallback(() => {
    if (socket && projectId) {
      socket.emit('cancel_operation', { project_id: projectId });
    }
  }, [projectId]);

  return { cancelOperation };
}
```

---

## 10. UI/UX Specifications

### 10.1 Page Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER FLOW                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐     ┌──────────────┐     ┌───────────────────┐   │
│  │  Login   │────▶│  Dashboard   │────▶│  Project Page     │   │
│  │  (XSUAA) │     │  (Projects)  │     │  (Workflow)       │   │
│  └──────────┘     └──────────────┘     └───────────────────┘   │
│                          │                      │                │
│                          │                      ▼                │
│                          │              ┌───────────────────┐   │
│                          │              │  Section I:       │   │
│                          │              │  File Upload      │   │
│                          │              └─────────┬─────────┘   │
│                          │                        │              │
│                          │                        ▼              │
│                          │              ┌───────────────────┐   │
│                          │              │  Section II:      │   │
│                          │              │  API Connection   │   │
│                          │              └─────────┬─────────┘   │
│                          │                        │              │
│                          │                        ▼              │
│                          │              ┌───────────────────┐   │
│                          │              │  Section III:     │   │
│                          │              │  ODATA Config     │   │
│                          │              └─────────┬─────────┘   │
│                          │                        │              │
│                          │                        ▼              │
│                          │              ┌───────────────────┐   │
│                          │              │  Section IV:      │   │
│                          │              │  Summary & Export │   │
│                          │              └─────────┬─────────┘   │
│                          │                        │              │
│                          │                        ▼              │
│                          │              ┌───────────────────┐   │
│                          │              │  Download /       │   │
│                          │              │  Import           │   │
│                          │              └───────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│                   ┌──────────────┐                               │
│                   │ Admin Panel  │ (Admin only)                  │
│                   │ - All Users  │                               │
│                   │ - All Proj.  │                               │
│                   │ - Stats      │                               │
│                   └──────────────┘                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 Section I: File Upload Design

```
┌─────────────────────────────────────────────────────────────────┐
│  SECTION I: Upload Data Models                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Drag and drop your data model files below, or click to browse  │
│                                                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │     SDM     │ │     CDM     │ │   EC-SDM    │ │   EC-CDM   │ │
│  │  ┌───────┐  │ │  ┌───────┐  │ │  ┌───────┐  │ │  ┌──────┐  │ │
│  │  │  📄   │  │ │  │  📄   │  │ │  │  ✓    │  │ │  │  📄  │  │ │
│  │  │ Gray  │  │ │  │ Gray  │  │ │  │ Green │  │ │  │ Gray │  │ │
│  │  └───────┘  │ │  └───────┘  │ │  └───────┘  │ │  └──────┘  │ │
│  │             │ │             │ │  EC-SDM.xml │ │            │ │
│  │  Not        │ │  Not        │ │  2.4 MB     │ │  Not       │ │
│  │  Uploaded   │ │  Uploaded   │ │  Uploaded ✓ │ │  Uploaded  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                      PICKLIST CSV                            ││
│  │  ┌─────────────────────────────────────────────────────┐    ││
│  │  │                      📋                              │    ││
│  │  │              Picklist-Values.csv                     │    ││
│  │  │                   567 KB                             │    ││
│  │  │                  Uploaded ✓                          │    ││
│  │  └─────────────────────────────────────────────────────┘    ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ℹ️  Upload Status: 2/5 files uploaded                       ││
│  │     For complete coverage, please upload all 5 files.       ││
│  │     Minimum required: 1 data model file.                    ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  [ Upload Files ] or drag files anywhere on this section        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.3 Section II: API Connection Design

```
┌─────────────────────────────────────────────────────────────────┐
│  SECTION II: SuccessFactors API Connection                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  API Server Endpoint                                             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  ▼ DC4 - US East (Ashburn) - Production                     ││
│  └─────────────────────────────────────────────────────────────┘│
│  │  Full URL: https://api4.successfactors.com/odata/v2          │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Production Datacenters                                      ││
│  │  ├─ DC2 - US West (Chandler)                                ││
│  │  ├─ DC4 - US East (Ashburn)            ◀── Selected         ││
│  │  ├─ DC8 - US East (Sterling)                                ││
│  │  ├─ DC10 - EU Central (Amsterdam)                           ││
│  │  ├─ DC12 - EU Central (Frankfurt)                           ││
│  │  ├─ DC15 - EU West (London)                                 ││
│  │  ├─ DC17 - APAC (Sydney)                                    ││
│  │  ├─ DC18 - APAC (Singapore)                                 ││
│  │  ├─ DC19 - APAC (Tokyo)                                     ││
│  │  └─ ...more                                                  ││
│  │                                                              ││
│  │  Preview/Sandbox Datacenters                                 ││
│  │  ├─ DC2 Preview                                             ││
│  │  ├─ DC4 Preview                                             ││
│  │  └─ ...                                                      ││
│  │                                                              ││
│  │  Salesdemo Instances                                         ││
│  │  ├─ Salesdemo 2 (EU)                                        ││
│  │  ├─ Salesdemo 4 (US)                                        ││
│  │  └─ Salesdemo 8 (APAC)                                      ││
│  │                                                              ││
│  │  Custom URL                                                  ││
│  │  └─ Enter custom endpoint...                                ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  Company ID                                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  SFCPART000377                                               ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  Username                                                        │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  API_USER                                                    ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  Password                                                        │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  ●●●●●●●●●●●●                                                ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────┐                                             │
│  │ Test Connection │  ← Only enabled when all fields filled     │
│  └─────────────────┘                                             │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ✓ Connected successfully!                                    ││
│  │   Instance: SFCPART000377 @ DC4                              ││
│  │   17 active locales detected                                 ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.4 Section III: ODATA Configuration Design

```
┌─────────────────────────────────────────────────────────────────┐
│  SECTION III: Translation Scope Configuration                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  LANGUAGES                                                   ││
│  │  ─────────────────────────────────────────────────────────  ││
│  │  ☑ English (US)  [locked]    ☑ German (DE)    ☑ French (FR) ││
│  │  ☐ Spanish (ES)              ☑ Italian (IT)   ☐ Dutch (NL)  ││
│  │  ☐ Portuguese (PT)           ☐ Japanese (JP)  ☐ Chinese (CN)││
│  │  [Select All]  [Deselect All]                                ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  ODATA OBJECTS                                               ││
│  │  ─────────────────────────────────────────────────────────  ││
│  │                                                              ││
│  │  ▼ Employee Central Core  (12 selected / 25 available)      ││
│  │  │  ☑ PerPersonal        ☑ PerEmail         ☑ EmpJob       ││
│  │  │  ☑ EmpCompensation    ☐ EmpPayCompRec... ☐ EmpWorkPerm  ││
│  │  │  ...                                                      ││
│  │                                                              ││
│  │  ▶ Foundation Objects  (5 selected / 15 available)          ││
│  │                                                              ││
│  │  ▶ MDF Objects  (3 selected / 8 custom objects)             ││
│  │                                                              ││
│  │  ▶ Picklists  (45 selected / 120 available)                 ││
│  │                                                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  FO TRANSLATIONS                                             ││
│  │  ─────────────────────────────────────────────────────────  ││
│  │  ☑ Event Reasons      ☑ Frequencies       ☑ Geo Zones      ││
│  │  ☑ Location Groups    ☑ Locations         ☑ Pay Components ││
│  │  ☑ Pay Comp. Groups   ☑ Pay Grades        ☑ Pay Ranges     ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.5 Section IV: Summary & Export Design

```
┌─────────────────────────────────────────────────────────────────┐
│  SECTION IV: Export Summary                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    EXPORT CONFIGURATION                    │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │                                                            │  │
│  │  📁 Data Models          │  🌐 Languages                   │  │
│  │  ────────────────────    │  ────────────────────          │  │
│  │  ✓ EC-SDM (2.4 MB)       │  5 languages selected:         │  │
│  │  ✓ Picklist CSV          │  en_US, de_DE, fr_FR,          │  │
│  │                          │  it_IT, es_ES                   │  │
│  │                          │                                 │  │
│  │  📊 ODATA Objects        │  📋 FO Translations            │  │
│  │  ────────────────────    │  ────────────────────          │  │
│  │  ▸ 12 EC Core fields     │  9 types selected              │  │
│  │  ▸ 5 Foundation Obj.     │  ▸ Event Reasons ▸ Locations   │  │
│  │  ▸ 3 MDF Objects         │  ▸ Pay Components ▸ Pay Grades │  │
│  │  ▸ 45 Picklists          │  [+5 more...]                  │  │
│  │                          │                                 │  │
│  │  🔗 API Connection                                         │  │
│  │  ──────────────────────────────────────────────────────   │  │
│  │  ✓ Connected to SFCPART000377 @ DC4 (Ashburn)             │  │
│  │                                                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Estimated Output                                          │  │
│  │  • ~15 worksheets in Excel workbook                       │  │
│  │  • ~25,000 translatable entries                           │  │
│  │  • Estimated file size: 4-6 MB                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│               ┌──────────────────────────────┐                   │
│               │  Generate Translation Workbook │                   │
│               └──────────────────────────────┘                   │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  💾 Auto-saved 2 seconds ago                               │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.6 Progress Overlay Design

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│                    ┌─────────────────────────┐                   │
│                    │    GENERATING WORKBOOK   │                   │
│                    └─────────────────────────┘                   │
│                                                                  │
│    Step 6 of 10: Extracting Foundation Objects                  │
│                                                                  │
│    ┌─────────────────────────────────────────────────────────┐  │
│    │████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░│  │
│    └─────────────────────────────────────────────────────────┘  │
│                          58%                                     │
│                                                                  │
│    Current: Processing FOLocation translations (45/120)         │
│                                                                  │
│    ┌─────────────────────────────────────────────────────────┐  │
│    │  ✓ Step 1: Initializing                          0.2s   │  │
│    │  ✓ Step 2: Loading Data Models                   1.5s   │  │
│    │  ✓ Step 3: Connecting to API                     0.8s   │  │
│    │  ✓ Step 4: Fetching Locales                      0.3s   │  │
│    │  ✓ Step 5: Extracting EC Fields                  4.2s   │  │
│    │  ◉ Step 6: Extracting Foundation Objects         ...    │  │
│    │  ○ Step 7: Extracting MDF Objects                       │  │
│    │  ○ Step 8: Fetching Picklists                           │  │
│    │  ○ Step 9: Generating Workbook                          │  │
│    │  ○ Step 10: Finalizing                                  │  │
│    └─────────────────────────────────────────────────────────┘  │
│                                                                  │
│                      [ Cancel Operation ]                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 11. SuccessFactors API Endpoints

### 11.1 Complete Endpoint List

```typescript
// src/utils/sfEndpoints.ts
export const SF_ENDPOINTS = {
  production: {
    label: "Production Datacenters",
    endpoints: [
      { id: "dc2", name: "DC2 - US West (Chandler)", url: "https://api2.successfactors.com/odata/v2" },
      { id: "dc4", name: "DC4 - US East (Ashburn)", url: "https://api4.successfactors.com/odata/v2" },
      { id: "dc5", name: "DC5 - US East (Ashburn)", url: "https://api5.successfactors.com/odata/v2" },
      { id: "dc8", name: "DC8 - US East (Sterling)", url: "https://api8.successfactors.com/odata/v2" },
      { id: "dc10", name: "DC10 - EU Central (Amsterdam)", url: "https://api10.successfactors.eu/odata/v2" },
      { id: "dc12", name: "DC12 - EU Central (Frankfurt)", url: "https://api12.successfactors.eu/odata/v2" },
      { id: "dc15", name: "DC15 - EU West (London)", url: "https://api15.successfactors.eu/odata/v2" },
      { id: "dc16", name: "DC16 - EU Central (Frankfurt)", url: "https://api16.successfactors.eu/odata/v2" },
      { id: "dc17", name: "DC17 - APAC (Sydney)", url: "https://api17.successfactors.com/odata/v2" },
      { id: "dc18", name: "DC18 - APAC (Singapore)", url: "https://api18.successfactors.com/odata/v2" },
      { id: "dc19", name: "DC19 - APAC (Tokyo)", url: "https://api19.successfactors.com/odata/v2" },
      { id: "dc22", name: "DC22 - APAC (Seoul)", url: "https://api22.successfactors.com/odata/v2" },
      { id: "dc23", name: "DC23 - APAC (Osaka)", url: "https://api23.successfactors.com/odata/v2" },
      { id: "dc24", name: "DC24 - Middle East (Dubai)", url: "https://api24.successfactors.com/odata/v2" },
      { id: "dc25", name: "DC25 - South America (São Paulo)", url: "https://api25.successfactors.com/odata/v2" },
      { id: "dc27", name: "DC27 - India (Mumbai)", url: "https://api27.successfactors.com/odata/v2" },
      { id: "dc28", name: "DC28 - Canada (Toronto)", url: "https://api28.successfactors.com/odata/v2" },
      { id: "dc33", name: "DC33 - Australia (Sydney)", url: "https://api33.successfactors.com/odata/v2" },
      { id: "dc35", name: "DC35 - US Gov Cloud", url: "https://api35.successfactors.com/odata/v2" },
      { id: "dc40", name: "DC40 - China (Shanghai)", url: "https://api40.successfactors.cn/odata/v2" },
      { id: "dc45", name: "DC45 - Saudi Arabia (Riyadh)", url: "https://api45.successfactors.com/odata/v2" },
      { id: "dc55", name: "DC55 - Switzerland (Zurich)", url: "https://api55.successfactors.eu/odata/v2" },
      { id: "dc56", name: "DC56 - India (Hyderabad)", url: "https://api56.successfactors.com/odata/v2" },
      { id: "dc58", name: "DC58 - South Korea (Seoul)", url: "https://api58.successfactors.com/odata/v2" },
      { id: "dc61", name: "DC61 - Hong Kong", url: "https://api61.successfactors.com/odata/v2" },
      { id: "dc68", name: "DC68 - EU Central (Frankfurt)", url: "https://api68.successfactors.eu/odata/v2" },
      { id: "dc69", name: "DC69 - US East (Virginia)", url: "https://api69.successfactors.com/odata/v2" },
      { id: "dc70", name: "DC70 - Indonesia (Jakarta)", url: "https://api70.successfactors.com/odata/v2" }
    ]
  },
  preview: {
    label: "Preview/Sandbox Datacenters",
    endpoints: [
      { id: "dc2-preview", name: "DC2 Preview", url: "https://api2preview.sapsf.com/odata/v2" },
      { id: "dc4-preview", name: "DC4 Preview", url: "https://api4preview.sapsf.com/odata/v2" },
      { id: "dc10-preview", name: "DC10 Preview (EU)", url: "https://api10preview.sapsf.eu/odata/v2" },
      { id: "dc12-preview", name: "DC12 Preview (EU)", url: "https://api12preview.sapsf.eu/odata/v2" },
      { id: "dc17-preview", name: "DC17 Preview (APAC)", url: "https://api17preview.sapsf.com/odata/v2" },
      { id: "dc18-preview", name: "DC18 Preview (APAC)", url: "https://api18preview.sapsf.com/odata/v2" }
    ]
  },
  salesdemo: {
    label: "Salesdemo Instances",
    endpoints: [
      { id: "salesdemo2", name: "Salesdemo 2 (EU)", url: "https://apisalesdemo2.successfactors.eu/odata/v2" },
      { id: "salesdemo4", name: "Salesdemo 4 (US)", url: "https://apisalesdemo4.successfactors.com/odata/v2" },
      { id: "salesdemo8", name: "Salesdemo 8 (APAC)", url: "https://apisalesdemo8.successfactors.com/odata/v2" }
    ]
  },
  custom: {
    label: "Custom URL",
    endpoints: [
      { id: "custom", name: "Enter custom endpoint URL", url: "" }
    ]
  }
};
```

---

## 12. ODATA Object Categories

### 12.1 Employee Central Core Objects

```typescript
export const EC_CORE_OBJECTS = [
  { id: "PerPersonal", name: "Personal Information", description: "Basic personal data" },
  { id: "PerEmail", name: "Email Information", description: "Email addresses" },
  { id: "PerPhone", name: "Phone Information", description: "Phone numbers" },
  { id: "PerAddressDeflt", name: "Address Information", description: "Physical addresses" },
  { id: "PerEmergencyContacts", name: "Emergency Contacts", description: "Emergency contact details" },
  { id: "PerNationalId", name: "National ID", description: "National identification" },
  { id: "EmpJob", name: "Job Information", description: "Employment and job data" },
  { id: "EmpCompensation", name: "Compensation Information", description: "Salary and pay data" },
  { id: "EmpPayCompRecurring", name: "Recurring Pay Components", description: "Recurring payments" },
  { id: "EmpPayCompNonRecurring", name: "Non-Recurring Pay Components", description: "One-time payments" },
  { id: "EmpWorkPermit", name: "Work Permits", description: "Work authorization" },
  { id: "EmpGlobalAssignment", name: "Global Assignments", description: "International assignments" },
  { id: "EmpJobRelationships", name: "Job Relationships", description: "Reporting relationships" },
  { id: "PerGlobalInfoCHE", name: "Switzerland Specific", description: "CH country-specific fields" },
  { id: "PerGlobalInfoDEU", name: "Germany Specific", description: "DE country-specific fields" },
  { id: "PerGlobalInfoFRA", name: "France Specific", description: "FR country-specific fields" },
  { id: "PerGlobalInfoGBR", name: "UK Specific", description: "GB country-specific fields" },
  { id: "PerGlobalInfoUSA", name: "USA Specific", description: "US country-specific fields" }
];
```

### 12.2 Foundation Objects

```typescript
export const FOUNDATION_OBJECTS = [
  { id: "FOBusinessUnit", name: "Business Units", translatable: true },
  { id: "FOCompany", name: "Companies", translatable: true },
  { id: "FOCostCenter", name: "Cost Centers", translatable: true },
  { id: "FODepartment", name: "Departments", translatable: true },
  { id: "FODivision", name: "Divisions", translatable: true },
  { id: "FOEventReason", name: "Event Reasons", translatable: true },
  { id: "FOFrequency", name: "Frequencies", translatable: true },
  { id: "FOGeozone", name: "Geo Zones", translatable: true },
  { id: "FOJobClassLocalDEU", name: "Job Classes (DE)", translatable: true },
  { id: "FOJobClassLocalFRA", name: "Job Classes (FR)", translatable: true },
  { id: "FOJobCode", name: "Job Codes", translatable: true },
  { id: "FOJobFunction", name: "Job Functions", translatable: true },
  { id: "FOLegalEntity", name: "Legal Entities", translatable: true },
  { id: "FOLocation", name: "Locations", translatable: true },
  { id: "FOLocationGroup", name: "Location Groups", translatable: true },
  { id: "FOPayComponent", name: "Pay Components", translatable: true },
  { id: "FOPayComponentGroup", name: "Pay Component Groups", translatable: true },
  { id: "FOPayGrade", name: "Pay Grades", translatable: true },
  { id: "FOPayRange", name: "Pay Ranges", translatable: true },
  { id: "FOPosition", name: "Positions", translatable: false }
];
```

### 12.3 FO Translation Types (Selectable)

```typescript
export const FO_TRANSLATION_TYPES = [
  { id: "eventReason", name: "Event Reasons", object: "FOEventReason", field: "name" },
  { id: "frequency", name: "Frequencies", object: "FOFrequency", field: "name" },
  { id: "geozone", name: "Geo Zones", object: "FOGeozone", field: "name" },
  { id: "locationGroup", name: "Location Groups", object: "FOLocationGroup", field: "name" },
  { id: "location", name: "Locations", object: "FOLocation", field: "name" },
  { id: "payComponent", name: "Pay Components", object: "FOPayComponent", field: "name" },
  { id: "payComponentGroup", name: "Pay Component Groups", object: "FOPayComponentGroup", field: "name" },
  { id: "payGrade", name: "Pay Grades", object: "FOPayGrade", field: "name" },
  { id: "payRange", name: "Pay Ranges", object: "FOPayRange", field: "name" }
];
```

---

## 13. Implementation Tasks

### 13.1 Task Breakdown (Ordered by Dependencies)

```
PHASE 1: Infrastructure Setup
├── 1.1 BTP Service Provisioning
│   ├── Create XSUAA service instance
│   ├── Create PostgreSQL service instance
│   ├── Create Object Store service instance
│   └── Configure service bindings
│
├── 1.2 Backend Foundation
│   ├── Add new dependencies to requirements.txt
│   ├── Create database models (models.py)
│   ├── Create storage service (storage.py)
│   ├── Create auth module (auth.py)
│   ├── Configure Flask-SQLAlchemy
│   └── Configure Flask-SocketIO
│
└── 1.3 Frontend Foundation
    ├── Initialize Vite + React + TypeScript project
    ├── Configure Tailwind CSS
    ├── Set up project structure
    ├── Create base UI components
    └── Configure API client (axios)

PHASE 2: Authentication
├── 2.1 XSUAA Integration
│   ├── Update xs-security.json
│   ├── Implement token validation
│   ├── Create auth decorators
│   └── Handle user provisioning
│
├── 2.2 Frontend Auth
│   ├── Implement OAuth2 flow
│   ├── Create auth store
│   ├── Create ProtectedRoute component
│   └── Create login redirect handling
│
└── 2.3 User Management
    ├── Auto-create user on first login
    ├── Track last login
    └── Implement admin user detection

PHASE 3: Project Management
├── 3.1 Backend APIs
│   ├── Create projects blueprint
│   ├── Implement CRUD operations
│   ├── Enforce 3-project limit
│   └── Implement project deletion flow
│
├── 3.2 Frontend Pages
│   ├── Create Dashboard page
│   ├── Create Project list component
│   ├── Create New Project modal
│   └── Create Delete Project confirmation
│
└── 3.3 Auto-Save
    ├── Implement debounced save
    ├── Create save indicator component
    └── Handle offline scenarios

PHASE 4: File Upload (Section I)
├── 4.1 Backend
│   ├── Create file upload endpoints
│   ├── Implement file type detection
│   ├── Store files in Object Store
│   └── Update project file references
│
├── 4.2 Frontend
│   ├── Create FileUploadZone component
│   ├── Create DataModelBucket component
│   ├── Implement drag-and-drop
│   ├── Add upload progress indicators
│   └── Handle multi-file uploads

PHASE 5: API Connection (Section II)
├── 5.1 Backend
│   ├── Create connection test endpoint
│   ├── Secure credential storage (encryption)
│   └── Implement locale discovery
│
├── 5.2 Frontend
│   ├── Create ConnectionConfig component
│   ├── Create endpoint selector
│   ├── Implement connection test UI
│   └── Display connection status

PHASE 6: ODATA Configuration (Section III)
├── 6.1 Backend
│   ├── Create object discovery endpoint
│   ├── Query available MDF objects
│   └── Query available picklists
│
├── 6.2 Frontend
│   ├── Create LanguageSelector component
│   ├── Create ObjectSelector component
│   ├── Create collapsible categories
│   └── Implement selection persistence

PHASE 7: Export Workflow (Section IV)
├── 7.1 Backend
│   ├── Refactor export logic for async
│   ├── Implement WebSocket progress
│   ├── Store generated files
│   └── Create download endpoints
│
├── 7.2 Frontend
│   ├── Create ExportSummary component
│   ├── Create ProgressOverlay component
│   ├── Implement WebSocket client
│   └── Handle download flow

PHASE 8: Import Workflow (Section VI)
├── 8.1 Backend
│   ├── Create import preview endpoint
│   ├── Refactor import logic for async
│   ├── Implement ODATA update opt-out
│   └── Create import status tracking
│
├── 8.2 Frontend
│   ├── Create ImportPreview component
│   ├── Create import configuration
│   └── Handle import progress

PHASE 9: Admin Features
├── 9.1 Backend
│   ├── Create admin blueprint
│   ├── Implement user listing
│   ├── Implement project oversight
│   └── Create statistics endpoint
│
└── 9.2 Frontend
    ├── Create AdminPage
    ├── Create user management table
    └── Create statistics dashboard

PHASE 10: Polish & Deployment
├── 10.1 Testing
│   ├── Backend unit tests
│   ├── Frontend component tests
│   └── Integration tests
│
├── 10.2 Deployment
│   ├── Update manifest.yml
│   ├── Configure mta.yaml for services
│   ├── Set up CI/CD
│   └── Deploy to BTP
│
└── 10.3 Documentation
    ├── Update README
    ├── Create user guide
    └── Create admin guide
```

### 13.2 File Creation Checklist

#### Backend Files (New)
```
trexima/web/
├── auth.py              # XSUAA authentication
├── models.py            # SQLAlchemy models
├── storage.py           # Object Store service
├── websocket.py         # WebSocket handlers
├── blueprints/
│   ├── __init__.py
│   ├── auth_bp.py       # Auth endpoints
│   ├── projects_bp.py   # Project endpoints
│   ├── files_bp.py      # File upload endpoints
│   ├── export_bp.py     # Export endpoints
│   ├── import_bp.py     # Import endpoints
│   └── admin_bp.py      # Admin endpoints
└── services/
    ├── __init__.py
    ├── project_service.py
    ├── export_service.py
    └── import_service.py
```

#### Frontend Files (New)
```
trexima-frontend/src/
├── components/
│   ├── ui/              # ~10 base components
│   ├── layout/          # ~3 layout components
│   ├── auth/            # ~2 auth components
│   └── project/         # ~8 project components
├── pages/               # ~5 page components
├── stores/              # ~3 Zustand stores
├── hooks/               # ~4 custom hooks
├── services/            # ~5 API services
├── types/               # ~4 type definition files
└── utils/               # ~3 utility files
```

---

## 14. Security Considerations

### 14.1 Authentication & Authorization
- All API endpoints require valid JWT token (except health check)
- Token validation using SAP XSSEC library
- Admin scope required for admin endpoints
- User can only access own projects (except admin)

### 14.2 Data Protection
- SF API credentials encrypted at rest using Fernet
- Credentials never logged or exposed in errors
- File access controlled by user ownership
- Pre-signed URLs for downloads (time-limited)

### 14.3 Input Validation
- File type validation (XML, XLSX, CSV only)
- File size limits (100MB per file)
- SQL injection prevention via SQLAlchemy ORM
- XSS prevention via React's default escaping

### 14.4 Rate Limiting
- Consider implementing rate limiting for API endpoints
- Limit concurrent export/import operations per user

---

## 15. Deployment Configuration

### 15.1 Updated manifest.yml

```yaml
---
applications:
  - name: trexima-web
    memory: 1G
    instances: 1
    buildpacks:
      - python_buildpack
    command: gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 --bind 0.0.0.0:$PORT 'trexima.web.app:create_app()'
    random-route: true
    env:
      FLASK_ENV: production
      PYTHONUNBUFFERED: true
    services:
      - trexima-xsuaa
      - trexima-postgresql
      - trexima-objectstore
```

### 15.2 mta.yaml (Multi-Target Application)

```yaml
_schema-version: "3.1"
ID: trexima
version: 4.0.0
description: TREXIMA - SF Translation Management

modules:
  - name: trexima-web
    type: python
    path: .
    parameters:
      memory: 1G
      disk-quota: 512M
    requires:
      - name: trexima-xsuaa
      - name: trexima-postgresql
      - name: trexima-objectstore
    properties:
      FLASK_ENV: production

  - name: trexima-frontend
    type: html5
    path: trexima-frontend/dist
    parameters:
      memory: 64M
    build-parameters:
      builder: npm
      build-result: dist

resources:
  - name: trexima-xsuaa
    type: org.cloudfoundry.managed-service
    parameters:
      service: xsuaa
      service-plan: application
      path: ./xs-security.json

  - name: trexima-postgresql
    type: org.cloudfoundry.managed-service
    parameters:
      service: postgresql-db
      service-plan: trial

  - name: trexima-objectstore
    type: org.cloudfoundry.managed-service
    parameters:
      service: objectstore
      service-plan: s3-standard
```

---

## 16. Testing Strategy

### 16.1 Backend Tests

```python
# tests/test_projects.py
import pytest
from trexima.web.app import create_app
from trexima.web.models import db, User, Project

@pytest.fixture
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(app):
    # Mock XSUAA token for testing
    return {'Authorization': 'Bearer test_token'}

def test_create_project(client, auth_headers):
    response = client.post('/api/projects',
        json={'name': 'Test Project'},
        headers=auth_headers)
    assert response.status_code == 201
    assert response.json['name'] == 'Test Project'

def test_project_limit(client, auth_headers):
    # Create 3 projects
    for i in range(3):
        client.post('/api/projects',
            json={'name': f'Project {i}'},
            headers=auth_headers)

    # 4th should fail
    response = client.post('/api/projects',
        json={'name': 'Project 4'},
        headers=auth_headers)
    assert response.status_code == 400
    assert 'limit' in response.json['error'].lower()
```

### 16.2 Frontend Tests

```typescript
// src/components/project/FileUploadZone.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { FileUploadZone } from './FileUploadZone';

describe('FileUploadZone', () => {
  it('renders all data model buckets', () => {
    render(<FileUploadZone projectId="test" />);

    expect(screen.getByText('SDM')).toBeInTheDocument();
    expect(screen.getByText('CDM')).toBeInTheDocument();
    expect(screen.getByText('EC-SDM')).toBeInTheDocument();
    expect(screen.getByText('EC-CDM')).toBeInTheDocument();
    expect(screen.getByText('Picklist')).toBeInTheDocument();
  });

  it('shows upload status after file drop', async () => {
    render(<FileUploadZone projectId="test" />);

    const dropzone = screen.getByTestId('dropzone');
    const file = new File(['content'], 'test.xml', { type: 'text/xml' });

    fireEvent.drop(dropzone, {
      dataTransfer: { files: [file] }
    });

    expect(await screen.findByText('Uploaded')).toBeInTheDocument();
  });
});
```

---

## Appendix A: Quick Reference for Implementation

### A.1 Key Constants

```python
# trexima/web/constants.py
MAX_PROJECTS_PER_USER = 3
FILE_RETENTION_DAYS = 90
MAX_FILE_SIZE_MB = 100
ALLOWED_EXTENSIONS = {'xml', 'xlsx', 'csv'}

DATA_MODEL_TYPES = ['sdm', 'cdm', 'ec_sdm', 'ec_cdm', 'picklist']

PROJECT_STATUSES = ['draft', 'configured', 'exported', 'imported']
```

### A.2 Environment Variables

```bash
# Required in production
VCAP_SERVICES           # Auto-set by Cloud Foundry
VCAP_APPLICATION        # Auto-set by Cloud Foundry

# Optional overrides
DATABASE_URL            # PostgreSQL connection string
OBJECT_STORE_BUCKET     # Object store bucket name
SECRET_KEY              # Flask secret key
```

### A.3 API Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (invalid/missing token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 409 | Conflict (e.g., project limit reached) |
| 500 | Server Error |

---

## Appendix B: Migration from v3.0

### B.1 Breaking Changes

1. **Authentication Required**: All endpoints now require JWT token
2. **Project-Based**: Operations tied to projects, not global state
3. **Persistent Storage**: Files stored in Object Store, not local filesystem
4. **WebSocket**: Progress updates via WebSocket, not polling

### B.2 Deprecated Endpoints

| Old Endpoint | New Endpoint |
|--------------|--------------|
| `/api/upload` | `/api/projects/{id}/files` |
| `/api/export` | `/api/projects/{id}/export` |
| `/api/import` | `/api/projects/{id}/import` |
| `/api/status` | `/api/projects/{id}` |
| `/api/reset` | DELETE `/api/projects/{id}` |

---

*Document Version: 1.0*
*Created: January 2026*
*For: TREXIMA v4.0 Implementation*
