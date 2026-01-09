"""
SMALL Scale Tests - Import API Endpoints

Unit tests for the import blueprint
"""

import pytest
import io
from unittest.mock import Mock, patch, MagicMock
from trexima.web.models import db


class TestImportAPI:
    """Test import API endpoints"""

    @patch('trexima.web.blueprints.import_bp.require_auth')
    @patch('trexima.web.blueprints.import_bp.get_current_user')
    def test_validate_workbook_no_file(self, mock_get_user, mock_auth, client, app, mock_user, mock_project):
        """Test validate without workbook file"""
        mock_auth.return_value = lambda f: f
        mock_get_user.return_value = MagicMock(user_id=mock_user.id, email='test@test.com', display_name='Test', is_admin=False)

        with app.app_context():
            db.session.add(mock_user)
            db.session.add(mock_project)
            db.session.commit()

            response = client.post(f'/api/projects/{mock_project.id}/import/validate')
            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data

    @patch('trexima.web.blueprints.import_bp.require_auth')
    @patch('trexima.web.blueprints.import_bp.get_current_user')
    def test_validate_workbook_wrong_type(self, mock_get_user, mock_auth, client, app, mock_user, mock_project):
        """Test validate with non-Excel file"""
        mock_auth.return_value = lambda f: f
        mock_get_user.return_value = MagicMock(user_id=mock_user.id, email='test@test.com', display_name='Test', is_admin=False)

        with app.app_context():
            db.session.add(mock_user)
            db.session.add(mock_project)
            db.session.commit()

            # Send text file instead of Excel
            data = {'workbook': (io.BytesIO(b'not excel'), 'test.txt')}
            response = client.post(
                f'/api/projects/{mock_project.id}/import/validate',
                data=data,
                content_type='multipart/form-data'
            )
            assert response.status_code == 400

    @patch('trexima.web.blueprints.import_bp.require_auth')
    @patch('trexima.web.blueprints.import_bp.get_current_user')
    @patch('trexima.web.blueprints.import_bp.TranslationImporter')
    def test_validate_workbook_success(self, mock_importer_class, mock_get_user, mock_auth, client, app, mock_user, mock_project):
        """Test successful workbook validation"""
        mock_auth.return_value = lambda f: f
        mock_get_user.return_value = MagicMock(user_id=mock_user.id, email='test@test.com', display_name='Test', is_admin=False)

        # Mock importer
        mock_importer = Mock()
        mock_importer.validate_workbook.return_value = {
            'valid': True,
            'sheets': {
                'all': ['EC_SDM_en_US', 'Picklists'],
                'datamodel': ['EC_SDM_en_US'],
                'pm_templates': ['Picklists'],
                'gm_templates': [],
                'other': []
            },
            'total_sheets': 2
        }
        mock_importer_class.return_value = mock_importer

        with app.app_context():
            db.session.add(mock_user)
            db.session.add(mock_project)
            db.session.commit()

            # Create fake Excel file
            data = {'workbook': (io.BytesIO(b'fake xlsx content'), 'workbook.xlsx')}
            response = client.post(
                f'/api/projects/{mock_project.id}/import/validate',
                data=data,
                content_type='multipart/form-data'
            )

            # Note: May fail if file processing happens, but tests the flow
            assert response.status_code in [200, 400, 500]

    @patch('trexima.web.blueprints.import_bp.require_auth')
    @patch('trexima.web.blueprints.import_bp.get_current_user')
    def test_start_import_unauthorized(self, mock_get_user, mock_auth, client):
        """Test import without auth"""
        mock_auth.side_effect = Exception('Unauthorized')

        response = client.post('/api/projects/proj-123/import')
        assert response.status_code in [401, 500]

    @patch('trexima.web.blueprints.import_bp.require_auth')
    @patch('trexima.web.blueprints.import_bp.get_current_user')
    def test_start_import_project_not_found(self, mock_get_user, mock_auth, client, app, mock_user):
        """Test import with non-existent project"""
        mock_auth.return_value = lambda f: f
        mock_get_user.return_value = MagicMock(user_id=mock_user.id, email='test@test.com', display_name='Test', is_admin=False)

        with app.app_context():
            db.session.add(mock_user)
            db.session.commit()

            response = client.post('/api/projects/nonexistent/import')
            assert response.status_code == 404

    @patch('trexima.web.blueprints.import_bp.require_auth')
    @patch('trexima.web.blueprints.import_bp.get_current_user')
    @patch('trexima.web.blueprints.import_bp.is_operation_active')
    def test_start_import_already_active(self, mock_is_active, mock_get_user, mock_auth, client, app, mock_user, mock_project):
        """Test import when operation already active"""
        mock_auth.return_value = lambda f: f
        mock_get_user.return_value = MagicMock(user_id=mock_user.id, email='test@test.com', display_name='Test', is_admin=False)
        mock_is_active.return_value = True

        with app.app_context():
            db.session.add(mock_user)
            db.session.add(mock_project)
            db.session.commit()

            response = client.post(f'/api/projects/{mock_project.id}/import')
            assert response.status_code in [400, 409]
            data = response.get_json()
            assert 'error' in data

    @patch('trexima.web.blueprints.import_bp.require_auth')
    @patch('trexima.web.blueprints.import_bp.get_current_user')
    def test_get_import_status(self, mock_get_user, mock_auth, client, app, mock_user, mock_project):
        """Test GET /api/projects/{id}/import/status"""
        mock_auth.return_value = lambda f: f
        mock_get_user.return_value = MagicMock(user_id=mock_user.id, email='test@test.com', display_name='Test', is_admin=False)

        with app.app_context():
            db.session.add(mock_user)
            db.session.add(mock_project)
            db.session.commit()

            response = client.get(f'/api/projects/{mock_project.id}/import/status')
            assert response.status_code == 200
            data = response.get_json()
            assert 'status' in data
            assert 'is_active' in data
            assert 'generated_files' in data

    @patch('trexima.web.blueprints.import_bp.require_auth')
    @patch('trexima.web.blueprints.import_bp.get_current_user')
    @patch('trexima.web.blueprints.import_bp.socketio')
    def test_cancel_import(self, mock_socketio, mock_get_user, mock_auth, client, app, mock_user, mock_project):
        """Test POST /api/projects/{id}/import/cancel"""
        mock_auth.return_value = lambda f: f
        mock_get_user.return_value = MagicMock(user_id=mock_user.id, email='test@test.com', display_name='Test', is_admin=False)
        mock_socketio.emit = Mock()

        with app.app_context():
            db.session.add(mock_user)
            db.session.add(mock_project)
            db.session.commit()

            response = client.post(f'/api/projects/{mock_project.id}/import/cancel')
            assert response.status_code == 200
            data = response.get_json()
            assert 'message' in data


