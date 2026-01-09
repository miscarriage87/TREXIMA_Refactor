"""
TREXIMA Web Routes

API routes and page handlers for the web application.
"""

import os
import time
import json
from typing import Dict, Any, Optional

from flask import (
    Blueprint, render_template, request, jsonify,
    current_app, send_file, session
)
from werkzeug.utils import secure_filename

from trexima.config import APP_NAME, VERSION, AppPaths, AppState
from trexima.io.xml_handler import XMLHandler
from trexima.io.excel_handler import ExcelHandler
from trexima.io.csv_handler import CSVHandler
from trexima.core.datamodel_processor import DataModelProcessor
from trexima.core.translation_extractor import TranslationExtractor
from trexima.core.translation_importer import TranslationImporter
from trexima.core.odata_client import ODataClient

# Blueprints
main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Global state (in production, use proper session management)
app_state: Dict[str, Any] = {
    'processor': None,
    'odata_client': None,
    'extractor': None,
    'importer': None,
    'progress': {'percent': 0, 'message': 'Ready'},
    'files_loaded': [],
    'last_export_path': None,
    'last_import_result': None
}


def get_processor() -> DataModelProcessor:
    """Get or create the data model processor."""
    if app_state['processor'] is None:
        app_state['processor'] = DataModelProcessor()
    return app_state['processor']


def get_odata_client() -> ODataClient:
    """Get or create the OData client."""
    if app_state['odata_client'] is None:
        app_state['odata_client'] = ODataClient()
    return app_state['odata_client']


def update_progress(percent: int, message: str):
    """Update progress state."""
    app_state['progress'] = {'percent': percent, 'message': message}


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def register_routes(app):
    """Register all routes with the Flask app."""
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)


# ==================== Main Routes ====================

@main_bp.route('/legacy')
def legacy_index():
    """Legacy main page (deprecated - use React app at /)."""
    return render_template('index.html')


@main_bp.route('/export')
def export_page():
    """Export translations page."""
    return render_template('export.html')


@main_bp.route('/import')
def import_page():
    """Import translations page."""
    return render_template('import.html')


@main_bp.route('/settings')
def settings_page():
    """Settings page."""
    return render_template('settings.html')


# ==================== API Routes ====================

@api_bp.route('/status')
def api_status():
    """Get application status."""
    processor = get_processor()
    odata = get_odata_client()

    return jsonify({
        'app_name': APP_NAME,
        'version': VERSION,
        'files_loaded': len(app_state['files_loaded']),
        'odata_connected': odata.is_connected,
        'is_pmgm_included': processor.is_pmgm_included,
        'is_sdm_included': processor.is_sdm_included,
        'progress': app_state['progress']
    })


@api_bp.route('/progress')
def api_progress():
    """Get current progress."""
    return jsonify(app_state['progress'])


@api_bp.route('/upload', methods=['POST'])
def api_upload():
    """Upload XML files."""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files')
    uploaded = []
    errors = []

    processor = get_processor()
    upload_folder = current_app.config['UPLOAD_FOLDER']

    for file in files:
        if file.filename == '':
            continue

        if file and allowed_file(file.filename, {'xml'}):
            filename = secure_filename(file.filename)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)

            # Load the data model
            model = processor.load_data_model(filepath)
            if model:
                uploaded.append({
                    'filename': filename,
                    'name': model.name,
                    'type': model.get_type_name()
                })
                app_state['files_loaded'].append(filepath)
            else:
                errors.append(f"{filename}: Could not parse as SF data model")
        else:
            errors.append(f"{file.filename}: Invalid file type")

    return jsonify({
        'uploaded': uploaded,
        'errors': errors,
        'total_loaded': len(app_state['files_loaded'])
    })


@api_bp.route('/upload/standard', methods=['POST'])
def api_upload_standard():
    """Load standard SAP data models."""
    processor = get_processor()
    app_paths = AppPaths()

    loaded = []
    for path in app_paths.get_standard_dm_paths():
        if os.path.exists(path):
            model = processor.load_data_model(path, is_standard=True)
            if model:
                loaded.append({
                    'name': model.name,
                    'type': model.get_type_name()
                })

    return jsonify({
        'loaded': loaded,
        'count': len(loaded)
    })


