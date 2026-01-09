"""
TREXIMA v4.0 - Export Blueprint

Handles translation export workflow:
1. Validates project configuration
2. Processes uploaded data model files
3. Connects to SF OData API
4. Extracts translations to Excel workbook
5. Stores result in Object Store

All operations emit real-time progress via WebSocket.
"""

from flask import Blueprint, jsonify, request, g
import logging
import os
import tempfile
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from trexima.web.auth import require_auth, get_current_user
from trexima.web.models import db, Project, ProjectFile, GeneratedFile, User, get_or_create_user
from trexima.web.storage import storage_service
from trexima.web.websocket import (
    ProgressTracker, is_operation_active, OperationCancelled
)
from trexima.web.constants import (
    FILE_RETENTION_DAYS, EC_CORE_OBJECTS, FOUNDATION_OBJECTS, FO_TRANSLATION_TYPES
)

# Core processing modules
from trexima.core.datamodel_processor import DataModelProcessor
from trexima.core.odata_client import ODataClient
from trexima.core.translation_extractor import TranslationExtractor
from trexima.config import AppPaths

logger = logging.getLogger(__name__)

export_bp = Blueprint('export', __name__)


def get_user_from_context():
    """Get or create database user from auth context."""
    user_context = get_current_user()
    return get_or_create_user(
        xsuaa_id=user_context.user_id,
        email=user_context.email,
        display_name=user_context.display_name,
        is_admin=user_context.is_admin
    )


# =============================================================================
# EXPORT WORKFLOW
# =============================================================================

@export_bp.route('/projects/<project_id>/export', methods=['POST'])
@require_auth
def start_export(project_id):
    """
    Start translation export for a project.

    Request body (optional overrides):
        {
            "locales": ["en_US", "de_DE", ...],
            "export_picklists": true,
            "export_mdf_objects": true,
            "export_fo_translations": true,
            "fo_translation_types": ["eventReason", "location", ...],
            "ec_objects": ["PerPersonal", "EmpJob", ...],
            "fo_objects": ["FOCompany", "FODepartment", ...]
        }

    Returns:
        - 202: Export started (check WebSocket for progress)
        - 400: Invalid configuration
        - 404: Project not found
        - 409: Export already in progress
    """
    user = get_user_from_context()
    project = Project.query.filter_by(id=project_id, user_id=user.id).first()

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    # Check for active operation
    if is_operation_active(project_id):
        return jsonify({
            'error': 'An operation is already in progress for this project'
        }), 409

    # Get project config
    config = project.config or {}
    request_data = request.get_json() or {}

    # Validate we have the minimum required data
    uploaded_files = ProjectFile.query.filter_by(project_id=project_id).all()
    if not uploaded_files:
        return jsonify({
            'error': 'No data model files uploaded. Please upload at least one XML file.'
        }), 400

    # Merge request overrides with project config
    export_config = {
        'locales': request_data.get('locales', config.get('locales', ['en_US'])),
        'export_picklists': request_data.get('export_picklists', config.get('export_picklists', True)),
        'export_mdf_objects': request_data.get('export_mdf_objects', config.get('export_mdf_objects', True)),
        'export_fo_translations': request_data.get('export_fo_translations', config.get('export_fo_translations', True)),
        'fo_translation_types': request_data.get('fo_translation_types', config.get('fo_translation_types', [])),
        'ec_objects': request_data.get('ec_objects', config.get('ec_objects', [])),
        'fo_objects': request_data.get('fo_objects', config.get('fo_objects', [])),
        'sf_connection': config.get('sf_connection', {})
    }

    # Update project status
    project.status = 'exporting'
    db.session.commit()

    # Start export in background (using socketio background task)
    from trexima.web.websocket import socketio
    socketio.start_background_task(
        _execute_export,
        project_id=project_id,
        user_id=user.id,
        uploaded_files=[(f.id, f.storage_key, f.file_type) for f in uploaded_files],
        export_config=export_config
    )

    return jsonify({
        'message': 'Export started',
        'project_id': project_id,
        'status': 'exporting'
    }), 202


