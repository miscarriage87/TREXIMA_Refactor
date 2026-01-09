"""
TREXIMA v4.0 - Projects Blueprint

Handles project CRUD, file uploads, SF connection, and workflow operations.
"""

from flask import Blueprint, jsonify, request, g, current_app
import logging
from datetime import datetime
from werkzeug.utils import secure_filename

from trexima.web.auth import require_auth, get_current_user
from trexima.web.models import (
    db, User, Project, ProjectFile, GeneratedFile,
    get_or_create_user, DEFAULT_PROJECT_CONFIG
)
from trexima.web.storage import storage_service
from trexima.web.websocket import (
    emit_progress, emit_operation_complete, emit_project_saved,
    ProgressTracker, is_operation_active
)

logger = logging.getLogger(__name__)

projects_bp = Blueprint('projects', __name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_user_from_context():
    """Get or create database user from auth context."""
    user_context = get_current_user()
    return get_or_create_user(
        xsuaa_id=user_context.user_id,
        email=user_context.email,
        display_name=user_context.display_name,
        is_admin=user_context.is_admin
    )


def get_project_or_404(project_id: str, user: User):
    """Get project by ID, checking ownership."""
    project = Project.query.filter_by(id=project_id).first()

    if not project:
        return None, ({'error': 'Project not found'}, 404)

    # Check ownership (unless admin)
    if project.user_id != user.id and not user.is_admin:
        return None, ({'error': 'Access denied'}, 403)

    return project, None


# =============================================================================
# STATIC DATA ENDPOINTS
# =============================================================================

@projects_bp.route('/sf-endpoints', methods=['GET'])
@require_auth
def get_sf_endpoints():
    """
    Get available SuccessFactors API endpoints.
    Returns categorized endpoints (production, preview, salesdemo, custom).
    """
    from trexima.web.constants import SF_ENDPOINTS
    return jsonify({'endpoints': SF_ENDPOINTS})


# =============================================================================
# PROJECT CRUD
# =============================================================================

@projects_bp.route('', methods=['GET'])
@require_auth
def list_projects():
    """
    List all projects for the current user.

    Query params:
        - include_config: Include full config (default: false)
        - status: Filter by status
    """
    user = get_user_from_context()

    include_config = request.args.get('include_config', 'false').lower() == 'true'
    status_filter = request.args.get('status')

    query = user.projects

    if status_filter:
        query = query.filter_by(status=status_filter)

    projects = query.order_by(Project.updated_at.desc()).all()

    return jsonify({
        'projects': [p.to_dict(include_config=include_config) for p in projects],
        'count': len(projects),
        'max_projects': User.MAX_PROJECTS,
        'can_create': user.can_create_project()
    })


@projects_bp.route('', methods=['POST'])
@require_auth
def create_project():
    """
    Create a new project.

    Request body:
        {
            "name": "Project Name",
            "description": "Optional description"
        }
    """
    user = get_user_from_context()

    # Check project limit
    if not user.can_create_project():
        return jsonify({
            'error': 'Project limit reached',
            'message': f'You can have a maximum of {User.MAX_PROJECTS} projects. Please delete an existing project first.',
            'current_count': user.projects.count(),
            'max_projects': User.MAX_PROJECTS
        }), 409

    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({'error': 'Project name is required'}), 400

    # Create project with default config
    project = Project(
        user_id=user.id,
        name=data['name'].strip(),
        description=data.get('description', '').strip(),
        status='draft',
        config=DEFAULT_PROJECT_CONFIG.copy()
    )

    db.session.add(project)
    db.session.commit()

    logger.info(f"Project created: {project.id} by {user.email}")

    return jsonify({
        'success': True,
        'project': project.to_dict()
    }), 201


@projects_bp.route('/<project_id>', methods=['GET'])
@require_auth
def get_project(project_id):
    """Get project details by ID."""
    user = get_user_from_context()
    project, error = get_project_or_404(project_id, user)

    if error:
        return jsonify(error[0]), error[1]

    # Update last accessed
    project.touch()
    db.session.commit()

    return jsonify({
        'project': project.to_dict(include_files=True, include_config=True)
    })


@projects_bp.route('/<project_id>', methods=['PUT'])
@require_auth
def update_project(project_id):
    """
    Update project metadata.

    Request body:
        {
            "name": "New Name",
            "description": "New description"
        }
    """
    user = get_user_from_context()
    project, error = get_project_or_404(project_id, user)

    if error:
        return jsonify(error[0]), error[1]

    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if 'name' in data:
        project.name = data['name'].strip()
    if 'description' in data:
        project.description = data['description'].strip()

    db.session.commit()

    return jsonify({
        'success': True,
        'project': project.to_dict()
    })


@projects_bp.route('/<project_id>', methods=['DELETE'])
@require_auth
def delete_project(project_id):
    """Delete a project and all associated files."""
    user = get_user_from_context()
    project, error = get_project_or_404(project_id, user)

    if error:
        return jsonify(error[0]), error[1]

    # Check for active operations
    if is_operation_active(project_id):
        return jsonify({
            'error': 'Cannot delete project with active operation',
            'message': 'Please wait for the current operation to complete'
        }), 409

    # Delete files from storage
    try:
        storage_service.delete_project_files(user.id, project_id)
    except Exception as e:
        logger.error(f"Failed to delete storage files: {e}")
        # Continue with database deletion anyway

    # Delete from database (cascades to files)
    project_name = project.name
    db.session.delete(project)
    db.session.commit()

    logger.info(f"Project deleted: {project_id} ({project_name}) by {user.email}")

    return jsonify({
        'success': True,
        'message': f'Project "{project_name}" deleted'
    })


# =============================================================================
# PROJECT CONFIGURATION
# =============================================================================

@projects_bp.route('/<project_id>/config', methods=['GET'])
@require_auth
def get_project_config(project_id):
    """Get project configuration."""
    user = get_user_from_context()
    project, error = get_project_or_404(project_id, user)

    if error:
        return jsonify(error[0]), error[1]

    return jsonify({
        'config': project.config or {}
    })


@projects_bp.route('/<project_id>/config', methods=['PUT'])
@require_auth
def update_project_config(project_id):
    """
    Update project configuration (partial update).

    Request body: Config object (will be merged with existing)
    """
    user = get_user_from_context()
    project, error = get_project_or_404(project_id, user)

    if error:
        return jsonify(error[0]), error[1]

    data = request.get_json()

    if not data:
        return jsonify({'error': 'No configuration provided'}), 400

    # Merge with existing config
    if project.config is None:
        project.config = DEFAULT_PROJECT_CONFIG.copy()

    # Deep merge for nested objects
    def deep_merge(base, updates):
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                deep_merge(base[key], value)
            else:
                base[key] = value

    deep_merge(project.config, data)
    project.config['last_saved_at'] = datetime.utcnow().isoformat()

    # Force SQLAlchemy to detect the change
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(project, 'config')

    db.session.commit()

    # Emit save notification
    emit_project_saved(project_id)

    return jsonify({
        'success': True,
        'config': project.config
    })


@projects_bp.route('/<project_id>/save', methods=['POST'])
@require_auth
def save_project_state(project_id):
    """
    Save current project state.

    This is called by auto-save functionality.
    """
    user = get_user_from_context()
    project, error = get_project_or_404(project_id, user)

    if error:
        return jsonify(error[0]), error[1]

    data = request.get_json() or {}

    # Update config if provided
    if 'config' in data:
        if project.config is None:
            project.config = {}
        project.config.update(data['config'])

    project.config['last_saved_at'] = datetime.utcnow().isoformat()

    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(project, 'config')

    db.session.commit()

    # Emit save notification
    emit_project_saved(project_id)

    return jsonify({
        'success': True,
        'saved_at': project.config['last_saved_at']
    })


# =============================================================================
# FILE UPLOAD
# =============================================================================

@projects_bp.route('/<project_id>/files', methods=['POST'])
@require_auth
def upload_files(project_id):
    """
    Upload files to project.

    Accepts multipart/form-data with files.
    Automatically detects file type (sdm, cdm, ec_sdm, ec_cdm, picklist).
    """
    user = get_user_from_context()
    project, error = get_project_or_404(project_id, user)

    if error:
        return jsonify(error[0]), error[1]

    if 'files' not in request.files and 'file' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    # Get files from request (support both single and multiple)
    files = request.files.getlist('files') or [request.files.get('file')]
    files = [f for f in files if f and f.filename]

    if not files:
        return jsonify({'error': 'No valid files provided'}), 400

    uploaded = []
    errors = []

    for file in files:
        try:
            filename = secure_filename(file.filename)

            # Read file content for type detection
            content = file.read()
            file.seek(0)  # Reset for upload

            # Detect file type
            file_type = ProjectFile.detect_file_type(filename, content)

            if not file_type:
                errors.append({
                    'filename': filename,
                    'error': 'Could not determine file type'
                })
                continue

            # Check if file of this type already exists
            existing = project.get_file_by_type(file_type)
            if existing:
                # Delete old file from storage
                try:
                    storage_service.delete_file(existing.storage_key)
                except Exception as e:
                    logger.warning(f"Failed to delete old file: {e}")
                db.session.delete(existing)

            # Generate storage key
            storage_key = storage_service.generate_upload_key(
                user.id, project_id, file_type, filename
            )

            # Determine content type
            content_type = 'application/xml' if filename.endswith('.xml') else 'text/csv'

            # Upload to storage
            from io import BytesIO
            result = storage_service.upload_file(
                BytesIO(content),
                storage_key,
                content_type
            )

            # Create database record
            project_file = ProjectFile(
                project_id=project_id,
                file_type=file_type,
                original_name=filename,
                storage_key=storage_key,
                file_size=len(content),
                content_type=content_type
            )

            db.session.add(project_file)

            uploaded.append({
                'id': project_file.id,
                'file_type': file_type,
                'original_name': filename,
                'file_size': len(content)
            })

            logger.info(f"File uploaded: {file_type} for project {project_id}")

        except Exception as e:
            logger.error(f"File upload error: {e}")
            errors.append({
                'filename': file.filename,
                'error': str(e)
            })

    db.session.commit()

    # Update project status if files uploaded
    if uploaded and project.status == 'draft':
        if project.has_minimum_files():
            project.status = 'draft'  # Keep as draft but mark as having files

    return jsonify({
        'uploaded': uploaded,
        'errors': errors if errors else None,
        'project_files': project.get_files_summary(),
        'has_minimum': project.has_minimum_files(),
        'has_all': project.has_all_files()
    }), 201 if uploaded else 400


@projects_bp.route('/<project_id>/files/<file_id>', methods=['DELETE'])
@require_auth
def delete_file(project_id, file_id):
    """Delete an uploaded file."""
    user = get_user_from_context()
    project, error = get_project_or_404(project_id, user)

    if error:
        return jsonify(error[0]), error[1]

    file = ProjectFile.query.filter_by(id=file_id, project_id=project_id).first()

    if not file:
        return jsonify({'error': 'File not found'}), 404

    # Delete from storage
    try:
        storage_service.delete_file(file.storage_key)
    except Exception as e:
        logger.warning(f"Failed to delete from storage: {e}")

    file_type = file.file_type
    db.session.delete(file)
    db.session.commit()

    return jsonify({
        'success': True,
        'deleted_type': file_type,
        'project_files': project.get_files_summary()
    })


# =============================================================================
# SF CONNECTION
# =============================================================================

@projects_bp.route('/<project_id>/connect', methods=['POST'])
@require_auth
def test_connection(project_id):
    """
    Test SuccessFactors API connection.

    Request body:
        {
            "endpoint_url": "https://api4.successfactors.com/odata/v2",
            "company_id": "COMPANY_ID",
            "username": "USERNAME",
            "password": "PASSWORD"
        }
    """
    user = get_user_from_context()
    project, error = get_project_or_404(project_id, user)

    if error:
        return jsonify(error[0]), error[1]

    data = request.get_json()

    required_fields = ['endpoint_url', 'company_id', 'username', 'password']
    missing = [f for f in required_fields if not data.get(f)]

    if missing:
        return jsonify({
            'error': 'Missing required fields',
            'missing': missing
        }), 400

    # Test connection
    try:
        from trexima.core.odata_client import ODataClient

        client = ODataClient()
        client.connect(
            service_url=data['endpoint_url'],
            company_id=data['company_id'],
            username=data['username'],
            password=data['password']
        )

        # Test connection by getting locales
        locales = client.get_active_locales()

        # Update project config with connection details
        # NOTE: We store credentials here so that dynamic SF data fetching can work.
        # In a production system, consider using a secure vault or session-based storage.
        project.config['sf_connection'] = {
            'endpoint_url': data['endpoint_url'],
            'endpoint': data['endpoint_url'],  # Alias for compatibility
            'endpoint_name': data.get('endpoint_name'),
            'company_id': data['company_id'],
            'username': data['username'],
            'password': data['password'],  # Required for dynamic SF data fetching
            'connected': True,
            'last_connected_at': datetime.utcnow().isoformat()
        }

        # Store locales in both formats for frontend compatibility
        project.config['locales'] = locales  # Array of strings for frontend
        project.config['languages'] = {
            'available': [{'code': loc, 'name': loc} for loc in locales],
            'selected': ['en_US'] + [loc for loc in locales[:4] if loc != 'en_US']  # Default selection
        }

        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(project, 'config')
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Connection established successfully',
            'instance_info': {
                'company_id': data['company_id'],
                'endpoint': data['endpoint_url']
            },
            'available_locales': project.config['languages']['available']
        })

    except Exception as e:
        logger.error(f"Connection test failed: {e}")

        # Update config to reflect disconnected state
        project.config['sf_connection']['connected'] = False
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(project, 'config')
        db.session.commit()

        return jsonify({
            'success': False,
            'error': 'Connection failed',
            'details': str(e),
            'suggestion': 'Please verify your credentials and endpoint URL'
        }), 400


