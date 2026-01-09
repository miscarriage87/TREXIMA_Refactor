"""
TREXIMA v4.0 - Admin Blueprint

Administrator endpoints for user management, system oversight, and statistics.
"""

from flask import Blueprint, jsonify, request
import logging
from datetime import datetime, timedelta
from sqlalchemy import func

from trexima.web.auth import require_admin, get_current_user
from trexima.web.models import db, User, Project, ProjectFile, GeneratedFile
from trexima.web.storage import storage_service
from trexima.web.websocket import get_active_operations

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)


# =============================================================================
# USER MANAGEMENT
# =============================================================================

@admin_bp.route('/users', methods=['GET'])
@require_admin
def list_users():
    """
    List all users with optional filtering.

    Query params:
        - search: Search by email or name
        - sort: Sort field (created_at, last_login, email)
        - order: asc or desc
        - limit: Max results
        - offset: Pagination offset
    """
    search = request.args.get('search')
    sort_field = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    query = User.query

    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                User.email.ilike(search_term),
                User.display_name.ilike(search_term)
            )
        )

    # Sorting
    sort_column = getattr(User, sort_field, User.created_at)
    if order == 'desc':
        sort_column = sort_column.desc()
    query = query.order_by(sort_column)

    # Get total count before pagination
    total = query.count()

    # Apply pagination
    users = query.offset(offset).limit(limit).all()

    return jsonify({
        'users': [u.to_dict(include_projects=False) for u in users],
        'total': total,
        'limit': limit,
        'offset': offset
    })


@admin_bp.route('/users/<user_id>', methods=['GET'])
@require_admin
def get_user(user_id):
    """Get user details with their projects."""
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'user': user.to_dict(include_projects=True)
    })


@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    """
    Delete a user and all their data.

    WARNING: This permanently deletes all user projects and files.
    """
    admin = get_current_user()

    # Prevent self-deletion
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.xsuaa_id == admin.user_id:
        return jsonify({'error': 'Cannot delete your own account'}), 400

    # Delete all user files from storage
    try:
        storage_service.delete_user_files(user_id)
    except Exception as e:
        logger.error(f"Failed to delete user files from storage: {e}")

    # Delete user (cascades to projects)
    email = user.email
    db.session.delete(user)
    db.session.commit()

    logger.info(f"Admin {admin.email} deleted user {email}")

    return jsonify({
        'success': True,
        'message': f'User {email} deleted'
    })


@admin_bp.route('/users/<user_id>/admin', methods=['PUT'])
@require_admin
def toggle_user_admin(user_id):
    """
    Toggle admin status for a user.

    Request body:
        {
            "is_admin": true/false
        }
    """
    admin = get_current_user()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Prevent removing own admin
    if user.xsuaa_id == admin.user_id:
        return jsonify({'error': 'Cannot modify your own admin status'}), 400

    data = request.get_json()

    if 'is_admin' not in data:
        return jsonify({'error': 'is_admin field required'}), 400

    user.is_admin = bool(data['is_admin'])
    db.session.commit()

    action = 'granted admin' if user.is_admin else 'revoked admin from'
    logger.info(f"Admin {admin.email} {action} {user.email}")

    return jsonify({
        'success': True,
        'user': user.to_dict()
    })


# =============================================================================
# PROJECT MANAGEMENT
# =============================================================================

@admin_bp.route('/projects', methods=['GET'])
@require_admin
def list_all_projects():
    """
    List all projects across all users.

    Query params:
        - user_id: Filter by user
        - status: Filter by status
        - search: Search by name
        - sort: Sort field
        - order: asc or desc
        - limit: Max results
        - offset: Pagination offset
    """
    user_id = request.args.get('user_id')
    status = request.args.get('status')
    search = request.args.get('search')
    sort_field = request.args.get('sort', 'updated_at')
    order = request.args.get('order', 'desc')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    query = Project.query

    # Filters
    if user_id:
        query = query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(Project.name.ilike(f"%{search}%"))

    # Sorting
    sort_column = getattr(Project, sort_field, Project.updated_at)
    if order == 'desc':
        sort_column = sort_column.desc()
    query = query.order_by(sort_column)

    total = query.count()
    projects = query.offset(offset).limit(limit).all()

    # Include owner info
    result = []
    for p in projects:
        data = p.to_dict(include_config=False)
        data['owner'] = {
            'id': p.owner.id,
            'email': p.owner.email,
            'display_name': p.owner.display_name
        }
        result.append(data)

    return jsonify({
        'projects': result,
        'total': total,
        'limit': limit,
        'offset': offset
    })