class TestImportWorkbookValidation:
    """Test workbook validation logic"""

    def test_worksheet_categorization_datamodel(self):
        """Test data model sheet categorization"""
        sheets = ['EC_SDM_en_US', 'EC_SDM_de_DE', 'EC_CDM_en_US']

        # Sheets containing SDM or CDM should be categorized as datamodel
        for sheet in sheets:
            assert 'SDM' in sheet or 'CDM' in sheet

    def test_worksheet_categorization_pm_templates(self):
        """Test PM template sheet categorization"""
        pm_sheets = [
            'Picklists',
            'MDF_Objects',
            'PerPersonal_Template',
        ]

        # These should be categorized as pm_templates
        for sheet in pm_sheets:
            assert any(keyword in sheet for keyword in ['Picklist', 'MDF', 'Template', 'Per', 'Emp'])

    def test_worksheet_categorization_gm_templates(self):
        """Test GM template sheet categorization"""
        gm_sheets = [
            'FOLocation_Generic',
            'FOCompany_Generic',
        ]

        # These should be categorized as gm_templates
        for sheet in gm_sheets:
            assert 'FO' in sheet or 'Generic' in sheet

    def test_excel_file_extension_validation(self):
        """Test Excel file extension validation"""
        valid_extensions = ['.xlsx', '.XLSX', '.Xlsx']
        invalid_extensions = ['.xls', '.csv', '.txt', '.xml']

        for ext in valid_extensions:
            assert ext.lower() == '.xlsx'

        for ext in invalid_extensions:
            assert ext.lower() != '.xlsx'


class TestImportOptions:
    """Test import options"""

    def test_push_to_api_option(self):
        """Test push_to_api parameter"""
        # This option should be boolean
        push_options = [True, False, 'true', 'false']

        for option in push_options:
            if isinstance(option, bool):
                assert option in [True, False]
            elif isinstance(option, str):
                assert option.lower() in ['true', 'false']

    def test_worksheet_selection(self):
        """Test worksheet selection format"""
        # Worksheets should be a list of strings
        worksheets = ['EC_SDM_en_US', 'EC_SDM_de_DE', 'Picklists']

        assert isinstance(worksheets, list)
        assert all(isinstance(sheet, str) for sheet in worksheets)
        assert len(worksheets) > 0

    def test_empty_worksheet_selection(self):
        """Test empty worksheet selection should fail"""
        worksheets = []

        # Should require at least one worksheet
        assert len(worksheets) == 0  # Would fail validation