@projects_bp.route('/<project_id>/locales', methods=['GET'])
@require_auth
def get_locales(project_id):
    """Get available locales for project."""
    user = get_user_from_context()
    project, error = get_project_or_404(project_id, user)

    if error:
        return jsonify(error[0]), error[1]

    available = project.config.get('languages', {}).get('available', [])
    selected = project.config.get('languages', {}).get('selected', ['en_US'])

    return jsonify({
        'available': available,
        'selected': selected
    })


@projects_bp.route('/<project_id>/locales', methods=['PUT'])
@require_auth
def update_locales(project_id):
    """
    Update selected locales.

    Request body:
        {
            "selected": ["en_US", "de_DE", "fr_FR"]
        }
    """
    user = get_user_from_context()
    project, error = get_project_or_404(project_id, user)

    if error:
        return jsonify(error[0]), error[1]

    data = request.get_json()

    if 'selected' not in data:
        return jsonify({'error': 'Selected locales required'}), 400

    selected = data['selected']

    # Ensure en_US is always included
    if 'en_US' not in selected:
        selected.insert(0, 'en_US')

    project.config['languages']['selected'] = selected

    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(project, 'config')
    db.session.commit()

    return jsonify({
        'success': True,
        'selected': selected
    })


# =============================================================================
# GENERATED FILES / DOWNLOADS
# =============================================================================

