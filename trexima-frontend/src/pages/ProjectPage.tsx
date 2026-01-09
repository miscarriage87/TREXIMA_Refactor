/**
 * TREXIMA v4.0 - Project Page
 *
 * Main project workspace with workflow sections.
 */

import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Upload,
  Globe,
  FileSpreadsheet,
  Loader2,
  CheckCircle,
  AlertCircle,
  Settings,
  ArrowUpCircle,
} from 'lucide-react';
import { useProjectStore } from '../store/projectStore';
import wsService from '../api/websocket';
import FileUploadZone from '../components/project/FileUploadZone';
import ConnectionConfig from '../components/project/ConnectionConfig';
import ProgressOverlay from '../components/project/ProgressOverlay';
import ExportConfig from '../components/project/ExportConfig';
import ExportSummary from '../components/project/ExportSummary';
import ImportSummary from '../components/project/ImportSummary';

// Workflow section type
type Section = 'files' | 'connection' | 'config' | 'export' | 'import';

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

  const [activeSection, setActiveSection] = useState<Section>('files');

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

    // Connect and subscribe to project updates
    wsService.connect().then(() => {
      wsService.subscribeToProject(projectId);
    }).catch((err) => {
      console.warn('WebSocket connection failed, progress updates may be delayed:', err);
    });

    // Register callbacks for progress updates
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

    // Cleanup on unmount
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

  const sections = [
    { id: 'files' as Section, name: 'Data Models', icon: Upload, description: 'Upload XML files' },
    { id: 'connection' as Section, name: 'SF Connection', icon: Globe, description: 'Connect to SF' },
    { id: 'config' as Section, name: 'Configuration', icon: Settings, description: 'Select options' },
    { id: 'export' as Section, name: 'Export', icon: FileSpreadsheet, description: 'Generate workbook' },
    { id: 'import' as Section, name: 'Import', icon: ArrowUpCircle, description: 'Import translations' },
  ];

  const getSectionStatus = (section: Section): 'pending' | 'complete' | 'active' => {
    if (activeSection === section) return 'active';

    switch (section) {
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
      case 'import':
        return currentProject.status === 'imported' ? 'complete' : 'pending';
      default:
        return 'pending';
    }
  };

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
            ? () => {
                // Handle cancel
                clearProgress();
              }
            : undefined
        }
        onClose={() => clearProgress()}
      />

      {/* Workflow Steps */}
      <div className="mb-6">
        <nav className="flex space-x-2 overflow-x-auto pb-2">
          {sections.map((section, index) => {
            const status = getSectionStatus(section.id);
            const Icon = section.icon;

            return (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`flex-shrink-0 flex items-center px-4 py-3 rounded-lg border-2 transition-colors ${
                  status === 'active'
                    ? 'border-sap-blue-500 bg-sap-blue-50 text-sap-blue-700'
                    : status === 'complete'
                    ? 'border-green-200 bg-green-50 text-green-700'
                    : 'border-gray-200 bg-white text-gray-500 hover:border-gray-300'
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
                      <span className="text-sm font-medium">{section.name}</span>
                    </div>
                    <p className="text-xs opacity-75">{section.description}</p>
                  </div>
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Section Content */}
      <div className="card">
        <div className="card-body">
          {activeSection === 'files' && projectId && (
            <FileUploadZone projectId={projectId} />
          )}

          {activeSection === 'connection' && projectId && (
            <ConnectionConfig projectId={projectId} />
          )}

          {activeSection === 'config' && projectId && (
            <ExportConfig projectId={projectId} />
          )}

          {activeSection === 'export' && projectId && (
            <ExportSummary projectId={projectId} />
          )}

          {activeSection === 'import' && projectId && (
            <ImportSummary projectId={projectId} />
          )}
        </div>
      </div>
    </div>
  );
}
