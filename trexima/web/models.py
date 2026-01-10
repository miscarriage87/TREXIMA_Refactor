"""
TREXIMA v2.0 - Database Models

SQLAlchemy models for PostgreSQL database.
Handles users, projects, files, and generated outputs.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import uuid
import json

db = SQLAlchemy()


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class User(db.Model):
    """User model - represents a TREXIMA user authenticated via XSUAA."""

    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    xsuaa_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    projects = db.relationship(
        'Project',
        backref='owner',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='Project.updated_at.desc()'
    )

    # Constants
    MAX_PROJECTS = 3  # Hard-coded limit per user

    def __repr__(self) -> str:
        return f'<User {self.email}>'

    def to_dict(self, include_projects: bool = False) -> Dict[str, Any]:
        """Convert user to dictionary."""
        data = {
            'id': self.id,
            'email': self.email,
            'display_name': self.display_name,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'project_count': self.projects.count()
        }
        if include_projects:
            data['projects'] = [p.to_dict() for p in self.projects.all()]
        return data

    def can_create_project(self) -> bool:
        """Check if user can create a new project."""
        return self.projects.count() < self.MAX_PROJECTS

    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()


class Project(db.Model):
    """Project model - represents a translation project."""

    __tablename__ = 'projects'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='draft', nullable=False)
    config = db.Column(db.JSON, default=dict, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_accessed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    files = db.relationship(
        'ProjectFile',
        backref='project',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    generated_files = db.relationship(
        'GeneratedFile',
        backref='project',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    # Valid status values
    STATUSES = ['draft', 'configured', 'exported', 'imported']

    # File type constants
    FILE_TYPES = ['sdm', 'cdm', 'ec_sdm', 'ec_cdm', 'picklist']

    def __repr__(self) -> str:
        return f'<Project {self.name}>'

    def to_dict(self, include_files: bool = True, include_config: bool = True) -> Dict[str, Any]:
        """Convert project to dictionary."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            'file_count': self.files.count()
        }

        if include_config:
            data['config'] = self.config or {}

        if include_files:
            data['files'] = self.get_files_summary()
            data['generated_files'] = [gf.to_dict() for gf in self.generated_files.all()]

        return data

    def get_files_summary(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """Get summary of uploaded files by type."""
        summary = {ft: None for ft in self.FILE_TYPES}
        for f in self.files.all():
            if f.file_type in summary:
                summary[f.file_type] = {
                    'id': f.id,
                    'name': f.original_name,
                    'size': f.file_size,
                    'uploaded_at': f.uploaded_at.isoformat() if f.uploaded_at else None
                }
        return summary

    def get_file_by_type(self, file_type: str) -> Optional['ProjectFile']:
        """Get uploaded file by type."""
        return self.files.filter_by(file_type=file_type).first()

    def has_minimum_files(self) -> bool:
        """Check if project has minimum required files (at least one data model)."""
        data_model_types = ['sdm', 'cdm', 'ec_sdm', 'ec_cdm']
        return any(self.get_file_by_type(ft) is not None for ft in data_model_types)

    def has_all_files(self) -> bool:
        """Check if all 5 files are uploaded."""
        return all(self.get_file_by_type(ft) is not None for ft in self.FILE_TYPES)

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update project configuration."""
        if self.config is None:
            self.config = {}
        self.config.update(updates)
        self.config['last_saved_at'] = datetime.utcnow().isoformat()
        # Mark as modified for SQLAlchemy to detect JSON change
        db.session.execute(
            db.update(Project).where(Project.id == self.id).values(config=self.config)
        )

    def touch(self) -> None:
        """Update last_accessed_at timestamp."""
        self.last_accessed_at = datetime.utcnow()


class ProjectFile(db.Model):
    """ProjectFile model - represents an uploaded file (data model or picklist)."""

    __tablename__ = 'project_files'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False, index=True)
    file_type = db.Column(db.String(50), nullable=False)  # sdm, cdm, ec_sdm, ec_cdm, picklist
    original_name = db.Column(db.String(255), nullable=False)
    storage_key = db.Column(db.String(512), nullable=False)  # Object Store key
    file_size = db.Column(db.BigInteger, default=0)
    content_type = db.Column(db.String(100))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Valid file types
    VALID_TYPES = ['sdm', 'cdm', 'ec_sdm', 'ec_cdm', 'picklist']

    def __repr__(self) -> str:
        return f'<ProjectFile {self.file_type}: {self.original_name}>'

    def to_dict(self) -> Dict[str, Any]:
        """Convert file to dictionary."""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'file_type': self.file_type,
            'original_name': self.original_name,
            'file_size': self.file_size,
            'content_type': self.content_type,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }

    @staticmethod
    def detect_file_type(filename: str, content: bytes = None) -> Optional[str]:
        """
        Detect file type from filename and optionally content.
        Returns: sdm, cdm, ec_sdm, ec_cdm, picklist, or None
        """
        filename_lower = filename.lower()

        # CSV files are picklists
        if filename_lower.endswith('.csv'):
            return 'picklist'

        # XML files - detect type from name patterns
        if filename_lower.endswith('.xml'):
            # Check for EC (Employee Central) / CSF (Country-Specific Fields) patterns
            if 'ec-' in filename_lower or 'sfec' in filename_lower or 'csf' in filename_lower:
                if 'corporate' in filename_lower or 'cdm' in filename_lower:
                    return 'ec_cdm'
                else:
                    return 'ec_sdm'
            # Standard data models
            elif 'corporate' in filename_lower or 'cdm' in filename_lower:
                return 'cdm'
            elif 'succession' in filename_lower or 'sdm' in filename_lower:
                return 'sdm'

            # If no pattern match, try to detect from content
            if content:
                content_str = content[:2000].decode('utf-8', errors='ignore').lower()
                if 'hris-element' in content_str or 'hris-field' in content_str:
                    if 'corporate' in content_str:
                        return 'ec_cdm'
                    return 'ec_sdm'
                elif 'corporate' in content_str:
                    return 'cdm'
                else:
                    return 'sdm'

        return None


class GeneratedFile(db.Model):
    """GeneratedFile model - represents a generated output file (workbook or import XML)."""

    __tablename__ = 'generated_files'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False, index=True)
    file_type = db.Column(db.String(50), nullable=False)  # workbook, xml_sdm, xml_cdm, etc.
    filename = db.Column(db.String(255), nullable=False)
    storage_key = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.BigInteger, default=0)
    content_type = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    downloaded_count = db.Column(db.Integer, default=0, nullable=False)
    file_metadata = db.Column(db.JSON, default=dict)

    # File retention period in days
    RETENTION_DAYS = 90

    # Valid generated file types
    VALID_TYPES = ['workbook', 'xml_sdm', 'xml_cdm', 'xml_ec_sdm', 'xml_ec_cdm', 'csv_picklist']

    def __init__(self, **kwargs):
        """Initialize with default expiry date."""
        if 'expires_at' not in kwargs:
            kwargs['expires_at'] = datetime.utcnow() + timedelta(days=self.RETENTION_DAYS)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f'<GeneratedFile {self.file_type}: {self.filename}>'

    def to_dict(self) -> Dict[str, Any]:
        """Convert file to dictionary."""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'file_type': self.file_type,
            'filename': self.filename,
            'file_size': self.file_size,
            'content_type': self.content_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'downloaded_count': self.downloaded_count,
            'is_expired': self.is_expired,
            'metadata': self.file_metadata
        }

    @property
    def is_expired(self) -> bool:
        """Check if file has expired."""
        return datetime.utcnow() > self.expires_at if self.expires_at else False

    def increment_download_count(self) -> None:
        """Increment download counter."""
        self.downloaded_count += 1

    @classmethod
    def cleanup_expired(cls) -> int:
        """Delete expired files. Returns count of deleted files."""
        expired = cls.query.filter(cls.expires_at < datetime.utcnow()).all()
        count = len(expired)
        for f in expired:
            db.session.delete(f)
        db.session.commit()
        return count


# =============================================================================
# PROJECT CONFIGURATION SCHEMA
# =============================================================================

DEFAULT_PROJECT_CONFIG = {
    "sf_connection": {
        "endpoint_url": None,
        "endpoint_name": None,
        "company_id": None,
        "username": None,
        "password_encrypted": None,
        "connected": False,
        "last_connected_at": None
    },
    "languages": {
        "selected": ["en_US"],  # English US always selected by default
        "available": []
    },
    "odata_objects": {
        "ec_fields": [],
        "foundation_objects": [],
        "mdf_objects": [],
        "picklists": {
            "legacy": [],
            "mdf": []
        }
    },
    "fo_translations": [],
    "export_options": {
        "include_empty": False,
        "sheet_per_model": True
    },
    "last_saved_at": None
}


def init_db(app):
    """Initialize database with Flask app."""
    db.init_app(app)
    with app.app_context():
        db.create_all()


def get_or_create_user(xsuaa_id: str, email: str, display_name: str = None, is_admin: bool = False) -> User:
    """Get existing user or create new one."""
    user = User.query.filter_by(xsuaa_id=xsuaa_id).first()
    if user:
        user.update_last_login()
        # Update admin status if changed
        if user.is_admin != is_admin:
            user.is_admin = is_admin
        db.session.commit()
        return user

    # Create new user
    user = User(
        xsuaa_id=xsuaa_id,
        email=email,
        display_name=display_name or email.split('@')[0],
        is_admin=is_admin
    )
    db.session.add(user)
    db.session.commit()
    return user
