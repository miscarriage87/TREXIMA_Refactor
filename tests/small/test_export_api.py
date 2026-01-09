"""
SMALL Scale Tests - Export API Endpoints

Unit tests for the export blueprint
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from trexima.web.models import db


class TestExportAPI:
    """Test export API endpoints"""

    def test_get_ec_objects(self, client):
        """Test GET /api/export/ec-objects"""
        response = client.get('/api/export/ec-objects')

        assert response.status_code == 200
        data = response.get_json()
        assert 'ec_objects' in data
        assert len(data['ec_objects']) > 0
        assert data['ec_objects'][0]['id'] == 'PerPersonal'
        assert data['ec_objects'][0]['name'] == 'Personal Information'

    def test_get_fo_objects(self, client):
        """Test GET /api/export/fo-objects"""
        response = client.get('/api/export/fo-objects')

        assert response.status_code == 200
        data = response.get_json()
        assert 'fo_objects' in data
        assert len(data['fo_objects']) > 0
        assert any(obj['id'] == 'FOCompany' for obj in data['fo_objects'])

    def test_get_fo_translation_types(self, client):
        """Test GET /api/export/fo-translation-types"""
        response = client.get('/api/export/fo-translation-types')

        assert response.status_code == 200
        data = response.get_json()
        assert 'fo_translation_types' in data
        assert len(data['fo_translation_types']) > 0

        # Check structure
        first_type = data['fo_translation_types'][0]
        assert 'id' in first_type
        assert 'name' in first_type
        assert 'object' in first_type
        assert 'field' in first_type
        assert 'description' in first_type

    @patch('trexima.web.blueprints.export_bp.require_auth')
    @patch('trexima.web.blueprints.export_bp.get_current_user')
    def test_start_export_unauthorized(self, mock_get_user, mock_auth, client, app):
        """Test export without auth"""
        mock_auth.side_effect = Exception('Unauthorized')

        response = client.post('/api/projects/proj-123/export')
        # Should fail due to auth
        assert response.status_code in [401, 500]

    @patch('trexima.web.blueprints.export_bp.require_auth')
    @patch('trexima.web.blueprints.export_bp.get_current_user')
    @patch('trexima.web.blueprints.export_bp.socketio')
    def test_start_export_project_not_found(self, mock_socketio, mock_get_user, mock_auth, client, app, mock_user):
        """Test export with non-existent project"""
        mock_auth.return_value = lambda f: f
        mock_get_user.return_value = MagicMock(user_id='user-123', email='test@test.com', display_name='Test', is_admin=False)

        with app.app_context():
            response = client.post('/api/projects/nonexistent/export')
            assert response.status_code == 404

    @patch('trexima.web.blueprints.export_bp.require_auth')
    @patch('trexima.web.blueprints.export_bp.get_current_user')
    @patch('trexima.web.blueprints.export_bp.is_operation_active')
    @patch('trexima.web.blueprints.export_bp.socketio')
    def test_start_export_already_active(self, mock_socketio, mock_is_active, mock_get_user, mock_auth, client, app, mock_user, mock_project):
        """Test export when operation already active"""
        mock_auth.return_value = lambda f: f
        mock_get_user.return_value = MagicMock(user_id=mock_user.id, email='test@test.com', display_name='Test', is_admin=False)
        mock_is_active.return_value = True

        with app.app_context():
            db.session.add(mock_user)
            db.session.add(mock_project)
            db.session.commit()

            response = client.post(f'/api/projects/{mock_project.id}/export')
            assert response.status_code == 409
            data = response.get_json()
            assert 'error' in data
            assert 'already in progress' in data['error'].lower()

    @patch('trexima.web.blueprints.export_bp.require_auth')
    @patch('trexima.web.blueprints.export_bp.get_current_user')
    def test_get_export_status(self, mock_get_user, mock_auth, client, app, mock_user, mock_project):
        """Test GET /api/projects/{id}/export/status"""
        mock_auth.return_value = lambda f: f
        mock_get_user.return_value = MagicMock(user_id=mock_user.id, email='test@test.com', display_name='Test', is_admin=False)

        with app.app_context():
            db.session.add(mock_user)
            db.session.add(mock_project)
            db.session.commit()

            response = client.get(f'/api/projects/{mock_project.id}/export/status')
            assert response.status_code == 200
            data = response.get_json()
            assert 'status' in data
            assert 'is_active' in data

    @patch('trexima.web.blueprints.export_bp.require_auth')
    @patch('trexima.web.blueprints.export_bp.get_current_user')
    @patch('trexima.web.blueprints.export_bp.socketio')
    def test_cancel_export(self, mock_socketio, mock_get_user, mock_auth, client, app, mock_user, mock_project):
        """Test POST /api/projects/{id}/export/cancel"""
        mock_auth.return_value = lambda f: f
        mock_get_user.return_value = MagicMock(user_id=mock_user.id, email='test@test.com', display_name='Test', is_admin=False)
        mock_socketio.emit = Mock()

        with app.app_context():
            db.session.add(mock_user)
            db.session.add(mock_project)
            db.session.commit()

            response = client.post(f'/api/projects/{mock_project.id}/export/cancel')
            assert response.status_code == 200
            data = response.get_json()
            assert 'message' in data

    def test_export_constants_loaded(self, app):
        """Test that export constants are properly loaded"""
        with app.app_context():
            from trexima.web.constants import EC_CORE_OBJECTS, FOUNDATION_OBJECTS, FO_TRANSLATION_TYPES

            # EC Objects
            assert len(EC_CORE_OBJECTS) >= 20
            assert any(obj['id'] == 'PerPersonal' for obj in EC_CORE_OBJECTS)
            assert any(obj['id'] == 'EmpJob' for obj in EC_CORE_OBJECTS)

            # FO Objects
            assert len(FOUNDATION_OBJECTS) >= 19
            assert any(obj['id'] == 'FOCompany' for obj in FOUNDATION_OBJECTS)
            assert any(obj['id'] == 'FOLocation' for obj in FOUNDATION_OBJECTS)

            # FO Translation Types
            assert len(FO_TRANSLATION_TYPES) == 9
            assert any(t['id'] == 'eventReason' for t in FO_TRANSLATION_TYPES)
            assert any(t['id'] == 'location' for t in FO_TRANSLATION_TYPES)


class TestExportConfiguration:
    """Test export configuration validation"""

    def test_ec_objects_validation(self, app):
        """Test EC objects are valid"""
        with app.app_context():
            from trexima.web.constants import EC_CORE_OBJECTS

            for obj in EC_CORE_OBJECTS:
                assert 'id' in obj
                assert 'name' in obj
                assert 'description' in obj
                assert isinstance(obj['id'], str)
                assert isinstance(obj['name'], str)

    def test_fo_translation_types_validation(self, app):
        """Test FO translation types are valid"""
        with app.app_context():
            from trexima.web.constants import FO_TRANSLATION_TYPES

            for ft in FO_TRANSLATION_TYPES:
                assert 'id' in ft
                assert 'name' in ft
                assert 'object' in ft
                assert 'field' in ft
                assert 'description' in ft
                assert ft['field'] == 'name'  # All should use 'name' field

    def test_locale_names_available(self, app):
        """Test locale names are defined"""
        with app.app_context():
            from trexima.web.constants import LOCALE_NAMES

            assert len(LOCALE_NAMES) >= 40
            assert 'en_US' in LOCALE_NAMES
            assert 'de_DE' in LOCALE_NAMES
            assert 'fr_FR' in LOCALE_NAMES
            assert 'zh_CN' in LOCALE_NAMES
            assert 'ja_JP' in LOCALE_NAMES
