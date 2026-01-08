"""
TREXIMA Web Application

Flask-based web interface for the TREXIMA translation management tool.
"""

import os
import sys
from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from trexima.config import APP_NAME, VERSION, AppPaths
from trexima.web.routes import register_routes


def create_app(config=None):
    """
    Create and configure the Flask application.

    Args:
        config: Optional configuration dictionary

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

    # Default configuration
    app.config.update(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'trexima-dev-key-change-in-production'),
        MAX_CONTENT_LENGTH=100 * 1024 * 1024,  # 100MB max file size
        UPLOAD_FOLDER=os.path.join(web_dir, 'uploads'),
        OUTPUT_FOLDER=os.path.join(web_dir, 'output'),
        ALLOWED_EXTENSIONS={'xml', 'xlsx', 'csv'}
    )

    # Apply custom config
    if config:
        app.config.update(config)

    # Ensure upload and output directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

    # Enable CORS
    CORS(app)

    # Register routes
    register_routes(app)

    # Context processors
    @app.context_processor
    def inject_globals():
        return {
            'app_name': APP_NAME,
            'version': VERSION
        }

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Resource not found'}), 404
        return render_template('error.html', error='Page not found'), 404

    @app.errorhandler(500)
    def server_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('error.html', error='Internal server error'), 500

    return app


def run_web_app(host='127.0.0.1', port=5000, debug=False):
    """
    Run the web application.

    Args:
        host: Host to bind to
        port: Port to listen on
        debug: Enable debug mode
    """
    app = create_app()
    print(f"\n{'='*60}")
    print(f"  {APP_NAME} Web Application v{VERSION}")
    print(f"{'='*60}")
    print(f"\n  Running at: http://{host}:{port}")
    print(f"  Debug mode: {'ON' if debug else 'OFF'}")
    print(f"\n  Press Ctrl+C to stop the server")
    print(f"{'='*60}\n")

    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_web_app(debug=True)
