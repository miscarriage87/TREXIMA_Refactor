"""
TREXIMA v4.0 - Authentication Module

SAP BTP XSUAA integration for user authentication.
Handles JWT token validation and user context.
"""

from functools import wraps
from flask import request, jsonify, g, current_app
import os
import json
import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import SAP XSSEC library
try:
    from sap import xssec
    XSSEC_AVAILABLE = True
except ImportError:
    XSSEC_AVAILABLE = False
    logger.warning("sap-xssec not available, using mock authentication")

# Try to import jose for JWT handling
try:
    from jose import jwt, JWTError
    JOSE_AVAILABLE = True
except ImportError:
    JOSE_AVAILABLE = False
    logger.warning("python-jose not available")


class AuthConfig:
    """Authentication configuration from XSUAA service."""

    def __init__(self):
        self.xsappname = None
        self.client_id = None
        self.client_secret = None
        self.url = None
        self.uaa_domain = None
        self.verificationkey = None
        self._credentials = {}
        self._initialized = False

    def init_from_vcap(self):
        """Initialize from VCAP_SERVICES environment variable."""
        vcap_services = os.environ.get('VCAP_SERVICES', '{}')

        try:
            vcap = json.loads(vcap_services)
        except json.JSONDecodeError:
            logger.warning("Could not parse VCAP_SERVICES")
            return False

        # Look for XSUAA service
        xsuaa_creds = None
        for service_name in ['xsuaa', 'trexima-auth']:
            if service_name in vcap:
                xsuaa_creds = vcap[service_name][0].get('credentials', {})
                break

        if not xsuaa_creds:
            logger.warning("XSUAA service not found in VCAP_SERVICES")
            return False

        self._credentials = xsuaa_creds
        self.xsappname = xsuaa_creds.get('xsappname')
        self.client_id = xsuaa_creds.get('clientid')
        self.client_secret = xsuaa_creds.get('clientsecret')
        self.url = xsuaa_creds.get('url')
        self.uaa_domain = xsuaa_creds.get('uaadomain')
        self.verificationkey = xsuaa_creds.get('verificationkey')

        self._initialized = True
        logger.info(f"XSUAA config initialized: {self.xsappname}")
        return True

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def credentials(self) -> Dict[str, Any]:
        return self._credentials

    def get_admin_scope(self) -> str:
        """Get the admin scope name."""
        return f"{self.xsappname}.admin" if self.xsappname else "admin"

    def get_user_scope(self) -> str:
        """Get the user scope name."""
        return f"{self.xsappname}.user" if self.xsappname else "user"


# Global auth config instance
auth_config = AuthConfig()


class UserContext:
    """User context from validated JWT token."""

    def __init__(
        self,
        user_id: str,
        email: str,
        display_name: str = None,
        is_admin: bool = False,
        scopes: list = None,
        token: str = None
    ):
        self.user_id = user_id
        self.email = email
        self.display_name = display_name or email.split('@')[0]
        self.is_admin = is_admin
        self.scopes = scopes or []
        self.token = token
        self.authenticated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'email': self.email,
            'display_name': self.display_name,
            'is_admin': self.is_admin,
            'scopes': self.scopes
        }

    def has_scope(self, scope: str) -> bool:
        """Check if user has a specific scope."""
        return scope in self.scopes


def init_auth(app):
    """Initialize authentication with Flask app."""
    # Try to initialize from VCAP_SERVICES
    if not auth_config.init_from_vcap():
        # Check for development mode
        if app.debug or os.environ.get('FLASK_ENV') == 'development':
            logger.info("Running in development mode, authentication will be mocked")
        else:
            logger.warning("XSUAA not configured, authentication may not work properly")

    return auth_config


def extract_token_from_request() -> Optional[str]:
    """Extract JWT token from Authorization header, cookies, or query params."""
    # First check Authorization header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]

    # Check for token in cookies (set by OAuth callback)
    token = request.cookies.get('access_token')
    if token:
        return token

    # Also check for token in query params (for WebSocket connections)
    token = request.args.get('token')
    if token:
        return token

    return None