def _execute_export(
    project_id: str,
    user_id: str,
    uploaded_files: List[tuple],
    export_config: dict
):
    """
    Execute export operation in background.

    This function runs in a background greenlet and emits progress via WebSocket.
    """
    from flask import current_app

    # Need app context for database operations
    from trexima.web.app import create_app
    app = create_app()

    with app.app_context():
        with ProgressTracker(project_id, 'export') as tracker:
            temp_dir = None
            try:
                # Step 1: Initialize
                tracker.update(1, "Initializing export environment")

                temp_dir = tempfile.mkdtemp(prefix='trexima_export_')
                app_paths = AppPaths(base_dir=temp_dir)
                processor = DataModelProcessor(app_paths)
                odata_client = ODataClient()

                # Step 2: Load data models
                tracker.update(2, "Loading data model files")

                loaded_count = 0
                for file_id, storage_key, file_type in uploaded_files:
                    if tracker.is_cancelled():
                        raise OperationCancelled("Export cancelled by user")

                    # Download file from storage
                    file_path = os.path.join(temp_dir, f"{file_id}.xml")
                    storage_service.download_file(storage_key, file_path)

                    # Load into processor
                    model = processor.load_data_model(file_path)
                    if model:
                        loaded_count += 1

                    tracker.update(
                        2,
                        f"Loaded {loaded_count} of {len(uploaded_files)} files",
                        sub_progress=loaded_count / len(uploaded_files)
                    )

                if loaded_count == 0:
                    raise ValueError("No valid data model files could be loaded")

                # Step 3: Connect to OData API (if credentials provided)
                sf_connection = export_config.get('sf_connection', {})
                api_connected = False

                if sf_connection.get('endpoint') and sf_connection.get('company_id'):
                    tracker.update(3, "Connecting to SuccessFactors OData API")

                    try:
                        api_connected = odata_client.connect(
                            service_url=sf_connection['endpoint'],
                            company_id=sf_connection['company_id'],
                            username=sf_connection.get('username', ''),
                            password=sf_connection.get('password', '')
                        )
                    except Exception as e:
                        logger.warning(f"OData connection failed: {e}")
                        tracker.update(3, f"API connection skipped: {str(e)}")
                else:
                    tracker.update(3, "Skipping API connection (no credentials)")

                # Step 4: Fetch locales
                tracker.update(4, "Determining export locales")

                locales = export_config.get('locales', ['en_US'])
                if api_connected:
                    try:
                        active_locales = odata_client.get_active_locales()
                        if active_locales:
                            # Merge with requested locales
                            locales = list(set(locales + active_locales))
                    except Exception:
                        pass

                # Ensure en_US is always first
                if 'en_US' in locales:
                    locales.remove('en_US')
                    locales.insert(0, 'en_US')

                # Create extractor with progress callback
                def progress_callback(percent: int, message: str):
                    # Map extractor progress (0-100) to our steps (5-9)
                    if percent <= 20:
                        tracker.update(5, message, sub_progress=percent / 20)
                    elif percent <= 40:
                        tracker.update(6, message, sub_progress=(percent - 20) / 20)
                    elif percent <= 60:
                        tracker.update(7, message, sub_progress=(percent - 40) / 20)
                    elif percent <= 80:
                        tracker.update(8, message, sub_progress=(percent - 60) / 20)
                    else:
                        tracker.update(9, message, sub_progress=(percent - 80) / 20)

                extractor = TranslationExtractor(
                    processor=processor,
                    odata_client=odata_client if api_connected else None,
                    progress_callback=progress_callback
                )

                # Step 5-9: Extract translations (handled by progress_callback)
                tracker.update(5, "Extracting EC field translations")

                workbook = extractor.extract_to_workbook(
                    locales_for_export=locales,
                    export_picklists=export_config.get('export_picklists', True),
                    export_mdf_objects=export_config.get('export_mdf_objects', True) and api_connected,
                    export_fo_translations=export_config.get('export_fo_translations', True) and api_connected,
                    system_default_lang='en_US'
                )

                # Step 10: Save and upload
                tracker.update(10, "Saving workbook and preparing download")

                # Save workbook to temp file
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                filename = f"TranslationsWorkbook_{timestamp}.xlsx"
                local_path = os.path.join(temp_dir, filename)
                extractor.save_workbook(workbook, temp_dir, filename)

                # Upload to storage
                storage_key = f"users/{user_id}/projects/{project_id}/generated/{filename}"
                storage_service.upload_file(local_path, storage_key)

                # Get file size
                file_size = os.path.getsize(local_path)

                # Create database record
                generated_file = GeneratedFile(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    filename=filename,
                    file_type='translation_workbook',
                    storage_key=storage_key,
                    file_size=file_size,
                    expires_at=datetime.utcnow() + timedelta(days=FILE_RETENTION_DAYS)
                )
                db.session.add(generated_file)

                # Update project status
                project = Project.query.get(project_id)
                if project:
                    project.status = 'exported'
                    project.updated_at = datetime.utcnow()

                db.session.commit()

                # Complete
                tracker.complete(result={
                    'file_id': generated_file.id,
                    'filename': filename,
                    'file_size': file_size,
                    'locales_exported': locales,
                    'files_processed': loaded_count
                })

            except OperationCancelled:
                # Reset project status
                project = Project.query.get(project_id)
                if project:
                    project.status = 'configured'
                    db.session.commit()
                tracker.fail("Export cancelled by user")

            except Exception as e:
                logger.exception(f"Export failed for project {project_id}")
                # Reset project status
                project = Project.query.get(project_id)
                if project:
                    project.status = 'configured'
                    db.session.commit()
                tracker.fail(str(e))

            finally:
                # Cleanup temp directory
                if temp_dir and os.path.exists(temp_dir):
                    import shutil
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception:
                        pass


