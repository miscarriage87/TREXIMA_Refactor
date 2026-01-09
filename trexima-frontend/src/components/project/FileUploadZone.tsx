/**
 * TREXIMA v4.0 - File Upload Zone Component
 *
 * Drag-and-drop file upload with file type detection.
 */

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, AlertCircle, CheckCircle } from 'lucide-react';
import { useProjectStore } from '../../store/projectStore';
import type { FileType } from '../../types';

interface FileUploadZoneProps {
  projectId: string;
}

export default function FileUploadZone({ projectId }: FileUploadZoneProps) {
  const { files, uploadFile, deleteFile, isSaving, error, clearError } = useProjectStore();
  const [uploadErrors, setUploadErrors] = useState<Record<string, string>>({});

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      clearError();
      setUploadErrors({});

      for (const file of acceptedFiles) {
        try {
          // Auto-detect file type from filename
          const fileType = detectFileType(file.name);
          await uploadFile(projectId, file, fileType);
        } catch (err) {
          setUploadErrors((prev) => ({
            ...prev,
            [file.name]: err instanceof Error ? err.message : 'Upload failed',
          }));
        }
      }
    },
    [projectId, uploadFile, clearError]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/xml': ['.xml'],
      'application/xml': ['.xml'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/csv': ['.csv'],
    },
    maxSize: 100 * 1024 * 1024, // 100MB
    multiple: true,
  });

  const handleDelete = async (fileId: string) => {
    try {
      await deleteFile(projectId, fileId);
      clearError();
    } catch {
      // Error handled by store
    }
  };

  const getFileTypeBadge = (fileType: FileType | string) => {
    const badges: Record<string, { label: string; class: string }> = {
      sdm: { label: 'SDM', class: 'bg-blue-100 text-blue-800' },
      cdm: { label: 'CDM', class: 'bg-purple-100 text-purple-800' },
      ec_sdm: { label: 'EC-SDM', class: 'bg-green-100 text-green-800' },
      ec_cdm: { label: 'EC-CDM', class: 'bg-yellow-100 text-yellow-800' },
      picklist: { label: 'Picklist', class: 'bg-orange-100 text-orange-800' },
      unknown: { label: 'Unknown', class: 'bg-gray-100 text-gray-800' },
    };
    return badges[fileType] || badges.unknown;
  };

  return (
    <div className="space-y-4">
      {/* Upload Zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-sap-blue-500 bg-sap-blue-50'
            : 'border-gray-300 hover:border-gray-400 bg-gray-50'
        }`}
      >
        <input {...getInputProps()} />
        <Upload
          className={`mx-auto h-12 w-12 mb-4 ${
            isDragActive ? 'text-sap-blue-500' : 'text-gray-400'
          }`}
        />
        {isDragActive ? (
          <p className="text-sm text-sap-blue-600 font-medium">Drop files here...</p>
        ) : (
          <>
            <p className="text-sm text-gray-600 mb-1">
              Drag and drop XML files here, or click to browse
            </p>
            <p className="text-xs text-gray-400">
              Supported: .xml, .xlsx, .csv (max 100MB per file)
            </p>
          </>
        )}
      </div>

      {/* Error Messages */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md flex items-start">
          <AlertCircle className="w-5 h-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-red-600">{error}</p>
          </div>
          <button onClick={clearError} className="text-red-400 hover:text-red-600">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {Object.keys(uploadErrors).length > 0 && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm font-medium text-red-800 mb-2">Upload Errors:</p>
          <ul className="text-xs text-red-600 space-y-1">
            {Object.entries(uploadErrors).map(([filename, error]) => (
              <li key={filename}>
                <strong>{filename}:</strong> {error}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-gray-700">Uploaded Files ({files.length})</h3>
          <div className="space-y-2">
            {files.map((file) => {
              const badge = getFileTypeBadge(file.file_type);
              return (
                <div
                  key={file.id}
                  className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-md hover:shadow-sm transition-shadow"
                >
                  <div className="flex items-center min-w-0 flex-1">
                    <FileText className="w-5 h-5 text-gray-400 mr-3 flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {file.original_filename}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(file.file_size)} · Uploaded{' '}
                        {new Date(file.uploaded_at).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    <span className={`badge ${badge.class}`}>{badge.label}</span>
                    <button
                      onClick={() => handleDelete(file.id)}
                      disabled={isSaving}
                      className="p-1 text-gray-400 hover:text-red-600 disabled:opacity-50"
                      title="Delete file"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* File Type Legend */}
      <div className="p-3 bg-gray-50 border border-gray-200 rounded-md">
        <p className="text-xs font-medium text-gray-700 mb-2">File Types:</p>
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="badge bg-blue-100 text-blue-800">SDM</span> Standard Data Model
          <span className="badge bg-purple-100 text-purple-800">CDM</span> Corporate Data Model
          <span className="badge bg-green-100 text-green-800">EC-SDM</span> EC Standard
          <span className="badge bg-yellow-100 text-yellow-800">EC-CDM</span> EC Corporate
          <span className="badge bg-orange-100 text-orange-800">Picklist</span> Picklist Export
        </div>
      </div>

      {/* Success State */}
      {files.length > 0 && !error && (
        <div className="flex items-center text-sm text-green-600">
          <CheckCircle className="w-4 h-4 mr-2" />
          {files.length} file{files.length !== 1 ? 's' : ''} ready for processing
        </div>
      )}
    </div>
  );
}

// Helper functions
function detectFileType(filename: string): FileType | undefined {
  const lower = filename.toLowerCase();

  if (lower.includes('ec') && lower.includes('sdm')) return 'ec_sdm';
  if (lower.includes('ec') && lower.includes('cdm')) return 'ec_cdm';
  if (lower.includes('sdm')) return 'sdm';
  if (lower.includes('cdm')) return 'cdm';
  if (lower.includes('picklist') || lower.includes('picklists')) return 'picklist';

  return undefined; // Let backend auto-detect
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}
