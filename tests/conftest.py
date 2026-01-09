"""
Pytest Configuration for TREXIMA Backend Tests
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, MagicMock

@pytest.fixture
def app():
    """Create test Flask app"""
    from trexima.web.app import create_app

    # Use in-memory SQLite for testing
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
    }

    app = create_app(config=test_config, testing=True)

    with app.app_context():
        from trexima.web.models import db
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    from trexima.web.models import User

    user = User(
        id='test-user-123',
        xsuaa_id='xsuaa-123',
        email='test@example.com',
        display_name='Test User',
        is_admin=False
    )
    return user


@pytest.fixture
def mock_admin_user():
    """Mock admin user"""
    from trexima.web.models import User

    user = User(
        id='admin-user-123',
        xsuaa_id='xsuaa-admin',
        email='admin@example.com',
        display_name='Admin User',
        is_admin=True
    )
    return user


@pytest.fixture
def mock_project(mock_user):
    """Mock project"""
    from trexima.web.models import Project, DEFAULT_PROJECT_CONFIG

    project = Project(
        id='proj-123',
        name='Test Project',
        description='Test project for unit tests',
        user_id=mock_user.id,
        status='draft',
        config=DEFAULT_PROJECT_CONFIG.copy()
    )
    return project


@pytest.fixture
def mock_storage():
    """Mock storage service"""
    storage = Mock()
    storage.upload_file = Mock(return_value='s3://bucket/file-123')
    storage.download_file = Mock(return_value=b'file content')
    storage.delete_file = Mock()
    storage.generate_presigned_url = Mock(return_value='https://s3.example.com/file')
    return storage


@pytest.fixture
def mock_socketio():
    """Mock SocketIO"""
    socketio = Mock()
    socketio.emit = Mock()
    socketio.start_background_task = Mock()
    return socketio


@pytest.fixture
def temp_file():
    """Create temporary file for testing"""
    fd, path = tempfile.mkstemp(suffix='.xml')
    with os.fdopen(fd, 'w') as f:
        f.write('<?xml version="1.0"?><root><test>data</test></root>')

    yield path

    if os.path.exists(path):
        os.unlink(path)
