/**
 * TREXIMA v4.0 - WebSocket Service
 *
 * DISABLED: WebSocket has been disabled due to Cloud Foundry compatibility issues.
 * All methods are no-ops. The app works fully via REST API.
 */

import type { ProgressUpdate, OperationResult } from '../types';

type ProgressCallback = (update: ProgressUpdate) => void;
type CompleteCallback = (result: OperationResult) => void;
type ErrorCallback = (error: { code: string; message: string }) => void;
type SavedCallback = (data: { project_id: string; saved_at: string }) => void;

/**
 * WebSocket Service - DISABLED
 * All methods are no-ops. Real-time updates are not available.
 */
class WebSocketService {
  /**
   * Connect - NO-OP
   */
  connect(): Promise<void> {
    return Promise.resolve();
  }

  /**
   * Disconnect - NO-OP
   */
  disconnect(): void {
    // No-op
  }

  /**
   * Subscribe to project updates - NO-OP
   */
  subscribeToProject(_projectId: string): void {
    // No-op
  }

  /**
   * Unsubscribe from project updates - NO-OP
   */
  unsubscribeFromProject(_projectId: string): void {
    // No-op
  }

  /**
   * Cancel operation - NO-OP
   */
  cancelOperation(_projectId: string): void {
    // No-op
  }

  /**
   * Register progress callback - NO-OP
   */
  onProgress(_projectId: string, _callback: ProgressCallback): () => void {
    return () => {};
  }

  /**
   * Register complete callback - NO-OP
   */
  onComplete(_projectId: string, _callback: CompleteCallback): () => void {
    return () => {};
  }

  /**
   * Register error callback - NO-OP
   */
  onError(_projectId: string, _callback: ErrorCallback): () => void {
    return () => {};
  }

  /**
   * Register project saved callback - NO-OP
   */
  onProjectSaved(_projectId: string, _callback: SavedCallback): () => void {
    return () => {};
  }

  /**
   * Check if connected - always returns false
   */
  isConnected(): boolean {
    return false;
  }
}

// Export singleton instance (all methods are no-ops)
export const wsService = new WebSocketService();

export default wsService;