@projects_bp.route('/<project_id>/downloads', methods=['GET'])
@require_auth
def list_downloads(project_id):
    """List available downloads for project."""
    user = get_user_from_context()
    project, error = get_project_or_404(project_id, user)

    if error:
        return jsonify(error[0]), error[1]

    files = project.generated_files.filter(
        GeneratedFile.expires_at > datetime.utcnow()
    ).order_by(GeneratedFile.created_at.desc()).all()

    return jsonify({
        'files': [f.to_dict() for f in files],
        'count': len(files)
    })


@projects_bp.route('/<project_id>/download/<file_id>', methods=['GET'])
@require_auth
def download_file(project_id, file_id):
    """Get download URL for a generated file."""
    user = get_user_from_context()
    project, error = get_project_or_404(project_id, user)

    if error:
        return jsonify(error[0]), error[1]

    gen_file = GeneratedFile.query.filter_by(
        id=file_id,
        project_id=project_id
    ).first()

    if not gen_file:
        return jsonify({'error': 'File not found'}), 404

    if gen_file.is_expired:
        return jsonify({'error': 'File has expired'}), 410

    # Generate pre-signed URL
    try:
        url = storage_service.get_download_url(
            gen_file.storage_key,
            expires_in=3600,
            filename=gen_file.filename
        )

        # Update download count
        gen_file.increment_download_count()
        db.session.commit()

        return jsonify({
            'download_url': url,
            'filename': gen_file.filename,
            'expires_in': 3600
        })

    except Exception as e:
        logger.error(f"Failed to generate download URL: {e}")
        return jsonify({'error': 'Failed to generate download URL'}), 500