def validate_token(token: str) -> Optional[UserContext]:
    """
    Validate JWT token and return user context.

    Args:
        token: JWT token string

    Returns:
        UserContext if valid, None otherwise
    """
    if not token:
        return None

    # Use SAP XSSEC if available
    if XSSEC_AVAILABLE and auth_config.is_initialized:
        try:
            security_context = xssec.create_security_context(
                token,
                auth_config.credentials
            )

            user_id = security_context.get_logon_name()
            email = security_context.get_email() or f"{user_id}@unknown"
            display_name = security_context.get_given_name()
            if security_context.get_family_name():
                display_name = f"{display_name} {security_context.get_family_name()}"

            # Check scopes
            is_admin = security_context.check_scope(auth_config.get_admin_scope())
            scopes = []
            if security_context.check_scope(auth_config.get_user_scope()):
                scopes.append('user')
            if is_admin:
                scopes.append('admin')

            return UserContext(
                user_id=user_id,
                email=email,
                display_name=display_name,
                is_admin=is_admin,
                scopes=scopes,
                token=token
            )
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return None

    # Fallback: Try to decode JWT manually (for development/testing)
    if JOSE_AVAILABLE:
        try:
            # Decode without verification for development
            payload = jwt.get_unverified_claims(token)

            user_id = payload.get('user_name') or payload.get('sub') or 'unknown'
            email = payload.get('email') or f"{user_id}@example.com"
            display_name = payload.get('given_name', '')
            if payload.get('family_name'):
                display_name = f"{display_name} {payload.get('family_name')}".strip()

            scopes = payload.get('scope', [])
            is_admin = 'admin' in scopes or any('admin' in s for s in scopes)

            logger.warning("Using unverified JWT decode (development mode)")

            return UserContext(
                user_id=user_id,
                email=email,
                display_name=display_name or email.split('@')[0],
                is_admin=is_admin,
                scopes=scopes,
                token=token
            )
        except JWTError as e:
            logger.error(f"JWT decode failed: {e}")
            return None

    # Development fallback: Mock user
    if current_app.debug or os.environ.get('FLASK_ENV') == 'development':
        logger.warning("Using mock authentication (development mode)")
        return UserContext(
            user_id='dev-user',
            email='developer@localhost',
            display_name='Developer',
            is_admin=True,
            scopes=['user', 'admin'],
            token=token
        )

    return None


def get_current_user() -> Optional[UserContext]:
    """Get current authenticated user from Flask g object."""
    return getattr(g, 'user', None)


def require_auth(f: Callable) -> Callable:
    """
    Decorator to require valid authentication.

    Usage:
        @app.route('/api/protected')
        @require_auth
        def protected_endpoint():
            user = get_current_user()
            return jsonify({'user': user.email})
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = extract_token_from_request()

        if not token:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Missing authorization token'
            }), 401

        user = validate_token(token)

        if not user:
            return jsonify({
                'error': 'Invalid token',
                'message': 'The provided token is invalid or expired'
            }), 401

        # Store user in Flask g for access in route handlers
        g.user = user

        return f(*args, **kwargs)

    return decorated


def require_admin(f: Callable) -> Callable:
    """
    Decorator to require admin privileges.

    Usage:
        @app.route('/api/admin/users')
        @require_admin
        def list_all_users():
            ...
    """
    @wraps(f)
    @require_auth
    def decorated(*args, **kwargs):
        user = get_current_user()

        if not user or not user.is_admin:
            return jsonify({
                'error': 'Access denied',
                'message': 'Administrator privileges required'
            }), 403

        return f(*args, **kwargs)

    return decorated


def optional_auth(f: Callable) -> Callable:
    """
    Decorator for optional authentication.
    Sets g.user if token is valid, but doesn't require it.

    Usage:
        @app.route('/api/public')
        @optional_auth
        def public_endpoint():
            user = get_current_user()  # May be None
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = extract_token_from_request()

        if token:
            user = validate_token(token)
            if user:
                g.user = user

        return f(*args, **kwargs)

    return decorated


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_oauth_config() -> Dict[str, Any]:
    """
    Get OAuth configuration for frontend.

    Returns configuration needed for OAuth2 PKCE flow.
    """
    if not auth_config.is_initialized:
        return {
            'configured': False,
            'message': 'XSUAA not configured'
        }

    return {
        'configured': True,
        'authorization_endpoint': f"{auth_config.url}/oauth/authorize",
        'token_endpoint': f"{auth_config.url}/oauth/token",
        'client_id': auth_config.client_id,
        'scopes': ['openid', auth_config.get_user_scope()]
    }


def create_dev_token(user_id: str = 'dev-user', email: str = 'dev@localhost', is_admin: bool = True) -> str:
    """
    Create a development JWT token (for testing only).

    WARNING: Only use in development/testing environments!
    """
    if not JOSE_AVAILABLE:
        return 'dev-token'

    if not current_app.debug and os.environ.get('FLASK_ENV') != 'development':
        raise RuntimeError("Development tokens can only be created in debug mode")

    payload = {
        'sub': user_id,
        'user_name': user_id,
        'email': email,
        'given_name': 'Dev',
        'family_name': 'User',
        'scope': ['user', 'admin'] if is_admin else ['user'],
        'exp': datetime.utcnow().timestamp() + 3600
    }

    # Use a simple secret for dev tokens
    return jwt.encode(payload, 'dev-secret', algorithm='HS256')
