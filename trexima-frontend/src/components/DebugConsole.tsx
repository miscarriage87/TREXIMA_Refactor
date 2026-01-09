/**
 * TREXIMA v4.0 - Debug Console
 *
 * Collapsible debug panel showing API calls, WebSocket events, and errors.
 * Only visible to admin users.
 */

import { useState, useEffect, useRef } from 'react';
import { ChevronUp, ChevronDown, Trash2, Bug, Wifi, WifiOff, AlertCircle, CheckCircle, Clock } from 'lucide-react';
// Note: Wifi/WifiOff kept for log icons but WebSocket status removed from header

export interface LogEntry {
  id: string;
  timestamp: Date;
  type: 'api-request' | 'api-response' | 'api-error' | 'ws-event' | 'ws-connect' | 'ws-disconnect' | 'error' | 'info';
  method?: string;
  url?: string;
  status?: number;
  duration?: number;
  data?: unknown;
  message?: string;
}

// Global log store
class DebugLogStore {
  private logs: LogEntry[] = [];
  private listeners: Set<() => void> = new Set();
  private maxLogs = 200;

  addLog(entry: Omit<LogEntry, 'id' | 'timestamp'>) {
    const logEntry: LogEntry = {
      ...entry,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
    };

    this.logs.unshift(logEntry);

    // Trim old logs
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(0, this.maxLogs);
    }

    this.notifyListeners();
  }

  getLogs() {
    return this.logs;
  }

  clear() {
    this.logs = [];
    this.notifyListeners();
  }

  subscribe(listener: () => void) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notifyListeners() {
    this.listeners.forEach(listener => listener());
  }
}

export const debugLog = new DebugLogStore();

// Helper to log API requests
export function logApiRequest(method: string, url: string, data?: unknown) {
  debugLog.addLog({
    type: 'api-request',
    method,
    url,
    data,
    message: `${method} ${url}`,
  });
}

export function logApiResponse(method: string, url: string, status: number, duration: number, data?: unknown) {
  debugLog.addLog({
    type: status >= 400 ? 'api-error' : 'api-response',
    method,
    url,
    status,
    duration,
    data,
    message: `${method} ${url} → ${status} (${duration}ms)`,
  });
}

export function logApiError(method: string, url: string, error: unknown) {
  debugLog.addLog({
    type: 'api-error',
    method,
    url,
    data: error,
    message: `${method} ${url} → ERROR: ${error instanceof Error ? error.message : String(error)}`,
  });
}

export function logWsEvent(event: string, data?: unknown) {
  debugLog.addLog({
    type: 'ws-event',
    message: `WS: ${event}`,
    data,
  });
}

export function logWsConnect() {
  debugLog.addLog({
    type: 'ws-connect',
    message: 'WebSocket connected',
  });
}

export function logWsDisconnect(reason?: string) {
  debugLog.addLog({
    type: 'ws-disconnect',
    message: `WebSocket disconnected${reason ? `: ${reason}` : ''}`,
  });
}

export function logError(message: string, error?: unknown) {
  debugLog.addLog({
    type: 'error',
    message,
    data: error,
  });
}

export function logInfo(message: string, data?: unknown) {
  debugLog.addLog({
    type: 'info',
    message,
    data,
  });
}

// Debug Console Component
interface DebugConsoleProps {
  isAdmin?: boolean;
}