# =============================================================================
# OPERATION STATUS
# =============================================================================

@projects_bp.route('/<project_id>/status', methods=['GET'])
@require_auth
def get_operation_status(project_id):
    """Get current operation status for project."""
    user = get_user_from_context()
    project, error = get_project_or_404(project_id, user)

    if error:
        return jsonify(error[0]), error[1]

    from trexima.web.websocket import get_active_operations

    operations = get_active_operations()
    current_op = operations.get(project_id)

    return jsonify({
        'has_active_operation': current_op is not None,
        'operation': current_op
    })


# =============================================================================
# DYNAMIC SF DATA FETCHING
# =============================================================================

@projects_bp.route('/<project_id>/sf-objects', methods=['GET'])
@require_auth
def get_sf_objects(project_id):
    """
    Fetch available objects from the connected SF instance.

    Returns dynamic data including:
    - Available entity sets (MDF objects)
    - Picklist counts (MDF and legacy)
    - Foundation objects availability

    Requires an active SF connection with stored credentials.
    """
    user = get_user_from_context()
    project, error = get_project_or_404(project_id, user)

    if error:
        return jsonify(error[0]), error[1]

    sf_connection = project.config.get('sf_connection', {})

    if not sf_connection.get('connected'):
        return jsonify({
            'error': 'No active SF connection',
            'message': 'Please connect to SuccessFactors first'
        }), 400

    # Check if we have credentials
    endpoint_url = sf_connection.get('endpoint_url') or sf_connection.get('endpoint')
    company_id = sf_connection.get('company_id')
    username = sf_connection.get('username')
    password = sf_connection.get('password')

    if not all([endpoint_url, company_id, username, password]):
        return jsonify({
            'error': 'Missing credentials',
            'message': 'SF connection credentials are incomplete. Please reconnect.'
        }), 400

    try:
        from trexima.core.odata_client import ODataClient

        client = ODataClient()
        client.connect(
            service_url=endpoint_url,
            company_id=company_id,
            username=username,
            password=password
        )

        # Fetch all entity names
        all_entities = client.get_all_entity_names()

        # Categorize entities
        mdf_objects = []
        foundation_objects = []
        ec_objects = []

        # Known FO prefixes
        fo_prefixes = ['FO', 'FOCorp', 'FOBusiness', 'FOCompany', 'FODepartment',
                       'FODivision', 'FOJob', 'FOLocation', 'FOPay', 'FOEvent',
                       'FOGeo', 'FOFrequency', 'FOCostCenter', 'FOLegal']

        # Known EC prefixes
        ec_prefixes = ['Per', 'Emp', 'Position', 'Competency', 'DevGoal',
                       'Goal', 'Achievement', 'Activity', 'Background',
                       'TimeAccount', 'TimeManagement', 'Absence']

        for entity in all_entities:
            # Skip metadata and internal entities
            if entity.startswith('cust_') or entity.endswith('Nav'):
                mdf_objects.append(entity)
            elif any(entity.startswith(prefix) for prefix in fo_prefixes):
                foundation_objects.append(entity)
            elif any(entity.startswith(prefix) for prefix in ec_prefixes):
                ec_objects.append(entity)

        # Get picklist counts
        mdf_picklist_count = client.get_picklist_count('mdf')
        legacy_picklist_count = client.get_picklist_count('legacy')
        migrated_count = client.get_migrated_legacy_picklist_count()

        # Get active locales
        active_locales = client.get_active_locales()

        client.disconnect()

        return jsonify({
            'success': True,
            'data': {
                'entities': {
                    'total': len(all_entities),
                    'mdf_objects': sorted(mdf_objects),
                    'foundation_objects': sorted(foundation_objects),
                    'ec_objects': sorted(ec_objects)
                },
                'picklists': {
                    'mdf_count': mdf_picklist_count,
                    'legacy_count': legacy_picklist_count,
                    'migrated_legacy_count': migrated_count
                },
                'locales': active_locales
            }
        })

    except Exception as e:
        logger.error(f"Failed to fetch SF objects: {e}")
        return jsonify({
            'error': 'Failed to fetch SF data',
            'details': str(e)
        }), 500


