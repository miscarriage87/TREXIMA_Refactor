/**
 * TREXIMA v2.0 - Export Summary Component
 *
 * Summary and action panel for starting export operation.
 * Includes polling for progress since WebSocket is disabled.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  FileSpreadsheet,
  Download,
  CheckCircle,
  AlertCircle,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { useProjectStore } from '../../store/projectStore';
import projectsApi from '../../api/projects';

interface ExportSummaryProps {
  projectId: string;
}

export default function ExportSummary({ projectId }: ExportSummaryProps) {
  const {
    currentProject,
    files,
    downloads,
    startExport,
    fetchDownloads,
    fetchProject,
    isLoading,
    error,
  } = useProjectStore();

  const [isExporting, setIsExporting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [exportProgress, setExportProgress] = useState<{
    active: boolean;
    message?: string;
    progress?: number;
  }>({ active: false });

  // Poll for operation status
  const pollStatus = useCallback(async () => {
    try {
      const status = await projectsApi.status.get(projectId);
      if (status.has_active_operation) {
        setExportProgress({
          active: true,
          message: status.operation?.message || 'Processing...',
          progress: status.operation?.progress,
        });
        return true; // Still active
      } else {
        setExportProgress({ active: false });
        return false; // Complete
      }
    } catch {
      return false;
    }
  }, [projectId]);

  // Start polling when export begins
  useEffect(() => {
    let pollInterval: ReturnType<typeof setInterval> | null = null;

    if (isExporting || exportProgress.active) {
      pollInterval = setInterval(async () => {
        const stillActive = await pollStatus();
        if (!stillActive) {
          setIsExporting(false);
          // Refresh downloads and project when export completes
          await fetchDownloads(projectId);
          fetchProject(projectId);

          // Auto-download the latest export file
          try {
            const downloadFiles = await projectsApi.files.listDownloads(projectId);
            const latest = downloadFiles
              .filter((f) => f.file_type === 'translation_workbook')
              .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0];
            if (latest) {
              // Small delay to ensure UI updates first
              setTimeout(() => {
                const blob = projectsApi.files.downloadFile(projectId, latest.id);
                blob.then((data) => {
                  const url = window.URL.createObjectURL(data);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = latest.filename;
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                  window.URL.revokeObjectURL(url);
                });
              }, 500);
            }
          } catch (err) {
            console.error('Auto-download failed:', err);
          }

          if (pollInterval) {
            clearInterval(pollInterval);
          }
        }
      }, 2000); // Poll every 2 seconds
    }

    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [isExporting, exportProgress.active, pollStatus, fetchDownloads, fetchProject, projectId]);

  // Check if there's already an active operation on mount
  useEffect(() => {
    pollStatus();
  }, [pollStatus]);

  const handleStartExport = async () => {
    if (isExporting || exportProgress.active) return;

    setLocalError(null);
    setIsExporting(true);
    setExportProgress({ active: true, message: 'Starting export...' });

    try {
      await startExport(projectId, currentProject?.config);
      // Polling will handle the rest
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Export failed. Please try again.';
      setLocalError(message);
      console.error('Export error:', err);
      setIsExporting(false);
      setExportProgress({ active: false });
    }
  };

  const handleRefreshDownloads = () => {
    fetchDownloads(projectId);
  };

  // Download file using blob (with auth)
  const handleDownload = async (fileId: string, filename: string) => {
    try {
      const blob = await projectsApi.files.downloadFile(projectId, fileId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed:', err);
      setLocalError('Download failed. Please try again.');
    }
  };

  // Get latest export file
  const latestExport = downloads
    .filter((f) => f.file_type === 'translation_workbook')
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0];

  const config = currentProject?.config;
  const hasFiles = files.length > 0;
  const hasConnection = config?.sf_connection?.connected;
  const canExport = hasFiles && !isExporting && !exportProgress.active;
  const isOperationActive = isExporting || exportProgress.active;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <FileSpreadsheet className="mx-auto h-12 w-12 text-sap-blue-500 mb-4" />
        <h3 className="text-lg font-medium text-gray-900">Ready to Generate Workbook</h3>
        <p className="mt-2 text-sm text-gray-600">
          Review your configuration and generate the translation Excel workbook.
        </p>
      </div>

      {/* Progress Indicator */}
      {isOperationActive && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
          <div className="flex items-center">
            <Loader2 className="w-5 h-5 text-yellow-600 animate-spin mr-3" />
            <div className="flex-1">
              <p className="text-sm font-medium text-yellow-800">Export in Progress</p>
              <p className="text-xs text-yellow-700 mt-1">
                {exportProgress.message || 'Processing...'}
              </p>
              {exportProgress.progress !== undefined && (
                <div className="mt-2 w-full bg-yellow-200 rounded-full h-2">
                  <div
                    className="bg-yellow-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${exportProgress.progress}%` }}
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Configuration Summary */}
      <div className="card bg-gray-50">
        <div className="card-header bg-white">
          <h4 className="text-sm font-medium text-gray-900">Configuration Summary</h4>
        </div>
        <div className="card-body space-y-3">
          {/* Files */}
          <div className="flex items-start">
            <div className="flex-shrink-0 mr-3 mt-0.5">
              {hasFiles ? (
                <CheckCircle className="w-5 h-5 text-green-500" />
              ) : (
                <AlertCircle className="w-5 h-5 text-orange-500" />
              )}
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">Data Model Files</p>
              <p className="text-xs text-gray-600">
                {files.length} file{files.length !== 1 ? 's' : ''} uploaded
              </p>
            </div>
          </div>

          {/* Connection */}
          <div className="flex items-start">
            <div className="flex-shrink-0 mr-3 mt-0.5">
              {hasConnection ? (
                <CheckCircle className="w-5 h-5 text-green-500" />
              ) : (
                <AlertCircle className="w-5 h-5 text-gray-400" />
              )}
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">SF Connection</p>
              <p className="text-xs text-gray-600">
                {hasConnection ? 'Connected' : 'Not connected (optional)'}
              </p>
            </div>
          </div>

          {/* Locales */}
          <div className="flex items-start">
            <div className="flex-shrink-0 mr-3 mt-0.5">
              <CheckCircle className="w-5 h-5 text-sap-blue-500" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">Languages</p>
              <p className="text-xs text-gray-600">
                {config?.locales?.length || 1} locale
                {(config?.locales?.length || 1) !== 1 ? 's' : ''} selected
                {config?.locales && config.locales.length > 0 && (
                  <span className="ml-1">
                    ({config.locales.slice(0, 3).join(', ')}
                    {config.locales.length > 3 && ', ...'})
                  </span>
                )}
              </p>
            </div>
          </div>

          {/* Export Options */}
          {hasConnection && (
            <div className="border-t pt-3 mt-3">
              <p className="text-xs font-medium text-gray-700 mb-2">Export Options:</p>
              <div className="space-y-1 text-xs text-gray-600">
                {/* Picklists */}
                {config?.export_mdf_picklists && <div>✓ MDF Picklists</div>}
                {config?.export_legacy_picklists && <div>✓ Legacy Picklists</div>}
                {/* Objects */}
                {config?.export_mdf_objects && <div>✓ MDF Objects</div>}
                {config?.export_fo_translations && <div>✓ Foundation Object Translations</div>}
                {/* Details */}
                {config?.ec_objects && config.ec_objects.length > 0 && (
                  <div className="text-gray-500">EC Objects: {config.ec_objects.length} selected</div>
                )}
                {config?.fo_translation_types && config.fo_translation_types.length > 0 && (
                  <div className="text-gray-500">FO Types: {config.fo_translation_types.length} selected</div>
                )}
                {config?.mdf_objects && config.mdf_objects.length > 0 && (
                  <div className="text-gray-500">Custom MDF: {config.mdf_objects.length} selected</div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Previous Export */}
      {latestExport && (
        <div className="card border-green-200 bg-green-50">
          <div className="card-body">
            <div className="flex items-start">
              <Download className="w-5 h-5 text-green-600 mr-3 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-green-900">Previous Export Available</p>
                <p className="text-xs text-green-700 mt-1">
                  {latestExport.filename} ({formatFileSize(latestExport.file_size)})
                </p>
                <p className="text-xs text-green-600 mt-1">
                  Generated {new Date(latestExport.created_at).toLocaleString()}
                </p>
                <button
                  onClick={() => handleDownload(latestExport.id, latestExport.filename)}
                  className="mt-2 text-xs text-green-700 hover:text-green-900 font-medium"
                >
                  → Download Previous Export
                </button>
              </div>
              <button
                onClick={handleRefreshDownloads}
                className="p-1 hover:bg-green-100 rounded"
                title="Refresh downloads"
              >
                <RefreshCw className="w-4 h-4 text-green-600" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {(error || localError) && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-start">
            <AlertCircle className="w-5 h-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-800">Export Error</p>
              <p className="text-sm text-red-600 mt-1">{localError || error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-between items-center pt-4 border-t">
        <div className="text-xs text-gray-500">
          {canExport ? (
            <>
              Export will process {files.length} uploaded file{files.length !== 1 ? 's' : ''}
            </>
          ) : isOperationActive ? (
            <span className="text-yellow-600">Export in progress...</span>
          ) : (
            <span className="text-orange-600">Upload at least one data model file to export</span>
          )}
        </div>

        <button
          onClick={handleStartExport}
          disabled={!canExport || isLoading}
          className={`btn-primary ${!canExport ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          {isOperationActive ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Exporting...
            </>
          ) : (
            <>
              <FileSpreadsheet className="w-4 h-4 mr-2" />
              Generate Workbook
            </>
          )}
        </button>
      </div>

      {/* Info Notice */}
      <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
        <p className="text-xs text-blue-800">
          <strong>Note:</strong> The export process may take several minutes depending on the number
          of files and selected options. Progress updates will appear above.
        </p>
      </div>
    </div>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}
