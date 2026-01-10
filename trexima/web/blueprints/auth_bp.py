"""
TREXIMA v2.0 - Authentication Blueprint

Handles user authentication, session management, and OAuth configuration.
"""

from flask import Blueprint, jsonify, request, g, current_app, redirect
import logging
from datetime import datetime

from trexima.web.auth import (
    require_auth,
    optional_auth,
    get_current_user,
    get_oauth_config,
    create_dev_token,
    validate_token
)
from trexima.web.models import db, User, get_or_create_user

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


# =============================================================================
# USER ENDPOINTS
# =============================================================================

@auth_bp.route('/user', methods=['GET'])
@require_auth
def get_user():
    """
    Get current authenticated user information.

    Returns:
        User info including database record
    """
    user_context = get_current_user()

    # Get or create database user record
    db_user = get_or_create_user(
        xsuaa_id=user_context.user_id,
        email=user_context.email,
        display_name=user_context.display_name,
        is_admin=user_context.is_admin
    )

    return jsonify({
        'authenticated': True,
        'user': db_user.to_dict(include_projects=False),
        'context': user_context.to_dict(),
        'can_create_project': db_user.can_create_project(),
        'max_projects': User.MAX_PROJECTS,
        'project_count': db_user.projects.count()
    })


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """
    Logout user (client-side token invalidation).

    Note: With XSUAA, actual token invalidation happens on the IdP side.
    This endpoint is mainly for logging and cleanup.
    """
    user_context = get_current_user()
    logger.info(f"User logged out: {user_context.email}")

    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })


# =============================================================================
# OAUTH CONFIGURATION
# =============================================================================

@auth_bp.route('/config', methods=['GET'])
def get_auth_config():
    """
    Get authentication configuration for frontend.

    Returns configuration needed for login flow.
    """
    from trexima.web.auth import auth_config
    from urllib.parse import urlencode

    oauth_config = get_oauth_config()

    # Return format expected by frontend (wrapped in 'config' key)
    if oauth_config.get('configured'):
        # Build complete OAuth authorization URL with required parameters
        # Get the app URL from request or environment
        app_url = request.url_root.rstrip('/')

        # OAuth2 authorization parameters
        auth_params = {
            'client_id': auth_config.client_id,
            'redirect_uri': f"{app_url}/api/auth/callback",
            'response_type': 'code',
            'scope': 'openid'
        }

        login_url = f"{oauth_config['authorization_endpoint']}?{urlencode(auth_params)}"
        logout_url = f"{auth_config.url}/logout?redirect={app_url}"

        # XSUAA is properly configured
        return jsonify({
            'config': {
                'is_initialized': True,
                'login_url': login_url,
                'logout_url': logout_url
            }
        })

    # Development mode - XSUAA not configured
    return jsonify({
        'config': {
            'is_initialized': False
        }
    })


# =============================================================================
# OAUTH CALLBACK
# =============================================================================

