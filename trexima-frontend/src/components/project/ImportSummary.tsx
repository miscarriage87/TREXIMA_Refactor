/**
 * TREXIMA v2.0 - Import Summary Component
 *
 * Workbook upload, validation, worksheet selection, and import execution.
 */

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Upload,
  FileSpreadsheet,
  CheckCircle,
  AlertCircle,
  Loader2,
  X,
  ArrowUpCircle,
} from 'lucide-react';
import { useProjectStore } from '../../store/projectStore';

interface ImportSummaryProps {
  projectId: string;
}

export default function ImportSummary({ projectId }: ImportSummaryProps) {
  const {
    currentProject,
    validateWorkbook,
    startImport,
    isLoading,
    error,
    clearError,
  } = useProjectStore();

  const [workbookFile, setWorkbookFile] = useState<File | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    filename: string;
    sheets: {
      all: string[];
      datamodel: string[];
      pm_templates: string[];
      gm_templates: string[];
      other: string[];
    };
    total_sheets: number;
    error?: string;
  } | null>(null);

  const [selectedWorksheets, setSelectedWorksheets] = useState<string[]>([]);
  const [pushToAPI, setPushToAPI] = useState(false);
  const [isImporting, setIsImporting] = useState(false);

  const hasConnection = currentProject?.config?.sf_connection?.connected;

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;

      const file = acceptedFiles[0];
      setWorkbookFile(file);
      setValidationResult(null);
      setSelectedWorksheets([]);
      clearError();

      // Auto-validate
      setIsValidating(true);
      try {
        const result = await validateWorkbook(projectId, file);
        setValidationResult(result);

        // Auto-select all data model sheets
        if (result.valid && result.sheets.datamodel.length > 0) {
          setSelectedWorksheets(result.sheets.datamodel);
        }
      } catch (err) {
        console.error('Validation failed:', err);
      } finally {
        setIsValidating(false);
      }
    },
    [projectId, validateWorkbook, clearError]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    maxSize: 100 * 1024 * 1024, // 100MB
    multiple: false,
  });

  const handleWorksheetToggle = (sheet: string) => {
    setSelectedWorksheets((prev) =>
      prev.includes(sheet) ? prev.filter((s) => s !== sheet) : [...prev, sheet]
    );
  };

  const handleSelectAllDatamodel = () => {
    if (validationResult) {
      setSelectedWorksheets(validationResult.sheets.datamodel);
    }
  };

  const handleSelectAll = () => {
    if (validationResult) {
      setSelectedWorksheets(validationResult.sheets.all);
    }
  };

  const handleDeselectAll = () => {
    setSelectedWorksheets([]);
  };

  const handleStartImport = async () => {
    if (!workbookFile || selectedWorksheets.length === 0) return;

    setIsImporting(true);
    clearError();

    try {
      await startImport(projectId, workbookFile, {
        worksheets: selectedWorksheets,
        push_to_api: pushToAPI,
      });
    } catch (err) {
      console.error('Import failed:', err);
    } finally {
      setIsImporting(false);
    }
  };

  const handleClearWorkbook = () => {
    setWorkbookFile(null);
    setValidationResult(null);
    setSelectedWorksheets([]);
    clearError();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <ArrowUpCircle className="mx-auto h-12 w-12 text-sap-blue-500 mb-4" />
        <h3 className="text-lg font-medium text-gray-900">Import Translations</h3>
        <p className="mt-2 text-sm text-gray-600">
          Upload a translated workbook to import translations back into the system.
        </p>
      </div>

      {/* Upload Zone */}
      {!workbookFile ? (
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
            <p className="text-sm text-sap-blue-600 font-medium">Drop workbook here...</p>
          ) : (
            <>
              <p className="text-sm text-gray-600 mb-1">
                Drag and drop Excel workbook here, or click to browse
              </p>
              <p className="text-xs text-gray-400">Supported: .xlsx (max 100MB)</p>
            </>
          )}
        </div>
      ) : (
        <>
          {/* Workbook Info */}
          <div className="card">
            <div className="card-body">
              <div className="flex items-start justify-between">
                <div className="flex items-start flex-1">
                  <FileSpreadsheet className="w-8 h-8 text-sap-blue-500 mr-3 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {workbookFile.name}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {(workbookFile.size / (1024 * 1024)).toFixed(2)} MB
                    </p>

                    {/* Validation Status */}
                    {isValidating && (
                      <div className="mt-3 flex items-center text-sm text-sap-blue-600">
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Validating workbook structure...
                      </div>
                    )}

                    {validationResult && (
                      <div className="mt-3">
                        {validationResult.valid ? (
                          <div className="flex items-start text-sm text-green-600">
                            <CheckCircle className="w-4 h-4 mr-2 flex-shrink-0 mt-0.5" />
                            <div>
                              <p className="font-medium">Workbook validated successfully</p>
                              <p className="text-xs mt-1">
                                {validationResult.total_sheets} worksheet
                                {validationResult.total_sheets !== 1 ? 's' : ''} found
                              </p>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-start text-sm text-red-600">
                            <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0 mt-0.5" />
                            <div>
                              <p className="font-medium">Validation failed</p>
                              <p className="text-xs mt-1">{validationResult.error}</p>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                <button
                  onClick={handleClearWorkbook}
                  className="ml-4 text-gray-400 hover:text-gray-600"
                  title="Remove workbook"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Worksheet Selection */}
          {validationResult?.valid && (
            <div className="card">
              <div className="card-header flex items-center justify-between">
                <h4 className="text-sm font-medium text-gray-900">Select Worksheets to Import</h4>
                <div className="flex space-x-2 text-xs">
                  <button
                    onClick={handleSelectAllDatamodel}
                    className="text-sap-blue-600 hover:text-sap-blue-800"
                  >
                    Data Models
                  </button>
                  <span className="text-gray-300">|</span>
                  <button
                    onClick={handleSelectAll}
                    className="text-sap-blue-600 hover:text-sap-blue-800"
                  >
                    All
                  </button>
                  <span className="text-gray-300">|</span>
                  <button
                    onClick={handleDeselectAll}
                    className="text-sap-blue-600 hover:text-sap-blue-800"
                  >
                    None
                  </button>
                </div>
              </div>
              <div className="card-body">
                <p className="text-xs text-gray-500 mb-4">
                  Selected: {selectedWorksheets.length} worksheet
                  {selectedWorksheets.length !== 1 ? 's' : ''}
                </p>

                {/* Data Model Sheets */}
                {validationResult.sheets.datamodel.length > 0 && (
                  <div className="mb-4">
                    <h5 className="text-xs font-semibold text-gray-700 mb-2">
                      Data Model Translations ({validationResult.sheets.datamodel.length})
                    </h5>
                    <div className="space-y-1">
                      {validationResult.sheets.datamodel.map((sheet) => (
                        <label
                          key={sheet}
                          className="flex items-center p-2 rounded border cursor-pointer transition-colors hover:bg-gray-50"
                        >
                          <input
                            type="checkbox"
                            checked={selectedWorksheets.includes(sheet)}
                            onChange={() => handleWorksheetToggle(sheet)}
                            className="mr-2"
                          />
                          <span className="text-xs">{sheet}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}

                {/* PM Templates */}
                {validationResult.sheets.pm_templates.length > 0 && (
                  <div className="mb-4">
                    <h5 className="text-xs font-semibold text-gray-700 mb-2">
                      Picklist & MDF Templates ({validationResult.sheets.pm_templates.length})
                    </h5>
                    <div className="space-y-1">
                      {validationResult.sheets.pm_templates.map((sheet) => (
                        <label
                          key={sheet}
                          className="flex items-center p-2 rounded border cursor-pointer transition-colors hover:bg-gray-50"
                        >
                          <input
                            type="checkbox"
                            checked={selectedWorksheets.includes(sheet)}
                            onChange={() => handleWorksheetToggle(sheet)}
                            className="mr-2"
                          />
                          <span className="text-xs">{sheet}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}

                {/* GM Templates */}
                {validationResult.sheets.gm_templates.length > 0 && (
                  <div className="mb-4">
                    <h5 className="text-xs font-semibold text-gray-700 mb-2">
                      Generic Object Templates ({validationResult.sheets.gm_templates.length})
                    </h5>
                    <div className="space-y-1">
                      {validationResult.sheets.gm_templates.map((sheet) => (
                        <label
                          key={sheet}
                          className="flex items-center p-2 rounded border cursor-pointer transition-colors hover:bg-gray-50"
                        >
                          <input
                            type="checkbox"
                            checked={selectedWorksheets.includes(sheet)}
                            onChange={() => handleWorksheetToggle(sheet)}
                            className="mr-2"
                          />
                          <span className="text-xs">{sheet}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}

                {/* Other Sheets */}
                {validationResult.sheets.other.length > 0 && (
                  <div>
                    <h5 className="text-xs font-semibold text-gray-700 mb-2">
                      Other Sheets ({validationResult.sheets.other.length})
                    </h5>
                    <div className="space-y-1">
                      {validationResult.sheets.other.map((sheet) => (
                        <label
                          key={sheet}
                          className="flex items-center p-2 rounded border cursor-pointer transition-colors hover:bg-gray-50"
                        >
                          <input
                            type="checkbox"
                            checked={selectedWorksheets.includes(sheet)}
                            onChange={() => handleWorksheetToggle(sheet)}
                            className="mr-2"
                          />
                          <span className="text-xs text-gray-500">{sheet}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Import Options */}
          {validationResult?.valid && selectedWorksheets.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h4 className="text-sm font-medium text-gray-900">Import Options</h4>
              </div>
              <div className="card-body">
                <label className="flex items-start cursor-pointer">
                  <input
                    type="checkbox"
                    checked={pushToAPI}
                    onChange={(e) => setPushToAPI(e.target.checked)}
                    disabled={!hasConnection}
                    className="mt-1 mr-3"
                  />
                  <div className="flex-1">
                    <span className="text-sm font-medium text-gray-900">
                      Push to SuccessFactors API
                    </span>
                    <p className="text-xs text-gray-500 mt-1">
                      {hasConnection
                        ? 'Automatically push translated values to SuccessFactors via OData API'
                        : 'Connect to SuccessFactors first to enable this option'}
                    </p>
                  </div>
                </label>
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Import Actions */}
          {validationResult?.valid && (
            <div className="flex justify-between items-center pt-4 border-t">
              <div className="text-xs text-gray-500">
                {selectedWorksheets.length > 0 ? (
                  <>
                    Import will process {selectedWorksheets.length} worksheet
                    {selectedWorksheets.length !== 1 ? 's' : ''}
                    {pushToAPI && hasConnection && ' and push to SuccessFactors'}
                  </>
                ) : (
                  <span className="text-orange-600">Select at least one worksheet to import</span>
                )}
              </div>

              <button
                onClick={handleStartImport}
                disabled={selectedWorksheets.length === 0 || isImporting || isLoading}
                className="btn-primary"
              >
                {isImporting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Importing...
                  </>
                ) : (
                  <>
                    <ArrowUpCircle className="w-4 h-4 mr-2" />
                    Start Import
                  </>
                )}
              </button>
            </div>
          )}

          {/* Info Notice */}
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
            <p className="text-xs text-blue-800">
              <strong>Note:</strong> The import process validates translated values and can
              optionally push them to SuccessFactors. You'll receive real-time progress updates.
              Generated output files will be available for download after completion.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
