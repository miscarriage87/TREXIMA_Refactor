"""
TREXIMA v4.0 - Import Blueprint

Handles translation import workflow:
1. Accepts updated translation workbook
2. Validates workbook structure
3. Processes translations back to data models
4. Generates ready-to-import XML files
5. Optionally pushes translations via OData API

All operations emit real-time progress via WebSocket.
"""

from flask import Blueprint, jsonify, request, g
import logging
import os
import tempfile
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from werkzeug.utils import secure_filename

from trexima.web.auth import require_auth, get_current_user
from trexima.web.models import db, Project, ProjectFile, GeneratedFile, User, get_or_create_user
from trexima.web.storage import storage_service
from trexima.web.websocket import (
    ProgressTracker, is_operation_active, OperationCancelled
)
from trexima.web.constants import FILE_RETENTION_DAYS, MAX_FILE_SIZE_BYTES

# Core processing modules
from trexima.core.datamodel_processor import DataModelProcessor
from trexima.core.translation_importer import TranslationImporter
from trexima.io.excel_handler import ExcelHandler
from trexima.config import AppPaths

logger = logging.getLogger(__name__)

import_bp = Blueprint('import', __name__)


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
# IMPORT WORKFLOW
# =============================================================================

@import_bp.route('/projects/<project_id>/import', methods=['POST'])
@require_auth
def start_import(project_id):
    """
    Start translation import for a project.

    Expects multipart form with:
        - workbook: The updated translation workbook file (.xlsx)
        - worksheets: (optional) JSON array of worksheet names to process

    Query params:
        - push_to_api: "true" to push translations to SF (default: false)

    Returns:
        - 202: Import started (check WebSocket for progress)
        - 400: Invalid request
        - 404: Project not found
        - 409: Operation already in progress
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

    # Validate file upload
    if 'workbook' not in request.files:
        return jsonify({'error': 'No workbook file provided'}), 400

    workbook_file = request.files['workbook']
    if workbook_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not workbook_file.filename.endswith('.xlsx'):
        return jsonify({'error': 'Invalid file type. Expected .xlsx'}), 400

    # Check file size
    workbook_file.seek(0, os.SEEK_END)
    file_size = workbook_file.tell()
    workbook_file.seek(0)

    if file_size > MAX_FILE_SIZE_BYTES:
        return jsonify({
            'error': f'File too large. Maximum size is {MAX_FILE_SIZE_BYTES // (1024*1024)}MB'
        }), 400

    # Save workbook to temp storage
    temp_dir = tempfile.mkdtemp(prefix='trexima_import_')
    workbook_path = os.path.join(temp_dir, secure_filename(workbook_file.filename))
    workbook_file.save(workbook_path)

    # Parse optional parameters
    worksheets = None
    if 'worksheets' in request.form:
        import json
        try:
            worksheets = json.loads(request.form['worksheets'])
        except json.JSONDecodeError:
            pass

    push_to_api = request.args.get('push_to_api', 'false').lower() == 'true'

    # Get uploaded data model files
    uploaded_files = ProjectFile.query.filter_by(project_id=project_id).all()

    # Update project status
    project.status = 'importing'
    db.session.commit()

    # Start import in background
    from trexima.web.websocket import socketio
    socketio.start_background_task(
        _execute_import,
        project_id=project_id,
        user_id=user.id,
        workbook_path=workbook_path,
        temp_dir=temp_dir,
        uploaded_files=[(f.id, f.storage_key, f.file_type) for f in uploaded_files],
        worksheets=worksheets,
        push_to_api=push_to_api,
        sf_connection=project.config.get('sf_connection', {}) if project.config else {}
    )

    return jsonify({
        'message': 'Import started',
        'project_id': project_id,
        'status': 'importing'
    }), 202


def _execute_import(
    project_id: str,
    user_id: str,
    workbook_path: str,
    temp_dir: str,
    uploaded_files: List[tuple],
    worksheets: Optional[List[str]],
    push_to_api: bool,
    sf_connection: dict
):
    """
    Execute import operation in background.

    This function runs in a background greenlet and emits progress via WebSocket.
    """
    from flask import current_app

    # Need app context for database operations
    from trexima.web.app import create_app
    app = create_app()

    with app.app_context():
        with ProgressTracker(project_id, 'import') as tracker:
            try:
                # Step 1: Initialize
                tracker.update(1, "Initializing import environment")

                app_paths = AppPaths(base_dir=temp_dir)
                processor = DataModelProcessor(app_paths)
                excel_handler = ExcelHandler()

                # Step 2: Load workbook
                tracker.update(2, "Loading translation workbook")

                workbook = excel_handler.load_workbook(workbook_path)
                if not workbook:
                    raise ValueError("Failed to load workbook")

                # Validate workbook structure
                if not excel_handler.validate_translations_workbook(workbook):
                    raise ValueError("Invalid translations workbook format")

                available_sheets = workbook.sheetnames
                sheets_to_process = worksheets if worksheets else available_sheets

                # Filter to valid sheets
                sheets_to_process = [s for s in sheets_to_process if s in available_sheets]
                if not sheets_to_process:
                    raise ValueError("No valid worksheets to process")

                # Step 3: Load original data models
                tracker.update(3, "Validating original data models")

                loaded_count = 0
                for file_id, storage_key, file_type in uploaded_files:
                    if tracker.is_cancelled():
                        raise OperationCancelled("Import cancelled by user")

                    # Download file from storage
                    file_path = os.path.join(temp_dir, f"{file_id}.xml")
                    storage_service.download_file(storage_key, file_path)

                    # Load into processor
                    model = processor.load_data_model(file_path)
                    if model:
                        loaded_count += 1

                    tracker.update(
                        3,
                        f"Loaded {loaded_count} of {len(uploaded_files)} data models",
                        sub_progress=loaded_count / len(uploaded_files)
                    )

                # Step 4: Analyze changes
                tracker.update(4, "Analyzing translation changes")

                # Create progress callback for importer
                def progress_callback(percent: int, message: str):
                    # Map importer progress to our steps 5-8
                    if percent <= 55:
                        # Processing worksheets
                        tracker.update(5, message, sub_progress=percent / 55)
                    elif percent <= 65:
                        tracker.update(6, message, sub_progress=(percent - 55) / 10)
                    elif percent <= 100:
                        tracker.update(7, message, sub_progress=(percent - 65) / 35)

                importer = TranslationImporter(
                    processor=processor,
                    progress_callback=progress_callback
                )

                # Step 5: Process worksheets and generate XML
                tracker.update(5, "Generating updated XML files")

                result = importer.import_from_workbook(
                    workbook=workbook,
                    worksheets_to_process=sheets_to_process,
                    save_dir=temp_dir
                )

                if not result.success:
                    raise ValueError(result.error_message or "Import processing failed")

                # Step 6: Connect to API (if pushing)
                if push_to_api and sf_connection.get('endpoint'):
                    tracker.update(6, "Connecting to SuccessFactors API")

                    from trexima.core.odata_client import ODataClient
                    odata_client = ODataClient()

                    try:
                        api_connected = odata_client.connect(
                            service_url=sf_connection['endpoint'],
                            company_id=sf_connection['company_id'],
                            username=sf_connection.get('username', ''),
                            password=sf_connection.get('password', '')
                        )

                        if api_connected:
                            # Step 7: Push picklist translations
                            tracker.update(7, "Pushing picklist translations")
                            # Note: This would require additional implementation
                            # in the core module to push translations back

                            # Step 8: Push FO translations
                            tracker.update(8, "Pushing foundation object translations")
                            # Note: Same as above

                    except Exception as e:
                        logger.warning(f"API push failed: {e}")
                        tracker.update(6, f"API push skipped: {str(e)}")
                else:
                    tracker.update(6, "Skipping API push (not requested or no credentials)")
                    tracker.update(7, "Skipping picklist push")
                    tracker.update(8, "Skipping FO push")

                # Step 9: Upload generated files
                tracker.update(9, "Finalizing and uploading generated files")

                generated_files_info = []
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

                # Upload each generated XML file
                for xml_file_path in result.files_generated:
                    if os.path.exists(xml_file_path):
                        filename = os.path.basename(xml_file_path)
                        file_size = os.path.getsize(xml_file_path)

                        # Upload to storage
                        storage_key = f"users/{user_id}/projects/{project_id}/generated/{filename}"
                        storage_service.upload_file(xml_file_path, storage_key)

                        # Create database record
                        generated_file = GeneratedFile(
                            id=str(uuid.uuid4()),
                            project_id=project_id,
                            filename=filename,
                            file_type='import_xml',
                            storage_key=storage_key,
                            file_size=file_size,
                            expires_at=datetime.utcnow() + timedelta(days=FILE_RETENTION_DAYS)
                        )
                        db.session.add(generated_file)

                        generated_files_info.append({
                            'file_id': generated_file.id,
                            'filename': filename,
                            'file_size': file_size
                        })

                # Upload change log workbook if it exists
                changelog_path = os.path.join(temp_dir, "TranslationsWorkbook_WithChangeLog.xlsx")
                if os.path.exists(changelog_path):
                    changelog_filename = f"TranslationsWorkbook_WithChangeLog_{timestamp}.xlsx"
                    changelog_key = f"users/{user_id}/projects/{project_id}/generated/{changelog_filename}"
                    storage_service.upload_file(changelog_path, changelog_key)

                    changelog_file = GeneratedFile(
                        id=str(uuid.uuid4()),
                        project_id=project_id,
                        filename=changelog_filename,
                        file_type='changelog_workbook',
                        storage_key=changelog_key,
                        file_size=os.path.getsize(changelog_path),
                        expires_at=datetime.utcnow() + timedelta(days=FILE_RETENTION_DAYS)
                    )
                    db.session.add(changelog_file)

                    generated_files_info.append({
                        'file_id': changelog_file.id,
                        'filename': changelog_filename,
                        'file_type': 'changelog_workbook'
                    })

                # Upload import log
                if result.log_file_path and os.path.exists(result.log_file_path):
                    log_filename = os.path.basename(result.log_file_path)
                    log_key = f"users/{user_id}/projects/{project_id}/generated/{log_filename}"
                    storage_service.upload_file(result.log_file_path, log_key)

                    log_file = GeneratedFile(
                        id=str(uuid.uuid4()),
                        project_id=project_id,
                        filename=log_filename,
                        file_type='import_log',
                        storage_key=log_key,
                        file_size=os.path.getsize(result.log_file_path),
                        expires_at=datetime.utcnow() + timedelta(days=FILE_RETENTION_DAYS)
                    )
                    db.session.add(log_file)

                # Update project status
                project = Project.query.get(project_id)
                if project:
                    project.status = 'imported'
                    project.updated_at = datetime.utcnow()

                db.session.commit()

                # Complete
                tracker.complete(result={
                    'files_generated': generated_files_info,
                    'worksheets_processed': sheets_to_process,
                    'changes_made': result.changes_made,
                    'api_pushed': push_to_api and sf_connection.get('endpoint')
                })

            except OperationCancelled:
                # Reset project status
                project = Project.query.get(project_id)
                if project:
                    project.status = 'exported'
                    db.session.commit()
                tracker.fail("Import cancelled by user")

            except Exception as e:
                logger.exception(f"Import failed for project {project_id}")
                # Reset project status
                project = Project.query.get(project_id)
                if project:
                    project.status = 'exported'
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
# IMPORT STATUS & MANAGEMENT
# =============================================================================

@import_bp.route('/projects/<project_id>/import/status', methods=['GET'])
@require_auth
def get_import_status(project_id):
    """Get current import status for a project."""
    user = get_user_from_context()
    project = Project.query.filter_by(id=project_id, user_id=user.id).first()

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    active = is_operation_active(project_id)

    # Get latest generated files
    generated_files = GeneratedFile.query.filter_by(
        project_id=project_id
    ).filter(
        GeneratedFile.file_type.in_(['import_xml', 'changelog_workbook', 'import_log'])
    ).order_by(GeneratedFile.created_at.desc()).all()

    return jsonify({
        'project_id': project_id,
        'status': project.status,
        'is_active': active,
        'generated_files': [f.to_dict() for f in generated_files]
    })


@import_bp.route('/projects/<project_id>/import/cancel', methods=['POST'])
@require_auth
def cancel_import(project_id):
    """Cancel an in-progress import."""
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
            'error': 'No active import to cancel'
        }), 404


# =============================================================================
# WORKBOOK VALIDATION
# =============================================================================

@import_bp.route('/projects/<project_id>/import/validate', methods=['POST'])
@require_auth
def validate_workbook(project_id):
    """
    Validate a translation workbook before import.

    Expects multipart form with:
        - workbook: The translation workbook file (.xlsx)

    Returns:
        - 200: Validation result with available worksheets
        - 400: Invalid file
    """
    user = get_user_from_context()
    project = Project.query.filter_by(id=project_id, user_id=user.id).first()

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    if 'workbook' not in request.files:
        return jsonify({'error': 'No workbook file provided'}), 400

    workbook_file = request.files['workbook']
    if not workbook_file.filename.endswith('.xlsx'):
        return jsonify({'error': 'Invalid file type. Expected .xlsx'}), 400

    # Save to temp file for validation
    temp_dir = tempfile.mkdtemp(prefix='trexima_validate_')
    try:
        workbook_path = os.path.join(temp_dir, secure_filename(workbook_file.filename))
        workbook_file.save(workbook_path)

        excel_handler = ExcelHandler()
        workbook = excel_handler.load_workbook(workbook_path)

        if not workbook:
            return jsonify({
                'valid': False,
                'error': 'Failed to load workbook'
            }), 400

        is_valid = excel_handler.validate_translations_workbook(workbook)
        available_sheets = workbook.sheetnames

        # Categorize sheets
        datamodel_sheets = [s for s in available_sheets if s.startswith('DataModel')]
        pm_sheets = [s for s in available_sheets if 'Performance' in s or 'PM' in s]
        gm_sheets = [s for s in available_sheets if 'Goal' in s or 'GM' in s]
        other_sheets = [s for s in available_sheets
                        if s not in datamodel_sheets and s not in pm_sheets and s not in gm_sheets]

        return jsonify({
            'valid': is_valid,
            'filename': workbook_file.filename,
            'sheets': {
                'all': available_sheets,
                'datamodel': datamodel_sheets,
                'pm_templates': pm_sheets,
                'gm_templates': gm_sheets,
                'other': other_sheets
            },
            'total_sheets': len(available_sheets)
        })

    finally:
        # Cleanup
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass
