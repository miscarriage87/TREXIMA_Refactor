/**
 * TREXIMA v2.0 - WebSocket Service
 *
 * Socket.IO client for real-time progress updates.
 * Provides connection management, project subscriptions, and event handling.
 */

import { io, Socket } from 'socket.io-client';
import type { ProgressUpdate, OperationResult } from '../types';

type ProgressCallback = (update: ProgressUpdate) => void;
type CompleteCallback = (result: OperationResult) => void;
type ErrorCallback = (error: { code: string; message: string }) => void;
type SavedCallback = (data: { project_id: string; saved_at: string }) => void;

/**
 * WebSocket Service for real-time communication
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type EventCallback = (data: any) => void;

class WebSocketService {
  private socket: Socket | null = null;
  private callbacks: Map<string, Map<string, Set<EventCallback>>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private connectionPromise: Promise<void> | null = null;

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    // Return existing connection promise if already connecting
    if (this.connectionPromise) {
      return this.connectionPromise;
    }

    // Return immediately if already connected
    if (this.socket?.connected) {
      return Promise.resolve();
    }

    this.connectionPromise = new Promise((resolve) => {
      // Determine WebSocket URL - use same origin in production, configurable in dev
      const wsUrl = import.meta.env.VITE_WS_URL || window.location.origin;

      console.log('[WS] Connecting to:', wsUrl);

      this.socket = io(wsUrl, {
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionAttempts: this.maxReconnectAttempts,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        timeout: 20000,
        path: '/socket.io',
      });

      const connectTimeout = setTimeout(() => {
        if (!this.socket?.connected) {
          console.warn('[WS] Connection timeout - falling back to polling');
          this.connectionPromise = null;
          resolve(); // Resolve anyway to not block the app
        }
      }, 10000);

      this.socket.on('connect', () => {
        clearTimeout(connectTimeout);
        console.log('[WS] Connected:', this.socket?.id);
        this.reconnectAttempts = 0;
        this.connectionPromise = null;
        resolve();
      });

      this.socket.on('connect_error', (error) => {
        console.error('[WS] Connection error:', error.message);
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
          clearTimeout(connectTimeout);
          this.connectionPromise = null;
          // Don't reject - just log the error and allow the app to work without WS
          console.warn('[WS] Max reconnection attempts reached, continuing without WebSocket');
          resolve();
        }
        this.reconnectAttempts++;
      });

      this.socket.on('disconnect', (reason) => {
        console.log('[WS] Disconnected:', reason);
      });

      this.socket.on('reconnect', (attemptNumber) => {
        console.log('[WS] Reconnected after', attemptNumber, 'attempts');
      });

      // Set up event listeners for server events
      this.socket.on('progress_update', (data) => {
        console.log('[WS] Progress update:', data);
        this.emitToCallbacks(data.project_id, 'progress', data);
      });

      this.socket.on('operation_complete', (data) => {
        console.log('[WS] Operation complete:', data);
        this.emitToCallbacks(data.project_id, 'complete', data);
      });

      this.socket.on('error', (data) => {
        console.error('[WS] Error:', data);
        this.emitToCallbacks(data.project_id, 'error', data);
      });

      this.socket.on('project_saved', (data) => {
        console.log('[WS] Project saved:', data);
        this.emitToCallbacks(data.project_id, 'saved', data);
      });
    });

    return this.connectionPromise;
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.callbacks.clear();
    this.connectionPromise = null;
  }

  /**
   * Subscribe to project updates
   */
  subscribeToProject(projectId: string): void {
    if (!this.socket?.connected) {
      console.warn('[WS] Not connected, cannot subscribe to project:', projectId);
      return;
    }
    console.log('[WS] Subscribing to project:', projectId);
    this.socket.emit('subscribe_project', { project_id: projectId });
  }

  /**
   * Unsubscribe from project updates
   */
  unsubscribeFromProject(projectId: string): void {
    if (!this.socket?.connected) return;
    console.log('[WS] Unsubscribing from project:', projectId);
    this.socket.emit('unsubscribe_project', { project_id: projectId });
    this.callbacks.delete(projectId);
  }

  /**
   * Cancel an operation
   */
  cancelOperation(projectId: string): void {
    if (!this.socket?.connected) {
      console.warn('[WS] Not connected, cannot cancel operation');
      return;
    }
    console.log('[WS] Cancelling operation for project:', projectId);
    this.socket.emit('cancel_operation', { project_id: projectId });
  }

  /**
   * Register progress callback
   */
  onProgress(projectId: string, callback: ProgressCallback): () => void {
    return this.registerCallback(projectId, 'progress', callback);
  }

  /**
   * Register complete callback
   */
  onComplete(projectId: string, callback: CompleteCallback): () => void {
    return this.registerCallback(projectId, 'complete', callback);
  }

  /**
   * Register error callback
   */
  onError(projectId: string, callback: ErrorCallback): () => void {
    return this.registerCallback(projectId, 'error', callback);
  }

  /**
   * Register project saved callback
   */
  onProjectSaved(projectId: string, callback: SavedCallback): () => void {
    return this.registerCallback(projectId, 'saved', callback);
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.socket?.connected ?? false;
  }

  /**
   * Register a callback for a specific project and event
   */
  private registerCallback(projectId: string, event: string, callback: EventCallback): () => void {
    if (!this.callbacks.has(projectId)) {
      this.callbacks.set(projectId, new Map());
    }
    const projectCallbacks = this.callbacks.get(projectId)!;
    if (!projectCallbacks.has(event)) {
      projectCallbacks.set(event, new Set());
    }
    projectCallbacks.get(event)!.add(callback);

    // Return unsubscribe function
    return () => {
      projectCallbacks.get(event)?.delete(callback);
    };
  }

  /**
   * Emit data to registered callbacks
   */
  private emitToCallbacks(projectId: string, event: string, data: unknown): void {
    const projectCallbacks = this.callbacks.get(projectId);
    if (projectCallbacks?.has(event)) {
      projectCallbacks.get(event)!.forEach((cb) => {
        try {
          cb(data);
        } catch (err) {
          console.error('[WS] Callback error:', err);
        }
      });
    }
  }
}

// Export singleton instance
export const wsService = new WebSocketService();

export default wsService;