@api_bp.route('/odata/connect', methods=['POST'])
def api_odata_connect():
    """Connect to OData service."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No credentials provided'}), 400

    required = ['service_url', 'company_id', 'username', 'password']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400

    odata = get_odata_client()

    try:
        odata.connect(
            service_url=data['service_url'],
            company_id=data['company_id'],
            username=data['username'],
            password=data['password']
        )
        return jsonify({
            'success': True,
            'message': 'Connected to OData service'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@api_bp.route('/odata/disconnect', methods=['POST'])
def api_odata_disconnect():
    """Disconnect from OData service."""
    odata = get_odata_client()
    odata.disconnect()
    return jsonify({'success': True})


@api_bp.route('/odata/locales')
def api_odata_locales():
    """Get active locales from OData service."""
    odata = get_odata_client()

    if not odata.is_connected:
        # Return default locales
        return jsonify({
            'locales': ['en_US', 'de_DE', 'fr_FR', 'es_ES', 'ja_JP', 'zh_CN'],
            'from_api': False
        })

    locales = odata.get_active_locales()
    return jsonify({
        'locales': locales if locales else ['en_US'],
        'from_api': True
    })


@api_bp.route('/export', methods=['POST'])
def api_export():
    """Execute export operation."""
    data = request.get_json() or {}

    processor = get_processor()

    if len(app_state['files_loaded']) == 0:
        return jsonify({'error': 'No files loaded'}), 400

    # Get export options
    locales = data.get('locales', ['en_US'])
    export_picklists = data.get('export_picklists', True)
    export_mdf = data.get('export_mdf', False)
    export_fo = data.get('export_fo', True)
    remove_html = data.get('remove_html', False)
    default_lang = data.get('default_lang', 'en_US')

    # Create extractor
    odata = get_odata_client()
    extractor = TranslationExtractor(
        processor,
        odata if odata.is_connected else None,
        update_progress
    )

    try:
        update_progress(10, 'Starting export...')

        # Execute export
        workbook = extractor.extract_to_workbook(
            locales_for_export=locales,
            export_picklists=export_picklists,
            export_mdf_objects=export_mdf,
            export_fo_translations=export_fo,
            remove_html_tags=remove_html,
            system_default_lang=default_lang
        )

        # Save workbook
        output_folder = current_app.config['OUTPUT_FOLDER']
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"SF_Translations_{timestamp}.xlsx"
        filepath = os.path.join(output_folder, filename)

        extractor.save_workbook(workbook, output_folder, filename)
        app_state['last_export_path'] = filepath

        update_progress(100, 'Export complete!')

        return jsonify({
            'success': True,
            'filename': filename,
            'download_url': f'/api/download/{filename}'
        })

    except Exception as e:
        update_progress(0, f'Export failed: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/import', methods=['POST'])
def api_import():
    """Execute import operation."""
    if 'workbook' not in request.files:
        return jsonify({'error': 'No workbook provided'}), 400

    file = request.files['workbook']
    if not file or not allowed_file(file.filename, {'xlsx'}):
        return jsonify({'error': 'Invalid file type'}), 400

    processor = get_processor()

    if len(app_state['files_loaded']) == 0:
        return jsonify({'error': 'No XML files loaded'}), 400

    upload_folder = current_app.config['UPLOAD_FOLDER']
    output_folder = current_app.config['OUTPUT_FOLDER']

    # Save uploaded workbook
    filename = secure_filename(file.filename)
    wb_path = os.path.join(upload_folder, filename)
    file.save(wb_path)

    # Get sheets to process
    data = request.form.to_dict()
    sheets_to_process = json.loads(data.get('sheets', '[]'))

    try:
        update_progress(10, 'Starting import...')

        # Load workbook
        excel_handler = ExcelHandler()
        workbook = excel_handler.load_workbook(wb_path)

        if not sheets_to_process:
            sheets_to_process = workbook.sheetnames

        # Create importer
        importer = TranslationImporter(processor, update_progress)

        # Execute import
        result = importer.import_from_workbook(
            workbook,
            sheets_to_process,
            output_folder
        )

        app_state['last_import_result'] = result

        update_progress(100, 'Import complete!')

        return jsonify({
            'success': result.success,
            'files_generated': [os.path.basename(f) for f in result.files_generated],
            'changes_made': result.changes_made,
            'log_file': os.path.basename(result.log_file_path) if result.log_file_path else None
        })

    except Exception as e:
        update_progress(0, f'Import failed: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/download/<filename>')
def api_download(filename):
    """Download a file from the output folder."""
    filename = secure_filename(filename)
    output_folder = current_app.config['OUTPUT_FOLDER']
    filepath = os.path.join(output_folder, filename)

    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    return send_file(
        filepath,
        as_attachment=True,
        download_name=filename
    )


@api_bp.route('/datamodels')
def api_datamodels():
    """Get list of loaded data models."""
    processor = get_processor()
    models = processor.get_all_data_models(include_standard=True)

    return jsonify({
        'models': [
            {
                'name': m.name,
                'type': m.get_type_name(),
                'is_standard': m.is_standard,
                'languages': len(m.extract_languages())
            }
            for m in models
        ],
        'total': len(models)
    })


@api_bp.route('/reset', methods=['POST'])
def api_reset():
    """Reset application state."""
    global app_state

    # Clear state
    app_state = {
        'processor': None,
        'odata_client': None,
        'extractor': None,
        'importer': None,
        'progress': {'percent': 0, 'message': 'Ready'},
        'files_loaded': [],
        'last_export_path': None,
        'last_import_result': None
    }

    return jsonify({'success': True, 'message': 'Application state reset'})
