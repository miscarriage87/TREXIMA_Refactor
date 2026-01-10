"""
TREXIMA v2.0 - WebSocket Handler

Flask-SocketIO integration for real-time progress updates.
Handles bidirectional communication for export/import operations.
"""

from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask import request, g
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from functools import wraps
import threading

logger = logging.getLogger(__name__)

# Initialize SocketIO with eventlet async mode for production
# Note: Must match gunicorn --worker-class in manifest.yml
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    # Increased timeouts for Cloud Foundry
    ping_timeout=120,
    ping_interval=30,
    # Prefer WebSocket - polling has issues with CF's load balancer
    # WebSocket connections work better with CF's sticky sessions
    transports=['websocket', 'polling'],
    # Allow upgrade from polling to websocket
    allow_upgrades=True,
    # Increase max HTTP buffer size
    max_http_buffer_size=10 * 1024 * 1024
)

# Store for active operations (thread-safe)
_active_operations: Dict[str, Dict[str, Any]] = {}
_operations_lock = threading.Lock()


# =============================================================================
# PROGRESS STEP DEFINITIONS
# =============================================================================

EXPORT_STEPS = [
    {"step": 1, "name": "Initializing", "description": "Setting up export environment"},
    {"step": 2, "name": "Loading Data Models", "description": "Parsing uploaded XML files"},
    {"step": 3, "name": "Connecting to API", "description": "Establishing OData connection"},
    {"step": 4, "name": "Fetching Locales", "description": "Retrieving active languages"},
    {"step": 5, "name": "Extracting EC Fields", "description": "Processing Employee Central fields"},
    {"step": 6, "name": "Extracting Foundation Objects", "description": "Processing FO translations"},
    {"step": 7, "name": "Extracting MDF Objects", "description": "Processing MDF definitions"},
    {"step": 8, "name": "Fetching Picklists", "description": "Retrieving picklist values"},
    {"step": 9, "name": "Generating Workbook", "description": "Creating Excel file"},
    {"step": 10, "name": "Finalizing", "description": "Saving and preparing download"}
]

IMPORT_STEPS = [
    {"step": 1, "name": "Initializing", "description": "Setting up import environment"},
    {"step": 2, "name": "Loading Workbook", "description": "Reading translation workbook"},
    {"step": 3, "name": "Validating Data", "description": "Checking data integrity"},
    {"step": 4, "name": "Analyzing Changes", "description": "Detecting modified translations"},
    {"step": 5, "name": "Generating XML Files", "description": "Creating data model files"},
    {"step": 6, "name": "Connecting to API", "description": "Establishing OData connection"},
    {"step": 7, "name": "Updating Picklists", "description": "Pushing picklist translations"},
    {"step": 8, "name": "Updating FO Translations", "description": "Pushing FO translations"},
    {"step": 9, "name": "Finalizing", "description": "Completing import process"}
]

CONNECTION_STEPS = [
    {"step": 1, "name": "Validating", "description": "Validating connection parameters"},
    {"step": 2, "name": "Connecting", "description": "Establishing connection to SF instance"},
    {"step": 3, "name": "Authenticating", "description": "Verifying credentials"},
    {"step": 4, "name": "Fetching Metadata", "description": "Retrieving instance information"},
    {"step": 5, "name": "Complete", "description": "Connection established successfully"}
]


def get_steps_for_operation(operation: str) -> list:
    """Get step definitions for an operation type."""
    if operation == 'export':
        return EXPORT_STEPS
    elif operation == 'import':
        return IMPORT_STEPS
    elif operation == 'connect':
        return CONNECTION_STEPS
    return []