@projects_bp.route('/<project_id>/sf-picklists', methods=['GET'])
@require_auth
def get_sf_picklists(project_id):
    """
    Fetch picklist details from the connected SF instance.

    Query params:
        - type: 'mdf' or 'legacy' (default: 'mdf')
        - limit: Number to fetch (default: 100)
        - offset: Pagination offset (default: 0)
    """
    user = get_user_from_context()
    project, error = get_project_or_404(project_id, user)

    if error:
        return jsonify(error[0]), error[1]

    sf_connection = project.config.get('sf_connection', {})

    if not sf_connection.get('connected'):
        return jsonify({'error': 'No active SF connection'}), 400

    endpoint_url = sf_connection.get('endpoint_url') or sf_connection.get('endpoint')
    company_id = sf_connection.get('company_id')
    username = sf_connection.get('username')
    password = sf_connection.get('password')

    if not all([endpoint_url, company_id, username, password]):
        return jsonify({'error': 'Missing credentials'}), 400

    picklist_type = request.args.get('type', 'mdf')
    limit = min(int(request.args.get('limit', 100)), 500)
    offset = int(request.args.get('offset', 0))

    try:
        from trexima.core.odata_client import ODataClient

        client = ODataClient()
        client.connect(
            service_url=endpoint_url,
            company_id=company_id,
            username=username,
            password=password
        )

        if picklist_type == 'mdf':
            picklists = client.get_mdf_picklists(top=limit, skip=offset)
            total = client.get_picklist_count('mdf')
        else:
            picklists = client.get_legacy_picklists(top=limit, skip=offset)
            total = client.get_picklist_count('legacy')

        # Convert to serializable format
        picklist_data = []
        for pl in picklists:
            try:
                pl_dict = {
                    'id': getattr(pl, 'picklistId', None) or getattr(pl, 'picklistId', None),
                    'name': getattr(pl, 'name', None) or getattr(pl, 'picklistId', 'Unknown'),
                }
                if picklist_type == 'mdf':
                    pl_dict['value_count'] = len(getattr(pl, 'values', []) or [])
                    pl_dict['status'] = getattr(pl, 'status', None)
                else:
                    options = getattr(pl, 'picklistOptions', []) or []
                    pl_dict['option_count'] = len(options)

                picklist_data.append(pl_dict)
            except Exception:
                continue

        client.disconnect()

        return jsonify({
            'success': True,
            'type': picklist_type,
            'total': total,
            'limit': limit,
            'offset': offset,
            'picklists': picklist_data
        })

    except Exception as e:
        logger.error(f"Failed to fetch picklists: {e}")
        return jsonify({'error': 'Failed to fetch picklists', 'details': str(e)}), 500