# =============================================================================
# EXPORT STATUS & DOWNLOADS
# =============================================================================

@export_bp.route('/projects/<project_id>/export/status', methods=['GET'])
@require_auth
def get_export_status(project_id):
    """Get current export status for a project."""
    user = get_user_from_context()
    project = Project.query.filter_by(id=project_id, user_id=user.id).first()

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    active = is_operation_active(project_id)

    # Get latest generated file
    latest_file = GeneratedFile.query.filter_by(
        project_id=project_id,
        file_type='translation_workbook'
    ).order_by(GeneratedFile.created_at.desc()).first()

    return jsonify({
        'project_id': project_id,
        'status': project.status,
        'is_active': active,
        'latest_export': latest_file.to_dict() if latest_file else None
    })


@export_bp.route('/projects/<project_id>/export/cancel', methods=['POST'])
@require_auth
def cancel_export(project_id):
    """Cancel an in-progress export."""
    user = get_user_from_context()
    project = Project.query.filter_by(id=project_id, user_id=user.id).first()

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    from trexima.web.websocket import cancel_operation

    if cancel_operation(project_id):
        return jsonify({
            'message': 'Cancellation requested',
            'project_id': project_id
        })
    else:
        return jsonify({
            'error': 'No active export to cancel'
        }), 404


# =============================================================================
# EXPORT CONFIGURATION HELPERS
# =============================================================================

@export_bp.route('/export/ec-objects', methods=['GET'])
@require_auth
def list_ec_objects():
    """List available EC objects for export."""
    return jsonify({
        'ec_objects': EC_CORE_OBJECTS
    })


@export_bp.route('/export/fo-objects', methods=['GET'])
@require_auth
def list_fo_objects():
    """List available Foundation objects for export."""
    return jsonify({
        'fo_objects': FOUNDATION_OBJECTS
    })


@export_bp.route('/export/fo-translation-types', methods=['GET'])
@require_auth
def list_fo_translation_types():
    """List available FO translation types."""
    return jsonify({
        'fo_translation_types': FO_TRANSLATION_TYPES
    })