# =============================================================================
# SOCKETIO EVENT HANDLERS
# =============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    # Authentication is optional for connection
    # Token validation happens when subscribing to a project
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {
        'message': 'Connected to TREXIMA',
        'sid': request.sid,
        'timestamp': datetime.utcnow().isoformat()
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {request.sid}")
    # Clean up any subscriptions
    _cleanup_client_subscriptions(request.sid)


@socketio.on('subscribe_project')
def handle_subscribe(data):
    """
    Subscribe to project updates.

    Expected data: {'project_id': str, 'token': str (optional)}
    """
    project_id = data.get('project_id')

    if not project_id:
        emit('error', {'code': 'INVALID_REQUEST', 'message': 'project_id required'})
        return

    # Join the project room
    room = f'project_{project_id}'
    join_room(room)

    logger.info(f"Client {request.sid} subscribed to project {project_id}")

    emit('subscribed', {
        'project_id': project_id,
        'timestamp': datetime.utcnow().isoformat()
    })

    # Send current operation status if any
    with _operations_lock:
        if project_id in _active_operations:
            op = _active_operations[project_id]
            emit('progress_update', {
                'project_id': project_id,
                'operation': op['operation'],
                'step': op['current_step'],
                'total_steps': op['total_steps'],
                'step_name': op['step_name'],
                'percent': op['percent'],
                'message': op['message'],
                'details': op.get('details', {})
            })


@socketio.on('unsubscribe_project')
def handle_unsubscribe(data):
    """
    Unsubscribe from project updates.

    Expected data: {'project_id': str}
    """
    project_id = data.get('project_id')

    if project_id:
        room = f'project_{project_id}'
        leave_room(room)
        logger.info(f"Client {request.sid} unsubscribed from project {project_id}")

        emit('unsubscribed', {
            'project_id': project_id,
            'timestamp': datetime.utcnow().isoformat()
        })


@socketio.on('cancel_operation')
def handle_cancel(data):
    """
    Request cancellation of an operation.

    Expected data: {'project_id': str}
    """
    project_id = data.get('project_id')

    if not project_id:
        emit('error', {'code': 'INVALID_REQUEST', 'message': 'project_id required'})
        return

    with _operations_lock:
        if project_id in _active_operations:
            _active_operations[project_id]['cancelled'] = True
            logger.info(f"Operation cancellation requested for project {project_id}")

            emit('operation_cancelling', {
                'project_id': project_id,
                'message': 'Cancellation requested, please wait...'
            }, room=f'project_{project_id}')
        else:
            emit('error', {
                'code': 'NO_OPERATION',
                'message': 'No active operation for this project'
            })


@socketio.on('ping')
def handle_ping():
    """Handle ping for connection keep-alive."""
    emit('pong', {'timestamp': datetime.utcnow().isoformat()})


# =============================================================================
# PROGRESS EMITTERS (Called from backend operations)
# =============================================================================

def emit_progress(
    project_id: str,
    operation: str,
    step: int,
    total_steps: int,
    step_name: str,
    percent: float,
    message: str,
    details: Dict[str, Any] = None
):
    """
    Emit progress update to project subscribers.

    Args:
        project_id: Project ID
        operation: Operation type ('export', 'import', 'connect')
        step: Current step number (1-based)
        total_steps: Total number of steps
        step_name: Name of current step
        percent: Progress percentage (0-100)
        message: Human-readable status message
        details: Optional additional details
    """
    # Update active operations tracking
    with _operations_lock:
        _active_operations[project_id] = {
            'operation': operation,
            'current_step': step,
            'total_steps': total_steps,
            'step_name': step_name,
            'percent': percent,
            'message': message,
            'details': details or {},
            'updated_at': datetime.utcnow().isoformat()
        }

    # Emit to project room
    socketio.emit('progress_update', {
        'project_id': project_id,
        'operation': operation,
        'step': step,
        'total_steps': total_steps,
        'step_name': step_name,
        'percent': percent,
        'message': message,
        'details': details or {},
        'timestamp': datetime.utcnow().isoformat()
    }, room=f'project_{project_id}')

    logger.debug(f"Progress: {project_id} - {step}/{total_steps} ({percent:.1f}%) - {message}")


def emit_operation_complete(
    project_id: str,
    operation: str,
    success: bool,
    result: Dict[str, Any] = None,
    error: str = None
):
    """
    Emit operation complete event.

    Args:
        project_id: Project ID
        operation: Operation type
        success: Whether operation succeeded
        result: Result data (if success)
        error: Error message (if failed)
    """
    # Remove from active operations
    with _operations_lock:
        if project_id in _active_operations:
            del _active_operations[project_id]

    socketio.emit('operation_complete', {
        'project_id': project_id,
        'operation': operation,
        'success': success,
        'result': result,
        'error': error,
        'timestamp': datetime.utcnow().isoformat()
    }, room=f'project_{project_id}')

    status = "completed" if success else "failed"
    logger.info(f"Operation {status}: {project_id} - {operation}")


def emit_project_saved(project_id: str):
    """Emit project saved notification."""
    socketio.emit('project_saved', {
        'project_id': project_id,
        'saved_at': datetime.utcnow().isoformat()
    }, room=f'project_{project_id}')


def emit_error(project_id: str, code: str, message: str, details: Dict[str, Any] = None):
    """Emit error event to project subscribers."""
    socketio.emit('error', {
        'project_id': project_id,
        'code': code,
        'message': message,
        'details': details or {},
        'timestamp': datetime.utcnow().isoformat()
    }, room=f'project_{project_id}')

    logger.error(f"Error for project {project_id}: {code} - {message}")


# =============================================================================
# PROGRESS TRACKER CLASS
# =============================================================================

class ProgressTracker:
    """
    Context manager for tracking operation progress.

    Usage:
        with ProgressTracker(project_id, 'export') as tracker:
            tracker.update(1, "Loading files")
            # ... do work ...
            tracker.update(2, "Processing data")
            # ... more work ...
            tracker.complete(result={'file_id': '...'})
    """

    def __init__(self, project_id: str, operation: str):
        self.project_id = project_id
        self.operation = operation
        self.steps = get_steps_for_operation(operation)
        self.total_steps = len(self.steps)
        self.current_step = 0
        self.cancelled = False
        self._started_at = None

    def __enter__(self):
        self._started_at = datetime.utcnow()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clean up on exit
        with _operations_lock:
            if self.project_id in _active_operations:
                del _active_operations[self.project_id]

        # If exception occurred, emit error
        if exc_type is not None:
            emit_operation_complete(
                self.project_id,
                self.operation,
                success=False,
                error=str(exc_val)
            )
            return False  # Don't suppress exception

        return False

    def update(self, step: int, message: str, details: Dict[str, Any] = None, sub_progress: float = 0):
        """
        Update progress to a specific step.

        Args:
            step: Step number (1-based)
            message: Status message
            details: Optional details
            sub_progress: Progress within current step (0-1)
        """
        # Check for cancellation
        with _operations_lock:
            if self.project_id in _active_operations:
                if _active_operations[self.project_id].get('cancelled'):
                    self.cancelled = True
                    raise OperationCancelled(f"Operation cancelled by user")

        self.current_step = step
        step_info = self.steps[step - 1] if step <= len(self.steps) else {"name": "Processing"}

        # Calculate overall percentage
        base_percent = ((step - 1) / self.total_steps) * 100
        step_percent = (sub_progress / self.total_steps) * 100
        percent = min(base_percent + step_percent, 99)  # Cap at 99 until complete

        emit_progress(
            project_id=self.project_id,
            operation=self.operation,
            step=step,
            total_steps=self.total_steps,
            step_name=step_info.get('name', 'Processing'),
            percent=percent,
            message=message,
            details=details
        )

    def complete(self, result: Dict[str, Any] = None):
        """Mark operation as complete."""
        emit_progress(
            project_id=self.project_id,
            operation=self.operation,
            step=self.total_steps,
            total_steps=self.total_steps,
            step_name="Complete",
            percent=100,
            message="Operation completed successfully"
        )

        emit_operation_complete(
            project_id=self.project_id,
            operation=self.operation,
            success=True,
            result=result
        )

    def fail(self, error: str, details: Dict[str, Any] = None):
        """Mark operation as failed."""
        emit_operation_complete(
            project_id=self.project_id,
            operation=self.operation,
            success=False,
            error=error
        )

    def is_cancelled(self) -> bool:
        """Check if operation was cancelled."""
        with _operations_lock:
            if self.project_id in _active_operations:
                return _active_operations[self.project_id].get('cancelled', False)
        return self.cancelled


class OperationCancelled(Exception):
    """Exception raised when operation is cancelled by user."""
    pass


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def _cleanup_client_subscriptions(sid: str):
    """Clean up subscriptions for disconnected client."""
    # SocketIO handles room cleanup automatically
    # Log for debugging purposes
    logger.debug(f"Cleaning up subscriptions for disconnected client: {sid}")


def get_active_operations() -> Dict[str, Dict[str, Any]]:
    """Get all active operations (for admin/debugging)."""
    with _operations_lock:
        return dict(_active_operations)


def is_operation_active(project_id: str) -> bool:
    """Check if there's an active operation for a project."""
    with _operations_lock:
        return project_id in _active_operations


def cancel_operation(project_id: str) -> bool:
    """
    Cancel an active operation.

    Returns:
        True if operation was found and cancellation requested
    """
    with _operations_lock:
        if project_id in _active_operations:
            _active_operations[project_id]['cancelled'] = True
            return True
    return False


def init_websocket(app):
    """Initialize WebSocket with Flask app."""
    socketio.init_app(app)
    logger.info("WebSocket initialized")
    return socketio
