/**
 * TREXIMA v4.0 - Export Configuration Component
 *
 * Configure export options with DYNAMIC data fetched from the connected SF instance.
 * Displays real entities, picklists, and locales from the API.
 */

import { useEffect, useState } from 'react';
import {
  Settings,
  Languages,
  CheckCircle,
  Loader2,
  Save,
  RefreshCw,
  Database,
  List,
  Globe,
  AlertCircle,
} from 'lucide-react';
import { useProjectStore } from '../../store/projectStore';
import projectsApi from '../../api/projects';

interface ExportConfigProps {
  projectId: string;
}

interface SFData {
  entities: {
    total: number;
    mdf_objects: string[];
    foundation_objects: string[];
    ec_objects: string[];
  };
  picklists: {
    mdf_count: number;
    legacy_count: number;
    migrated_legacy_count: number;
  };
  locales: string[];
}

export default function ExportConfig({ projectId }: ExportConfigProps) {
  const { currentProject, updateConfig, isSaving } = useProjectStore();

  // SF dynamic data
  const [sfData, setSfData] = useState<SFData | null>(null);
  const [isLoadingSF, setIsLoadingSF] = useState(false);
  const [sfError, setSfError] = useState<string | null>(null);

  // Export options
  const [selectedLocales, setSelectedLocales] = useState<string[]>(['en_US']);
  const [exportPicklists, setExportPicklists] = useState(false);
  const [exportMDFObjects, setExportMDFObjects] = useState(false);
  const [exportFOTranslations, setExportFOTranslations] = useState(false);

  // Object selections
  const [selectedECObjects, setSelectedECObjects] = useState<string[]>([]);
  const [selectedFOObjects, setSelectedFOObjects] = useState<string[]>([]);
  const [selectedMDFObjects, setSelectedMDFObjects] = useState<string[]>([]);

  const [saveSuccess, setSaveSuccess] = useState(false);

  const hasConnection = currentProject?.config?.sf_connection?.connected;

  // Load config from project
  useEffect(() => {
    if (currentProject?.config) {
      const config = currentProject.config;
      if (config.locales) setSelectedLocales(config.locales);
      if (config.export_picklists !== undefined) setExportPicklists(config.export_picklists);
      if (config.export_mdf_objects !== undefined) setExportMDFObjects(config.export_mdf_objects);
      if (config.export_fo_translations !== undefined)
        setExportFOTranslations(config.export_fo_translations);
      if (config.ec_objects) setSelectedECObjects(config.ec_objects);
      if (config.fo_objects) setSelectedFOObjects(config.fo_objects);
    }
  }, [currentProject]);

  // Fetch SF data when connected
  const fetchSFData = async () => {
    if (!hasConnection) return;

    setIsLoadingSF(true);
    setSfError(null);
    try {
      const response = await projectsApi.connection.getSFObjects(projectId);
      if (response.success && response.data) {
        setSfData(response.data);
        // If we got locales from SF and current selection is just default, use SF locales
        if (response.data.locales.length > 0 && selectedLocales.length === 1) {
          // Keep en_US first, add others
          const newLocales = ['en_US', ...response.data.locales.filter((l) => l !== 'en_US')];
          setSelectedLocales(newLocales.slice(0, 5)); // Select first 5 by default
        }
      } else {
        setSfError(response.error || 'Failed to fetch SF data');
      }
    } catch (error) {
      setSfError(error instanceof Error ? error.message : 'Failed to fetch SF data');
    } finally {
      setIsLoadingSF(false);
    }
  };

  // Fetch SF data on mount if connected
  useEffect(() => {
    if (hasConnection) {
      fetchSFData();
    }
  }, [hasConnection, projectId]);

  const handleLocaleToggle = (locale: string) => {
    if (locale === 'en_US') return; // en_US is mandatory
    setSelectedLocales((prev) =>
      prev.includes(locale) ? prev.filter((l) => l !== locale) : [...prev, locale]
    );
  };

  const handleSelectAllLocales = () => {
    if (sfData?.locales) {
      setSelectedLocales(['en_US', ...sfData.locales.filter((l) => l !== 'en_US')]);
    }
  };

  const handleDeselectAllLocales = () => {
    setSelectedLocales(['en_US']);
  };

  const handleObjectToggle = (
    objectId: string,
    setFn: React.Dispatch<React.SetStateAction<string[]>>
  ) => {
    setFn((prev) =>
      prev.includes(objectId) ? prev.filter((id) => id !== objectId) : [...prev, objectId]
    );
  };

  const handleSave = async () => {
    setSaveSuccess(false);
    try {
      await updateConfig(projectId, {
        locales: selectedLocales,
        export_picklists: exportPicklists,
        export_mdf_objects: exportMDFObjects,
        export_fo_translations: exportFOTranslations,
        ec_objects: exportMDFObjects ? [...selectedECObjects, ...selectedMDFObjects] : [],
        fo_objects: exportFOTranslations ? selectedFOObjects : [],
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to save config:', error);
    }
  };

  // Available locales - from SF or fallback to config
  const availableLocales: string[] =
    sfData?.locales || currentProject?.config?.locales || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <Settings className="mx-auto h-12 w-12 text-sap-blue-500 mb-4" />
        <h3 className="text-lg font-medium text-gray-900">Export Configuration</h3>
        <p className="mt-2 text-sm text-gray-600">
          {hasConnection
            ? 'Configure export options using live data from your SF instance.'
            : 'Connect to SuccessFactors to enable dynamic data fetching.'}
        </p>
      </div>

      {/* SF Connection Status / Data Fetch */}
      {hasConnection && (
        <div className="card border-sap-blue-200 bg-sap-blue-50">
          <div className="card-body">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <Database className="w-5 h-5 text-sap-blue-600 mr-2" />
                <div>
                  <p className="text-sm font-medium text-sap-blue-900">SF Instance Connected</p>
                  {sfData && (
                    <p className="text-xs text-sap-blue-700">
                      {sfData.entities.total} entities • {sfData.picklists.mdf_count} MDF picklists •{' '}
                      {sfData.picklists.legacy_count} legacy picklists • {sfData.locales.length}{' '}
                      locales
                    </p>
                  )}
                </div>
              </div>
              <button
                onClick={fetchSFData}
                disabled={isLoadingSF}
                className="p-2 text-sap-blue-600 hover:bg-sap-blue-100 rounded"
                title="Refresh SF data"
              >
                <RefreshCw className={`w-4 h-4 ${isLoadingSF ? 'animate-spin' : ''}`} />
              </button>
            </div>
            {sfError && (
              <p className="mt-2 text-xs text-red-600 flex items-center">
                <AlertCircle className="w-3 h-3 mr-1" />
                {sfError}
              </p>
            )}
          </div>
        </div>
      )}

      {isLoadingSF ? (
        <div className="flex justify-center py-8">
          <Loader2 className="w-8 h-8 animate-spin text-sap-blue-500" />
          <span className="ml-2 text-gray-600">Loading SF data...</span>
        </div>
      ) : (
        <>
          {/* Language Selection */}
          <div className="card">
            <div className="card-header flex items-center justify-between">
              <div className="flex items-center">
                <Languages className="w-5 h-5 mr-2 text-sap-blue-500" />
                <h4 className="text-sm font-medium text-gray-900">
                  Languages
                  {sfData && (
                    <span className="ml-2 text-xs text-gray-500 font-normal">
                      (from SF instance)
                    </span>
                  )}
                </h4>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={handleSelectAllLocales}
                  className="text-xs text-sap-blue-600 hover:text-sap-blue-800"
                >
                  Select All
                </button>
                <span className="text-gray-300">|</span>
                <button
                  onClick={handleDeselectAllLocales}
                  className="text-xs text-sap-blue-600 hover:text-sap-blue-800"
                >
                  Deselect All
                </button>
              </div>
            </div>
            <div className="card-body">
              <p className="text-xs text-gray-500 mb-4">
                Selected: {selectedLocales.length} language{selectedLocales.length !== 1 ? 's' : ''}
                {availableLocales.length > 0 && ` / ${availableLocales.length} available`}
              </p>

              {availableLocales.length > 0 ? (
                <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2">
                  {/* Always show en_US first */}
                  <label className="flex items-center p-2 rounded border border-sap-blue-500 bg-sap-blue-50 opacity-75">
                    <input
                      type="checkbox"
                      checked={true}
                      disabled={true}
                      className="mr-2"
                    />
                    <span className="text-xs">en_US (Required)</span>
                  </label>
                  {availableLocales
                    .filter((l) => l !== 'en_US')
                    .sort()
                    .map((locale) => (
                      <label
                        key={locale}
                        className={`flex items-center p-2 rounded border cursor-pointer transition-colors ${
                          selectedLocales.includes(locale)
                            ? 'border-sap-blue-500 bg-sap-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedLocales.includes(locale)}
                          onChange={() => handleLocaleToggle(locale)}
                          className="mr-2"
                        />
                        <span className="text-xs">{locale}</span>
                      </label>
                    ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 italic">
                  Connect to SF to see available locales
                </p>
              )}
            </div>
          </div>

          {/* Export Options */}
          <div className="card">
            <div className="card-header">
              <h4 className="text-sm font-medium text-gray-900">Export Options</h4>
              {!hasConnection && (
                <p className="text-xs text-gray-500 mt-1">
                  Connect to SuccessFactors API to enable these options
                </p>
              )}
            </div>
            <div className="card-body space-y-4">
              {/* Picklists */}
              <label className="flex items-start cursor-pointer">
                <input
                  type="checkbox"
                  checked={exportPicklists}
                  onChange={(e) => setExportPicklists(e.target.checked)}
                  disabled={!hasConnection}
                  className="mt-1 mr-3"
                />
                <div className="flex-1">
                  <div className="flex items-center">
                    <List className="w-4 h-4 mr-1 text-gray-600" />
                    <span className="text-sm font-medium text-gray-900">Export Picklists</span>
                    {sfData && (
                      <span className="ml-2 text-xs bg-gray-100 px-2 py-0.5 rounded">
                        {sfData.picklists.mdf_count} MDF + {sfData.picklists.legacy_count} Legacy
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Export all picklist values and their translations
                  </p>
                </div>
              </label>

              {/* MDF/EC Objects */}
              <label className="flex items-start cursor-pointer">
                <input
                  type="checkbox"
                  checked={exportMDFObjects}
                  onChange={(e) => setExportMDFObjects(e.target.checked)}
                  disabled={!hasConnection}
                  className="mt-1 mr-3"
                />
                <div className="flex-1">
                  <div className="flex items-center">
                    <Database className="w-4 h-4 mr-1 text-gray-600" />
                    <span className="text-sm font-medium text-gray-900">Export EC/MDF Objects</span>
                    {sfData && (
                      <span className="ml-2 text-xs bg-gray-100 px-2 py-0.5 rounded">
                        {sfData.entities.ec_objects.length} EC +{' '}
                        {sfData.entities.mdf_objects.length} MDF available
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Export Employee Central and MDF object translations
                  </p>
                </div>
              </label>

              {/* EC Objects Selection */}
              {exportMDFObjects && sfData && (
                <div className="ml-6 p-3 bg-gray-50 rounded-md space-y-3">
                  {/* EC Objects */}
                  {sfData.entities.ec_objects.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-gray-700 mb-2">
                        EC Objects ({selectedECObjects.length}/{sfData.entities.ec_objects.length}{' '}
                        selected):
                      </p>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-1 max-h-40 overflow-y-auto">
                        {sfData.entities.ec_objects.slice(0, 50).map((obj) => (
                          <label
                            key={obj}
                            className="flex items-center text-xs cursor-pointer p-1 hover:bg-gray-100 rounded"
                          >
                            <input
                              type="checkbox"
                              checked={selectedECObjects.includes(obj)}
                              onChange={() => handleObjectToggle(obj, setSelectedECObjects)}
                              className="mr-1"
                            />
                            <span className="truncate">{obj}</span>
                          </label>
                        ))}
                      </div>
                      {sfData.entities.ec_objects.length > 50 && (
                        <p className="text-xs text-gray-500 mt-1">
                          ... and {sfData.entities.ec_objects.length - 50} more
                        </p>
                      )}
                    </div>
                  )}

                  {/* MDF Objects */}
                  {sfData.entities.mdf_objects.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-gray-700 mb-2">
                        MDF Objects ({selectedMDFObjects.length}/{sfData.entities.mdf_objects.length}{' '}
                        selected):
                      </p>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-1 max-h-40 overflow-y-auto">
                        {sfData.entities.mdf_objects.slice(0, 50).map((obj) => (
                          <label
                            key={obj}
                            className="flex items-center text-xs cursor-pointer p-1 hover:bg-gray-100 rounded"
                          >
                            <input
                              type="checkbox"
                              checked={selectedMDFObjects.includes(obj)}
                              onChange={() => handleObjectToggle(obj, setSelectedMDFObjects)}
                              className="mr-1"
                            />
                            <span className="truncate">{obj}</span>
                          </label>
                        ))}
                      </div>
                      {sfData.entities.mdf_objects.length > 50 && (
                        <p className="text-xs text-gray-500 mt-1">
                          ... and {sfData.entities.mdf_objects.length - 50} more
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* FO Translations */}
              <label className="flex items-start cursor-pointer">
                <input
                  type="checkbox"
                  checked={exportFOTranslations}
                  onChange={(e) => setExportFOTranslations(e.target.checked)}
                  disabled={!hasConnection}
                  className="mt-1 mr-3"
                />
                <div className="flex-1">
                  <div className="flex items-center">
                    <Globe className="w-4 h-4 mr-1 text-gray-600" />
                    <span className="text-sm font-medium text-gray-900">
                      Export Foundation Object Translations
                    </span>
                    {sfData && (
                      <span className="ml-2 text-xs bg-gray-100 px-2 py-0.5 rounded">
                        {sfData.entities.foundation_objects.length} FO available
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Export translations for Foundation Objects (locations, departments, etc.)
                  </p>
                </div>
              </label>

              {/* FO Objects Selection */}
              {exportFOTranslations && sfData && sfData.entities.foundation_objects.length > 0 && (
                <div className="ml-6 p-3 bg-gray-50 rounded-md">
                  <p className="text-xs font-medium text-gray-700 mb-2">
                    FO Objects ({selectedFOObjects.length}/
                    {sfData.entities.foundation_objects.length} selected):
                  </p>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-1 max-h-40 overflow-y-auto">
                    {sfData.entities.foundation_objects.map((obj) => (
                      <label
                        key={obj}
                        className="flex items-center text-xs cursor-pointer p-1 hover:bg-gray-100 rounded"
                      >
                        <input
                          type="checkbox"
                          checked={selectedFOObjects.includes(obj)}
                          onChange={() => handleObjectToggle(obj, setSelectedFOObjects)}
                          className="mr-1"
                        />
                        <span className="truncate">{obj}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Summary */}
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
            <p className="text-sm text-blue-800">
              <strong>Configuration Summary:</strong>
            </p>
            <ul className="mt-2 text-xs text-blue-700 space-y-1">
              <li>
                • {selectedLocales.length} language{selectedLocales.length !== 1 ? 's' : ''} selected
              </li>
              {hasConnection && (
                <>
                  {exportPicklists && (
                    <li>
                      • Picklists enabled (
                      {sfData
                        ? `${sfData.picklists.mdf_count + sfData.picklists.legacy_count} total`
                        : 'all'}
                      )
                    </li>
                  )}
                  {exportMDFObjects && (
                    <li>
                      • {selectedECObjects.length} EC + {selectedMDFObjects.length} MDF objects
                      selected
                    </li>
                  )}
                  {exportFOTranslations && (
                    <li>• {selectedFOObjects.length} FO objects selected</li>
                  )}
                </>
              )}
            </ul>
          </div>

          {/* Save Button */}
          <div className="flex justify-between items-center pt-4 border-t">
            <div>
              {saveSuccess && (
                <span className="text-sm text-green-600 flex items-center">
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Configuration saved successfully
                </span>
              )}
            </div>

            <button onClick={handleSave} disabled={isSaving} className="btn-primary">
              {isSaving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Save Configuration
                </>
              )}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
