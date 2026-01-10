/**
 * TREXIMA v2.0 - Progress Overlay Component
 *
 * Real-time progress display for export/import operations.
 */

import { X, Loader2, CheckCircle, XCircle } from 'lucide-react';
import type { ProgressUpdate } from '../../types';

interface ProgressOverlayProps {
  progress: ProgressUpdate | null;
  onCancel?: () => void;
  onClose?: () => void;
}

export default function ProgressOverlay({
  progress,
  onCancel,
  onClose,
}: ProgressOverlayProps) {
  if (!progress) return null;

  const isComplete = progress.percent >= 100;
  const canCancel = !isComplete && onCancel;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center">
            {isComplete ? (
              <CheckCircle className="w-6 h-6 text-green-500 mr-3" />
            ) : (
              <Loader2 className="w-6 h-6 text-sap-blue-500 animate-spin mr-3" />
            )}
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                {progress.operation === 'export' ? 'Exporting Translations' : 'Importing Translations'}
              </h3>
              <p className="text-sm text-gray-500">
                Step {progress.step} of {progress.total_steps}
              </p>
            </div>
          </div>

          {onClose && isComplete && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Progress Content */}
        <div className="px-6 py-6">
          {/* Current Step */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-900">{progress.step_name}</span>
              <span className="text-sm text-gray-600">{Math.round(progress.percent)}%</span>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <div
                className="bg-sap-blue-500 h-3 rounded-full transition-all duration-300 ease-out relative overflow-hidden"
                style={{ width: `${progress.percent}%` }}
              >
                {!isComplete && (
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-shimmer" />
                )}
              </div>
            </div>

            {/* Status Message */}
            <p className="mt-3 text-sm text-gray-600">{progress.message}</p>
          </div>

          {/* Step List */}
          <div className="space-y-2 max-h-64 overflow-y-auto scrollbar-thin">
            {Array.from({ length: progress.total_steps }, (_, i) => {
              const stepNum = i + 1;
              const isCurrentStep = stepNum === progress.step;
              const isCompleted = stepNum < progress.step;

              return (
                <div
                  key={stepNum}
                  className={`flex items-center py-2 px-3 rounded-md transition-colors ${
                    isCurrentStep
                      ? 'bg-sap-blue-50 border border-sap-blue-200'
                      : isCompleted
                      ? 'bg-green-50'
                      : 'bg-gray-50'
                  }`}
                >
                  <div className="flex-shrink-0 mr-3">
                    {isCompleted ? (
                      <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center">
                        <CheckCircle className="w-4 h-4 text-white" />
                      </div>
                    ) : isCurrentStep ? (
                      <div className="w-6 h-6 rounded-full bg-sap-blue-500 flex items-center justify-center">
                        <Loader2 className="w-4 h-4 text-white animate-spin" />
                      </div>
                    ) : (
                      <div className="w-6 h-6 rounded-full bg-gray-300 flex items-center justify-center">
                        <span className="text-xs text-gray-600 font-medium">{stepNum}</span>
                      </div>
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <p
                      className={`text-sm font-medium ${
                        isCurrentStep
                          ? 'text-sap-blue-900'
                          : isCompleted
                          ? 'text-green-800'
                          : 'text-gray-500'
                      }`}
                    >
                      Step {stepNum}
                      {isCurrentStep && `: ${progress.step_name}`}
                    </p>
                  </div>

                  {isCompleted && (
                    <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                  )}
                </div>
              );
            })}
          </div>

          {/* Details */}
          {progress.details && Object.keys(progress.details).length > 0 && (
            <div className="mt-4 p-3 bg-gray-50 rounded-md">
              <p className="text-xs font-medium text-gray-700 mb-2">Details:</p>
              <div className="text-xs text-gray-600 space-y-1">
                {Object.entries(progress.details).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="capitalize">{key.replace(/_/g, ' ')}:</span>
                    <span className="font-medium">{String(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-between items-center">
          <div className="text-xs text-gray-500">
            {isComplete ? (
              <span className="text-green-600 flex items-center">
                <CheckCircle className="w-4 h-4 mr-1" />
                Operation completed successfully
              </span>
            ) : (
              <span>Started {new Date(progress.timestamp).toLocaleTimeString()}</span>
            )}
          </div>

          <div className="flex space-x-2">
            {canCancel && (
              <button onClick={onCancel} className="btn-secondary text-sm">
                <XCircle className="w-4 h-4 mr-2" />
                Cancel Operation
              </button>
            )}

            {isComplete && onClose && (
              <button onClick={onClose} className="btn-primary text-sm">
                <CheckCircle className="w-4 h-4 mr-2" />
                Close
              </button>
            )}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
      `}</style>
    </div>
  );
}
