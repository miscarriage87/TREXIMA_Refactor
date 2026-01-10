"""
TREXIMA v2.0 Web Application

Enterprise-grade Flask web application with:
- SAP BTP XSUAA authentication
- PostgreSQL database for persistence
- S3-compatible Object Store for files
- WebSocket for real-time progress updates
- React SPA frontend support
"""

import os
import sys
import json
import logging
from flask import Flask, render_template, jsonify, request, send_from_directory, make_response
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from trexima.config import APP_NAME, VERSION


def create_app(config=None, testing=False):
    """
    Create and configure the Flask application.

    Args:
        config: Optional configuration dictionary
        testing: Enable testing mode

    Returns:
        Flask application instance
    """
    # Get the absolute path to the web directory
    web_dir = os.path.dirname(os.path.abspath(__file__))

    app = Flask(
        __name__,
        template_folder=os.path.join(web_dir, 'templates'),
        static_folder=os.path.join(web_dir, 'static')
    )

    # ==========================================================================
    # CONFIGURATION
    # ==========================================================================

    # Determine if we're in production
    is_production = os.environ.get('FLASK_ENV') == 'production'

    # Get SECRET_KEY - require in production, use dev default only in development
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        if is_production:
            # Generate a random key in production if not set (sessions won't persist across restarts)
            import secrets
            secret_key = secrets.token_hex(32)
            logger.warning("SECRET_KEY not set in production! Using random key - sessions will not persist across restarts.")
        else:
            secret_key = 'trexima-dev-key-for-local-development-only'

    # Default configuration
    app.config.update(
        # Security
        SECRET_KEY=secret_key,

        # File uploads
        MAX_CONTENT_LENGTH=100 * 1024 * 1024,  # 100MB max file size
        UPLOAD_FOLDER=os.path.join(web_dir, 'uploads'),
        OUTPUT_FOLDER=os.path.join(web_dir, 'output'),
        ALLOWED_EXTENSIONS={'xml', 'xlsx', 'csv'},

        # Database - will be overridden by VCAP_SERVICES in production
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'DATABASE_URL',
            'sqlite:///' + os.path.join(web_dir, 'trexima.db')
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={
            'pool_pre_ping': True,
            'pool_recycle': 300
        },

        # Session
        SESSION_TYPE='filesystem',

        # App info
        APP_NAME=APP_NAME,
        VERSION=VERSION,

        # Testing
        TESTING=testing
    )

    # Parse VCAP_SERVICES for BTP environment
    vcap_services = os.environ.get('VCAP_SERVICES')
    if vcap_services:
        try:
            vcap = json.loads(vcap_services)

            # PostgreSQL configuration
            for service_name in ['postgresql-db', 'postgresql', 'trexima-sql']:
                if service_name in vcap:
                    pg_creds = vcap[service_name][0]['credentials']
                    db_uri = pg_creds.get('uri') or (
                        f"postgresql://{pg_creds['username']}:{pg_creds['password']}"
                        f"@{pg_creds['hostname']}:{pg_creds['port']}/{pg_creds['dbname']}"
                    )
                    # Convert postgres:// to postgresql:// for SQLAlchemy 2.0 compatibility
                    if db_uri.startswith('postgres://'):
                        db_uri = db_uri.replace('postgres://', 'postgresql://', 1)
                    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
                    logger.info(f"PostgreSQL configured from {service_name}")
                    break

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse VCAP_SERVICES: {e}")

    # Apply custom config
    if config:
        app.config.update(config)

    # Ensure local directories exist (for development)
    if not vcap_services:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

    # ==========================================================================
    # INITIALIZE EXTENSIONS
    # ==========================================================================

    # Enable CORS - use CORS_ORIGINS env var or restrictive defaults
    cors_origins_env = os.environ.get('CORS_ORIGINS', '')
    if cors_origins_env == '*':
        cors_origins = '*'  # Allow all (only for development/specific cases)
    elif cors_origins_env:
        cors_origins = [origin.strip() for origin in cors_origins_env.split(',') if origin.strip()]
    else:
        # Default to localhost only for development
        cors_origins = ["http://localhost:5173", "http://localhost:5000", "http://127.0.0.1:5173", "http://127.0.0.1:5000"]
        if not is_production:
            logger.info("CORS_ORIGINS not set, using localhost defaults for development")

    CORS(app, resources={
        r"/api/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    # Initialize database
    from trexima.web.models import db, init_db
    db.init_app(app)

    # Initialize Flask-Migrate for database migrations
    from flask_migrate import Migrate
    migrate = Migrate(app, db)

    # Initialize storage service
    from trexima.web.storage import init_storage
    storage = init_storage(app)

    # Initialize authentication
    from trexima.web.auth import init_auth
    auth_config = init_auth(app)

    # Initialize WebSocket
    from trexima.web.websocket import init_websocket, socketio
    init_websocket(app)

    # ==========================================================================
    # DATABASE INITIALIZATION
    # ==========================================================================
    # In production, use 'flask db upgrade' for migrations
    # db.create_all() is used as fallback for development/testing when migrations aren't set up

    with app.app_context():
        # Check if migrations directory exists
        migrations_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'migrations')
        if not os.path.exists(migrations_dir):
            # No migrations - use create_all for development
            db.create_all()
            logger.info("Database tables created via db.create_all() (no migrations found)")
        else:
            logger.info("Migrations directory found - use 'flask db upgrade' for schema changes")

    # ==========================================================================
    # REGISTER BLUEPRINTS
    # ==========================================================================

    # Legacy routes (for backward compatibility during transition)
    from trexima.web.routes import register_routes
    register_routes(app)

    # New API blueprints
    try:
        from trexima.web.blueprints.auth_bp import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        logger.info("Registered auth blueprint")
    except ImportError:
        logger.warning("Auth blueprint not yet implemented")

    try:
        from trexima.web.blueprints.projects_bp import projects_bp
        app.register_blueprint(projects_bp, url_prefix='/api/projects')
        logger.info("Registered projects blueprint")
    except ImportError:
        logger.warning("Projects blueprint not yet implemented")

    try:
        from trexima.web.blueprints.admin_bp import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
        logger.info("Registered admin blueprint")
    except ImportError:
        logger.warning("Admin blueprint not yet implemented")

    try:
        from trexima.web.blueprints.export_bp import export_bp
        app.register_blueprint(export_bp, url_prefix='/api')
        logger.info("Registered export blueprint")
    except ImportError:
        logger.warning("Export blueprint not yet implemented")

    try:
        from trexima.web.blueprints.import_bp import import_bp
        app.register_blueprint(import_bp, url_prefix='/api')
        logger.info("Registered import blueprint")
    except ImportError:
        logger.warning("Import blueprint not yet implemented")

    # ==========================================================================
    # REACT SPA SUPPORT
    # ==========================================================================

    # Serve React frontend from static/app folder (copied during build)
    frontend_dist = os.path.join(web_dir, 'static', 'app')

    # Log frontend directory contents at startup for debugging
    logger.info(f"Frontend dist path: {frontend_dist}")
    if os.path.exists(frontend_dist):
        try:
            contents = os.listdir(frontend_dist)
            logger.info(f"Frontend dist contents: {contents}")
            assets_dir = os.path.join(frontend_dist, 'assets')
            if os.path.exists(assets_dir):
                assets = os.listdir(assets_dir)
                logger.info(f"Assets dir contents: {assets[:10]}...")  # First 10 files
        except Exception as e:
            logger.error(f"Error listing frontend dir: {e}")
    else:
        logger.warning(f"Frontend dist does NOT exist at: {frontend_dist}")

    # Register SPA route with lowest priority (catch-all)
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_spa(path):
        """Serve React SPA at root (catch-all for unmatched routes)."""
        # Check if frontend exists
        index_path = os.path.join(frontend_dist, 'index.html')

        # Log for debugging (only for asset requests to avoid spam)
        if path.startswith('assets/'):
            full_path = os.path.join(frontend_dist, path)
            exists = os.path.exists(full_path)
            logger.info(f"Asset request: {path} -> {full_path} (exists: {exists})")

        if os.path.exists(index_path):
            # Serve static assets from app/assets
            if path.startswith('assets/'):
                asset_path = os.path.join(frontend_dist, path)
                if os.path.exists(asset_path):
                    logger.info(f"Serving asset: {path}")
                    return send_from_directory(frontend_dist, path)
                else:
                    logger.warning(f"Asset not found: {asset_path}")

            # Serve other static files (vite.svg, etc)
            if path and path != 'index.html':
                file_path = os.path.join(frontend_dist, path)
                if os.path.exists(file_path):
                    return send_from_directory(frontend_dist, path)

            # Serve index.html for root and all unmatched routes (SPA client-side routing)
            return send_from_directory(frontend_dist, 'index.html')

        # Fallback to legacy UI if React not built
        logger.warning(f"React frontend not found, falling back to legacy UI")
        return render_template('index.html')

    # ==========================================================================
    # CONTEXT PROCESSORS
    # ==========================================================================

    @app.context_processor
    def inject_globals():
        """Inject global variables into templates."""
        return {
            'app_name': APP_NAME,
            'version': VERSION,
            'is_production': os.environ.get('FLASK_ENV') == 'production'
        }

    # ==========================================================================
    # HEALTH CHECK ENDPOINT
    # ==========================================================================

    @app.route('/health')
    @app.route('/api/health')
    def health_check():
        """Health check endpoint for Cloud Foundry."""
        health = {
            'status': 'healthy',
            'app': APP_NAME,
            'version': VERSION,
            'checks': {}
        }

        # Check database
        try:
            db.session.execute(db.text('SELECT 1'))
            health['checks']['database'] = 'ok'
        except Exception as e:
            health['checks']['database'] = f'error: {str(e)}'
            health['status'] = 'degraded'

        # Check storage
        try:
            if storage.is_initialized:
                health['checks']['storage'] = 'ok'
            else:
                health['checks']['storage'] = 'not initialized'
        except Exception as e:
            health['checks']['storage'] = f'error: {str(e)}'

        # Check auth
        health['checks']['auth'] = 'ok' if auth_config.is_initialized else 'not configured'

        status_code = 200 if health['status'] == 'healthy' else 503
        return jsonify(health), status_code

    # ==========================================================================
    # API INFO ENDPOINT
    # ==========================================================================

    @app.route('/api/info')
    def api_info():
        """API information endpoint."""
        return jsonify({
            'name': APP_NAME,
            'version': VERSION,
            'api_version': '4.0',
            'endpoints': {
                'auth': '/api/auth',
                'projects': '/api/projects',
                'export': '/api/projects/{id}/export',
                'import': '/api/projects/{id}/import',
                'admin': '/api/admin',
                'legacy': '/api'
            },
            'features': {
                'authentication': auth_config.is_initialized,
                'websocket': True,
                'storage': storage.is_initialized
            }
        })

    # ==========================================================================
    # ERROR HANDLERS
    # ==========================================================================

    @app.errorhandler(400)
    def bad_request(error):
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Bad request',
                'message': str(error.description) if hasattr(error, 'description') else 'Invalid request'
            }), 400
        return render_template('error.html', error='Bad request'), 400

    @app.errorhandler(401)
    def unauthorized(error):
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Authentication required'
            }), 401
        return render_template('error.html', error='Unauthorized'), 401

    @app.errorhandler(403)
    def forbidden(error):
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Forbidden',
                'message': 'Access denied'
            }), 403
        return render_template('error.html', error='Access denied'), 403

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Not found',
                'message': 'Resource not found'
            }), 404
        return render_template('error.html', error='Page not found'), 404

    @app.errorhandler(500)
    def server_error(error):
        logger.error(f"Internal server error: {error}")
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred'
            }), 500
        return render_template('error.html', error='Internal server error'), 500

    # ==========================================================================
    # REQUEST LOGGING
    # ==========================================================================

    @app.before_request
    def log_request():
        """Log incoming requests (debug mode only)."""
        if app.debug:
            logger.debug(f"{request.method} {request.path}")

    @app.after_request
    def log_response(response):
        """Log response status."""
        if app.debug and response.status_code >= 400:
            logger.warning(f"{request.method} {request.path} -> {response.status_code}")
        return response

    logger.info(f"TREXIMA v{VERSION} application created")
    return app


def run_web_app(host='0.0.0.0', port=5000, debug=False):
    """
    Run the web application with WebSocket support.

    Args:
        host: Host to bind to
        port: Port to listen on
        debug: Enable debug mode
    """
    app = create_app()

    # Import socketio for running with WebSocket support
    from trexima.web.websocket import socketio

    print(f"\n{'='*60}")
    print(f"  {APP_NAME} Web Application v{VERSION}")
    print(f"{'='*60}")
    print(f"\n  Running at: http://{host}:{port}")
    print(f"  Debug mode: {'ON' if debug else 'OFF'}")
    print(f"\n  Press Ctrl+C to stop the server")
    print(f"{'='*60}\n")

    # Run with SocketIO for WebSocket support
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        use_reloader=debug,
        log_output=True
    )


# =============================================================================
# WSGI ENTRY POINT (for gunicorn)
# =============================================================================

# Create app instance for WSGI servers
application = create_app()


if __name__ == '__main__':
    run_web_app(debug=True)