@admin_bp.route('/projects/<project_id>', methods=['DELETE'])
@require_admin
def admin_delete_project(project_id):
    """Delete any project (admin override)."""
    admin = get_current_user()
    project = Project.query.get(project_id)

    if not project:
        return jsonify({'error': 'Project not found'}), 404

    # Check for active operations
    active_ops = get_active_operations()
    if project_id in active_ops:
        return jsonify({
            'error': 'Cannot delete project with active operation'
        }), 409

    # Delete files from storage
    try:
        storage_service.delete_project_files(project.user_id, project_id)
    except Exception as e:
        logger.error(f"Failed to delete project files: {e}")

    project_name = project.name
    owner_email = project.owner.email
    db.session.delete(project)
    db.session.commit()

    logger.info(f"Admin {admin.email} deleted project {project_name} (owner: {owner_email})")

    return jsonify({
        'success': True,
        'message': f'Project "{project_name}" deleted'
    })


# =============================================================================
# SYSTEM STATISTICS
# =============================================================================

@admin_bp.route('/stats', methods=['GET'])
@require_admin
def get_system_stats():
    """Get system-wide statistics."""
    # User stats
    total_users = User.query.count()
    admin_users = User.query.filter_by(is_admin=True).count()
    active_users_7d = User.query.filter(
        User.last_login > datetime.utcnow() - timedelta(days=7)
    ).count()
    active_users_30d = User.query.filter(
        User.last_login > datetime.utcnow() - timedelta(days=30)
    ).count()

    # Project stats
    total_projects = Project.query.count()
    projects_by_status = db.session.query(
        Project.status,
        func.count(Project.id)
    ).group_by(Project.status).all()

    # File stats
    total_uploaded_files = ProjectFile.query.count()
    total_generated_files = GeneratedFile.query.count()
    expired_files = GeneratedFile.query.filter(
        GeneratedFile.expires_at < datetime.utcnow()
    ).count()

    # Storage stats
    try:
        storage_stats = storage_service.get_storage_usage()
    except Exception:
        storage_stats = {'total_files': 0, 'total_size': 0}

    # Active operations
    active_ops = get_active_operations()

    return jsonify({
        'users': {
            'total': total_users,
            'admins': admin_users,
            'active_7d': active_users_7d,
            'active_30d': active_users_30d
        },
        'projects': {
            'total': total_projects,
            'by_status': {status: count for status, count in projects_by_status}
        },
        'files': {
            'uploaded': total_uploaded_files,
            'generated': total_generated_files,
            'expired': expired_files
        },
        'storage': storage_stats,
        'operations': {
            'active': len(active_ops),
            'details': active_ops
        },
        'generated_at': datetime.utcnow().isoformat()
    })


@admin_bp.route('/stats/users', methods=['GET'])
@require_admin
def get_user_stats():
    """Get detailed user statistics."""
    # Users created over time (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    users_by_day = db.session.query(
        func.date(User.created_at),
        func.count(User.id)
    ).filter(
        User.created_at > thirty_days_ago
    ).group_by(
        func.date(User.created_at)
    ).all()

    # Top users by project count
    top_users = db.session.query(
        User.id,
        User.email,
        User.display_name,
        func.count(Project.id).label('project_count')
    ).outerjoin(Project).group_by(
        User.id
    ).order_by(
        func.count(Project.id).desc()
    ).limit(10).all()

    return jsonify({
        'users_by_day': [
            {'date': str(date), 'count': count}
            for date, count in users_by_day
        ],
        'top_users': [
            {
                'id': id,
                'email': email,
                'display_name': name,
                'project_count': count
            }
            for id, email, name, count in top_users
        ]
    })