@auth_bp.route('/callback', methods=['GET'])
def oauth_callback():
    """
    OAuth2 callback endpoint.

    Receives authorization code from XSUAA, exchanges it for tokens,
    and redirects user back to the application.
    """
    import requests as http_requests
    from trexima.web.auth import auth_config

    code = request.args.get('code')
    error = request.args.get('error')
    error_description = request.args.get('error_description')

    # Handle OAuth errors
    if error:
        logger.error(f"OAuth error: {error} - {error_description}")
        return redirect(f"/?error={error}&message={error_description}")

    if not code:
        logger.error("No authorization code received")
        return redirect("/?error=no_code&message=No authorization code received")

    # Get app URL for redirect
    app_url = request.url_root.rstrip('/')

    try:
        # Exchange authorization code for tokens
        token_url = f"{auth_config.url}/oauth/token"
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': auth_config.client_id,
            'client_secret': auth_config.client_secret,
            'redirect_uri': f"{app_url}/api/auth/callback"
        }

        token_response = http_requests.post(
            token_url,
            data=token_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        if token_response.status_code != 200:
            logger.error(f"Token exchange failed: {token_response.text}")
            return redirect(f"/?error=token_exchange&message=Failed to exchange authorization code")

        tokens = token_response.json()
        access_token = tokens.get('access_token')

        if not access_token:
            return redirect("/?error=no_token&message=No access token received")

        # Create response with redirect to home page
        response = redirect("/")

        # Set the access token in a secure HTTP-only cookie
        response.set_cookie(
            'access_token',
            access_token,
            httponly=True,
            secure=True,
            samesite='Lax',
            max_age=tokens.get('expires_in', 3600)
        )

        logger.info("OAuth callback successful, user authenticated")
        return response

    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return redirect(f"/?error=callback_error&message={str(e)}")


# =============================================================================
# SESSION CHECK
# =============================================================================

@auth_bp.route('/check', methods=['GET'])
@optional_auth
def check_session():
    """
    Check if current session/token is valid.

    Can be called without authentication to check status.
    """
    user = get_current_user()

    if user:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': user.user_id,
                'email': user.email,
                'display_name': user.display_name,
                'is_admin': user.is_admin
            }
        })

    return jsonify({
        'authenticated': False,
        'message': 'No valid session'
    })


# =============================================================================
# TOKEN VALIDATION
# =============================================================================

@auth_bp.route('/validate', methods=['POST'])
def validate_auth_token():
    """
    Validate a JWT token.

    Request body:
        {
            "token": "jwt_token_string"
        }

    Returns validation result and user info if valid.
    """
    data = request.get_json()

    if not data or 'token' not in data:
        return jsonify({
            'valid': False,
            'error': 'Token required'
        }), 400

    user = validate_token(data['token'])

    if user:
        return jsonify({
            'valid': True,
            'user': user.to_dict()
        })

    return jsonify({
        'valid': False,
        'error': 'Invalid or expired token'
    })


# =============================================================================
# DEVELOPMENT ENDPOINTS
# =============================================================================

@auth_bp.route('/dev/token', methods=['POST'])
def get_dev_token():
    """
    Generate a development token (only available in debug mode).

    Request body (optional):
        {
            "user_id": "dev-user",
            "email": "dev@localhost",
            "is_admin": true
        }

    WARNING: Only available when FLASK_ENV=development or debug=True
    """
    if not current_app.debug:
        return jsonify({
            'error': 'Development tokens only available in debug mode'
        }), 403

    data = request.get_json() or {}

    try:
        token = create_dev_token(
            user_id=data.get('user_id', 'dev-user'),
            email=data.get('email', 'developer@localhost'),
            is_admin=data.get('is_admin', True)
        )

        return jsonify({
            'token': token,
            'type': 'Bearer',
            'expires_in': 3600,
            'warning': 'Development token - do not use in production'
        })
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 403


@auth_bp.route('/dev/users', methods=['GET'])
def list_dev_users():
    """
    List all users in database (development only).
    """
    if not current_app.debug:
        return jsonify({
            'error': 'Only available in debug mode'
        }), 403

    users = User.query.all()
    return jsonify({
        'users': [u.to_dict() for u in users],
        'count': len(users)
    })


# =============================================================================
# PROFILE MANAGEMENT
# =============================================================================

@auth_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
    """
    Update user profile.

    Request body:
        {
            "display_name": "New Name"
        }
    """
    user_context = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Get database user
    db_user = User.query.filter_by(xsuaa_id=user_context.user_id).first()

    if not db_user:
        return jsonify({'error': 'User not found'}), 404

    # Update allowed fields
    if 'display_name' in data:
        db_user.display_name = data['display_name']

    db.session.commit()

    return jsonify({
        'success': True,
        'user': db_user.to_dict()
    })


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@auth_bp.errorhandler(401)
def handle_unauthorized(error):
    return jsonify({
        'error': 'Unauthorized',
        'message': 'Valid authentication required'
    }), 401


@auth_bp.errorhandler(403)
def handle_forbidden(error):
    return jsonify({
        'error': 'Forbidden',
        'message': 'Access denied'
    }), 403