export default function DebugConsole({ isAdmin = false }: DebugConsoleProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Subscribe to log updates
  useEffect(() => {
    const updateLogs = () => setLogs([...debugLog.getLogs()]);
    updateLogs();
    const unsubscribe = debugLog.subscribe(updateLogs);
    return () => { unsubscribe(); };
  }, []);

  if (!isAdmin) return null;

  const filteredLogs = filter === 'all'
    ? logs
    : logs.filter(log => {
        if (filter === 'api') return log.type.startsWith('api');
        if (filter === 'ws') return log.type.startsWith('ws');
        if (filter === 'error') return log.type === 'api-error' || log.type === 'error';
        return true;
      });

  const getLogIcon = (type: LogEntry['type']) => {
    switch (type) {
      case 'api-request':
        return <Clock className="w-3 h-3 text-blue-400" />;
      case 'api-response':
        return <CheckCircle className="w-3 h-3 text-green-400" />;
      case 'api-error':
        return <AlertCircle className="w-3 h-3 text-red-400" />;
      case 'ws-event':
        return <Wifi className="w-3 h-3 text-purple-400" />;
      case 'ws-connect':
        return <Wifi className="w-3 h-3 text-green-400" />;
      case 'ws-disconnect':
        return <WifiOff className="w-3 h-3 text-orange-400" />;
      case 'error':
        return <AlertCircle className="w-3 h-3 text-red-400" />;
      default:
        return <Bug className="w-3 h-3 text-gray-400" />;
    }
  };

  const getLogColor = (type: LogEntry['type']) => {
    switch (type) {
      case 'api-request':
        return 'text-blue-300';
      case 'api-response':
        return 'text-green-300';
      case 'api-error':
      case 'error':
        return 'text-red-300';
      case 'ws-event':
        return 'text-purple-300';
      case 'ws-connect':
        return 'text-green-300';
      case 'ws-disconnect':
        return 'text-orange-300';
      default:
        return 'text-gray-300';
    }
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-gray-900 text-white font-mono text-xs border-t border-gray-700">
      {/* Header */}
      <div
        className="flex items-center justify-between px-3 py-2 bg-gray-800 cursor-pointer select-none"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-3">
          <Bug className="w-4 h-4 text-yellow-400" />
          <span className="font-semibold">Debug Console</span>
          <span className="text-gray-400">({logs.length} entries)</span>
        </div>
        <div className="flex items-center space-x-2">
          {isExpanded && (
            <>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                onClick={(e) => e.stopPropagation()}
                className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-xs"
              >
                <option value="all">All</option>
                <option value="api">API</option>
                <option value="ws">WebSocket</option>
                <option value="error">Errors</option>
              </select>
              <button
                onClick={(e) => { e.stopPropagation(); debugLog.clear(); }}
                className="p-1 hover:bg-gray-700 rounded"
                title="Clear logs"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </>
          )}
          {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </div>
      </div>

      {/* Log entries */}
      {isExpanded && (
        <div className="h-64 overflow-y-auto p-2 space-y-1">
          {filteredLogs.length === 0 ? (
            <div className="text-gray-500 text-center py-4">No logs yet</div>
          ) : (
            filteredLogs.map((log) => (
              <div
                key={log.id}
                className={`flex items-start space-x-2 py-1 px-2 rounded hover:bg-gray-800 ${getLogColor(log.type)}`}
              >
                <span className="flex-shrink-0 mt-0.5">{getLogIcon(log.type)}</span>
                <span className="text-gray-500 flex-shrink-0">
                  {log.timestamp.toLocaleTimeString()}
                </span>
                <span className="flex-1 break-all">
                  {log.message}
                  {log.status && (
                    <span className={`ml-2 px-1 rounded ${log.status >= 400 ? 'bg-red-900' : 'bg-green-900'}`}>
                      {log.status}
                    </span>
                  )}
                  {log.duration !== undefined && (
                    <span className="ml-2 text-gray-500">{log.duration}ms</span>
                  )}
                </span>
                {log.data !== undefined && log.data !== null && (
                  <details className="flex-shrink-0">
                    <summary className="cursor-pointer text-gray-500 hover:text-gray-300">data</summary>
                    <pre className="mt-1 p-2 bg-gray-800 rounded text-xs overflow-auto max-w-md max-h-32">
                      {JSON.stringify(log.data, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            ))
          )}
          <div ref={logsEndRef} />
        </div>
      )}
    </div>
  );
}