# =============================================================================
# CLEANUP OPERATIONS
# =============================================================================

@admin_bp.route('/cleanup/expired', methods=['POST'])
@require_admin
def cleanup_expired_files():
    """
    Clean up expired generated files.

    This removes expired files from both database and storage.
    """
    admin = get_current_user()

    # Find expired files
    expired = GeneratedFile.query.filter(
        GeneratedFile.expires_at < datetime.utcnow()
    ).all()

    deleted_count = 0
    errors = []

    for file in expired:
        try:
            # Delete from storage
            storage_service.delete_file(file.storage_key)
            # Delete from database
            db.session.delete(file)
            deleted_count += 1
        except Exception as e:
            errors.append({
                'file_id': file.id,
                'error': str(e)
            })

    db.session.commit()

    logger.info(f"Admin {admin.email} cleaned up {deleted_count} expired files")

    return jsonify({
        'success': True,
        'deleted': deleted_count,
        'errors': errors if errors else None
    })


@admin_bp.route('/cleanup/orphaned', methods=['POST'])
@require_admin
def cleanup_orphaned_storage():
    """
    Clean up orphaned files in storage.

    Finds files in storage that don't have database records.
    Use with caution - performs a full storage scan.
    """
    admin = get_current_user()

    # This is an expensive operation
    # Get all storage keys
    try:
        storage_files = storage_service.list_files('users/', max_keys=10000)
    except Exception as e:
        return jsonify({'error': f'Failed to list storage: {e}'}), 500

    # Get all database storage keys
    db_keys = set()

    for pf in ProjectFile.query.all():
        db_keys.add(pf.storage_key)
    for gf in GeneratedFile.query.all():
        db_keys.add(gf.storage_key)

    # Find orphans
    orphaned = [f for f in storage_files if f['key'] not in db_keys]

    # Optional: delete orphans (only if explicitly requested)
    if request.args.get('delete') == 'true':
        deleted = 0
        for f in orphaned:
            try:
                storage_service.delete_file(f['key'])
                deleted += 1
            except Exception:
                pass

        logger.info(f"Admin {admin.email} deleted {deleted} orphaned storage files")

        return jsonify({
            'orphaned_count': len(orphaned),
            'deleted': deleted
        })

    return jsonify({
        'orphaned_count': len(orphaned),
        'orphaned_files': orphaned[:100],  # Limit response size
        'message': 'Add ?delete=true to delete orphaned files'
    })


# =============================================================================
# SYSTEM HEALTH
# =============================================================================

@admin_bp.route('/health/detailed', methods=['GET'])
@require_admin
def detailed_health():
    """Get detailed system health information."""
    health = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'checks': {}
    }

    # Database check
    try:
        db.session.execute(db.text('SELECT 1'))
        user_count = User.query.count()
        health['checks']['database'] = {
            'status': 'ok',
            'user_count': user_count
        }
    except Exception as e:
        health['checks']['database'] = {
            'status': 'error',
            'error': str(e)
        }
        health['status'] = 'degraded'

    # Storage check
    try:
        if storage_service.is_initialized:
            stats = storage_service.get_storage_usage()
            health['checks']['storage'] = {
                'status': 'ok',
                'files': stats['total_files'],
                'size_bytes': stats['total_size']
            }
        else:
            health['checks']['storage'] = {
                'status': 'not_initialized'
            }
    except Exception as e:
        health['checks']['storage'] = {
            'status': 'error',
            'error': str(e)
        }

    # Active operations
    active_ops = get_active_operations()
    health['checks']['operations'] = {
        'active_count': len(active_ops),
        'projects': list(active_ops.keys())
    }

    return jsonify(health)
