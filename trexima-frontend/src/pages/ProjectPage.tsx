/**
 * TREXIMA v2.0 - Project Page
 *
 * Main project workspace with separate EXPORT and IMPORT workflows.
 */

import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  ArrowRight,
  Upload,
  Globe,
  FileSpreadsheet,
  Loader2,
  CheckCircle,
  AlertCircle,
  Settings,
  ArrowDownToLine,
  ArrowUpFromLine,
  FileCheck,
  ListChecks,
  Play,
} from 'lucide-react';
import { useProjectStore } from '../store/projectStore';
import wsService from '../api/websocket';
import FileUploadZone from '../components/project/FileUploadZone';
import ConnectionConfig from '../components/project/ConnectionConfig';
import ProgressOverlay from '../components/project/ProgressOverlay';
import ExportConfig from '../components/project/ExportConfig';
import ExportSummary from '../components/project/ExportSummary';
import ImportSummary from '../components/project/ImportSummary';

// Workflow modes
type WorkflowMode = 'export' | 'import';

// Export workflow sections
type ExportSection = 'files' | 'connection' | 'config' | 'export';

// Import workflow sections
type ImportSection = 'upload' | 'consistency' | 'summary' | 'execute';

export default function ProjectPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const {
    currentProject,
    fetchProject,
    fetchDownloads,
    isLoading,
    error,
    activeOperation,
    clearProgress,
    updateProgress,
  } = useProjectStore();

  // Workflow state
  const [workflowMode, setWorkflowMode] = useState<WorkflowMode>('export');
  const [exportSection, setExportSection] = useState<ExportSection>('files');
  const [importSection, setImportSection] = useState<ImportSection>('upload');

  // Fetch project on mount
  useEffect(() => {
    if (projectId) {
      fetchProject(projectId);
      fetchDownloads(projectId);
    }
  }, [projectId, fetchProject, fetchDownloads]);

  // WebSocket subscription for real-time progress updates
  useEffect(() => {
    if (!projectId) return;

    wsService.connect().then(() => {
      wsService.subscribeToProject(projectId);
    }).catch((err) => {
      console.warn('WebSocket connection failed, progress updates may be delayed:', err);
    });

    const unsubProgress = wsService.onProgress(projectId, (progress) => {
      updateProgress(progress);
    });

    const unsubComplete = wsService.onComplete(projectId, () => {
      clearProgress();
      fetchProject(projectId);
      fetchDownloads(projectId);
    });

    const unsubError = wsService.onError(projectId, (error) => {
      console.error('Operation error:', error);
      clearProgress();
    });

    return () => {
      unsubProgress();
      unsubComplete();
      unsubError();
      wsService.unsubscribeFromProject(projectId);
    };
  }, [projectId, updateProgress, clearProgress, fetchProject, fetchDownloads]);

  if (isLoading || !currentProject) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-sap-blue-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="text-center py-12">
          <AlertCircle className="mx-auto h-12 w-12 text-red-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">Error loading project</h3>
          <p className="mt-2 text-sm text-gray-500">{error}</p>
          <Link to="/" className="mt-4 btn-secondary inline-flex">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  // Export workflow steps
  const exportSteps = [
    { id: 'files' as ExportSection, name: 'Data Models', icon: Upload, description: 'Upload XML files' },
    { id: 'connection' as ExportSection, name: 'SF Connection', icon: Globe, description: 'Connect to SF' },
    { id: 'config' as ExportSection, name: 'Configuration', icon: Settings, description: 'Select options' },
    { id: 'export' as ExportSection, name: 'Export', icon: FileSpreadsheet, description: 'Generate workbook' },
  ];

  // Import workflow steps
  const importSteps = [
    { id: 'upload' as ImportSection, name: 'Excel Upload', icon: Upload, description: 'Upload workbook' },
    { id: 'consistency' as ImportSection, name: 'Consistency Check', icon: FileCheck, description: 'Validate file' },
    { id: 'summary' as ImportSection, name: 'Summary', icon: ListChecks, description: 'Review changes' },
    { id: 'execute' as ImportSection, name: 'Execute', icon: Play, description: 'Run import' },
  ];

  const getExportStepStatus = (step: ExportSection): 'pending' | 'complete' | 'active' => {
    if (exportSection === step) return 'active';

    switch (step) {
      case 'files':
        return (currentProject.file_count || 0) > 0 ? 'complete' : 'pending';
      case 'connection':
        return currentProject.config?.sf_connection?.connected ? 'complete' : 'pending';
      case 'config':
        return currentProject.status !== 'draft' ? 'complete' : 'pending';
      case 'export':
        return currentProject.status === 'exported' || currentProject.status === 'imported'
          ? 'complete'
          : 'pending';
      default:
        return 'pending';
    }
  };

  const getImportStepStatus = (step: ImportSection): 'pending' | 'complete' | 'active' => {
    if (importSection === step) return 'active';
    // For now, all import steps are pending except active
    return 'pending';
  };

  // Export navigation helpers
  const exportIndex = exportSteps.findIndex((s) => s.id === exportSection);
  const prevExportStep = exportIndex > 0 ? exportSteps[exportIndex - 1] : null;
  const nextExportStep = exportIndex < exportSteps.length - 1 ? exportSteps[exportIndex + 1] : null;

  // Import navigation helpers
  const importIndex = importSteps.findIndex((s) => s.id === importSection);
  const prevImportStep = importIndex > 0 ? importSteps[importIndex - 1] : null;
  const nextImportStep = importIndex < importSteps.length - 1 ? importSteps[importIndex + 1] : null;

  const handleExportPrev = () => {
    if (prevExportStep) setExportSection(prevExportStep.id);
  };

  const handleExportNext = () => {
    if (nextExportStep) setExportSection(nextExportStep.id);
  };

  const handleImportPrev = () => {
    if (prevImportStep) setImportSection(prevImportStep.id);
  };

  const handleImportNext = () => {
    if (nextImportStep) setImportSection(nextImportStep.id);
  };

  const currentSteps = workflowMode === 'export' ? exportSteps : importSteps;
  const getStepStatus = workflowMode === 'export' ? getExportStepStatus : getImportStepStatus;

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-6">
        <Link
          to="/"
          className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-2"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to Dashboard
        </Link>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{currentProject.name}</h1>
            {currentProject.description && (
              <p className="mt-1 text-sm text-gray-500">{currentProject.description}</p>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <span
              className={`badge ${
                currentProject.status === 'exported' || currentProject.status === 'imported'
                  ? 'badge-success'
                  : currentProject.status === 'exporting' || currentProject.status === 'importing'
                  ? 'badge-warning'
                  : 'badge-gray'
              }`}
            >
              {currentProject.status.charAt(0).toUpperCase() + currentProject.status.slice(1)}
            </span>
          </div>
        </div>
      </div>

      {/* Progress Overlay */}
      <ProgressOverlay
        progress={activeOperation.progress}
        onCancel={
          activeOperation.type === 'export' && projectId
            ? () => clearProgress()
            : undefined
        }
        onClose={() => clearProgress()}
      />

      {/* Main Workflow Tabs */}
      <div className="mb-6">
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setWorkflowMode('export')}
            className={`flex items-center px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
              workflowMode === 'export'
                ? 'border-sap-blue-500 text-sap-blue-600 bg-sap-blue-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <ArrowDownToLine className="w-5 h-5 mr-2" />
            EXPORT to Excel
          </button>
          <button
            onClick={() => setWorkflowMode('import')}
            className={`flex items-center px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
              workflowMode === 'import'
                ? 'border-green-500 text-green-600 bg-green-50'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <ArrowUpFromLine className="w-5 h-5 mr-2" />
            IMPORT from Excel
          </button>
        </div>
      </div>

      {/* Workflow Steps - Sticky progress indicator */}
      <div className="sticky top-0 z-10 bg-gray-50 pt-2 pb-4 mb-6 -mx-4 px-4 sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8">
        <nav className="flex space-x-2 overflow-x-auto pb-2">
          {currentSteps.map((step, index) => {
            const status = getStepStatus(step.id as ExportSection & ImportSection);
            const Icon = step.icon;

            return (
              <div
                key={step.id}
                className={`flex-shrink-0 flex items-center px-4 py-3 rounded-lg border-2 ${
                  status === 'active'
                    ? workflowMode === 'export'
                      ? 'border-sap-blue-500 bg-sap-blue-50 text-sap-blue-700'
                      : 'border-green-500 bg-green-50 text-green-700'
                    : status === 'complete'
                    ? 'border-green-200 bg-green-50 text-green-700'
                    : 'border-gray-200 bg-white text-gray-500'
                }`}
              >
                <div className="flex items-center">
                  <span className="flex items-center justify-center w-8 h-8 rounded-full mr-3 bg-white border">
                    {status === 'complete' ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <span className="text-sm font-medium">{index + 1}</span>
                    )}
                  </span>
                  <div className="text-left">
                    <div className="flex items-center">
                      <Icon className="w-4 h-4 mr-1" />
                      <span className="text-sm font-medium">{step.name}</span>
                    </div>
                    <p className="text-xs opacity-75">{step.description}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </nav>
      </div>

      {/* Section Content */}
      <div className="card">
        <div className="card-body">
          {/* EXPORT Workflow Content */}
          {workflowMode === 'export' && (
            <>
              {exportSection === 'files' && projectId && (
                <FileUploadZone projectId={projectId} />
              )}
              {exportSection === 'connection' && projectId && (
                <ConnectionConfig projectId={projectId} />
              )}
              {exportSection === 'config' && projectId && (
                <ExportConfig projectId={projectId} />
              )}
              {exportSection === 'export' && projectId && (
                <ExportSummary projectId={projectId} />
              )}
            </>
          )}

          {/* IMPORT Workflow Content */}
          {workflowMode === 'import' && (
            <>
              {importSection === 'upload' && projectId && (
                <ImportSummary projectId={projectId} />
              )}
              {importSection === 'consistency' && projectId && (
                <div className="text-center py-12">
                  <FileCheck className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900">Consistency Check</h3>
                  <p className="mt-2 text-sm text-gray-500">
                    Upload an Excel file first to run the consistency check.
                  </p>
                </div>
              )}
              {importSection === 'summary' && projectId && (
                <div className="text-center py-12">
                  <ListChecks className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900">Import Summary</h3>
                  <p className="mt-2 text-sm text-gray-500">
                    Complete the consistency check to see the import summary.
                  </p>
                </div>
              )}
              {importSection === 'execute' && projectId && (
                <div className="text-center py-12">
                  <Play className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900">Execute Import</h3>
                  <p className="mt-2 text-sm text-gray-500">
                    Review the summary before executing the import.
                  </p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Bottom Navigation */}
        <div className="flex justify-between items-center border-t border-gray-200 px-6 py-4 bg-gray-50">
          {workflowMode === 'export' ? (
            <>
              <button
                onClick={handleExportPrev}
                disabled={!prevExportStep}
                className={`inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  prevExportStep
                    ? 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
                    : 'text-gray-400 bg-gray-100 border border-gray-200 cursor-not-allowed'
                }`}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                {prevExportStep ? prevExportStep.name : 'Back'}
              </button>

              <button
                onClick={handleExportNext}
                disabled={!nextExportStep}
                className={`inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  nextExportStep
                    ? 'text-white bg-sap-blue-600 hover:bg-sap-blue-700'
                    : 'text-gray-400 bg-gray-100 border border-gray-200 cursor-not-allowed'
                }`}
              >
                {nextExportStep ? nextExportStep.name : 'Done'}
                <ArrowRight className="w-4 h-4 ml-2" />
              </button>
            </>
          ) : (
            <>
              <button
                onClick={handleImportPrev}
                disabled={!prevImportStep}
                className={`inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  prevImportStep
                    ? 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
                    : 'text-gray-400 bg-gray-100 border border-gray-200 cursor-not-allowed'
                }`}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                {prevImportStep ? prevImportStep.name : 'Back'}
              </button>

              <button
                onClick={handleImportNext}
                disabled={!nextImportStep}
                className={`inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  nextImportStep
                    ? 'text-white bg-green-600 hover:bg-green-700'
                    : 'text-gray-400 bg-gray-100 border border-gray-200 cursor-not-allowed'
                }`}
              >
                {nextImportStep ? nextImportStep.name : 'Done'}
                <ArrowRight className="w-4 h-4 ml-2" />
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
