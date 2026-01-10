/**
 * TREXIMA v2.0 - Export Configuration Component
 *
 * Configure export options with DYNAMIC data fetched from the connected SF instance.
 * Displays real entities, picklists, and locales from the API.
 */

import { useEffect, useState, useMemo } from 'react';
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
  Layers,
} from 'lucide-react';
import { useProjectStore } from '../../store/projectStore';
import projectsApi from '../../api/projects';
import type { ECObject, FOObject, FOTranslationType } from '../../types';

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

type TabId = 'ec-hris' | 'fo-translations' | 'mdf-objects' | 'picklists';

export default function ExportConfig({ projectId }: ExportConfigProps) {
  const { currentProject, updateConfig, isSaving } = useProjectStore();

  // SF dynamic data
  const [sfData, setSfData] = useState<SFData | null>(null);
  const [isLoadingSF, setIsLoadingSF] = useState(false);
  const [sfError, setSfError] = useState<string | null>(null);

  // Tab navigation
  const [activeTab, setActiveTab] = useState<TabId>('ec-hris');

  // Export options
  const [selectedLocales, setSelectedLocales] = useState<string[]>(['en_US']);
  const [exportMDFPicklists, setExportMDFPicklists] = useState(false);
  const [exportLegacyPicklists, setExportLegacyPicklists] = useState(false);

  // Object selections
  const [selectedECObjects, setSelectedECObjects] = useState<string[]>([]);
  const [selectedFOObjects, setSelectedFOObjects] = useState<string[]>([]);
  const [selectedMDFObjects, setSelectedMDFObjects] = useState<string[]>([]);
  const [selectedFOTypes, setSelectedFOTypes] = useState<string[]>([]);

  // Static definitions from backend
  const [staticECObjects, setStaticECObjects] = useState<ECObject[]>([]);
  const [staticFOObjects, setStaticFOObjects] = useState<FOObject[]>([]);
  const [foTranslationTypes, setFOTranslationTypes] = useState<FOTranslationType[]>([]);

  const [saveSuccess, setSaveSuccess] = useState(false);

  const hasConnection = currentProject?.config?.sf_connection?.connected;

  // Load config from project
  useEffect(() => {
    if (currentProject?.config) {
      const config = currentProject.config;
      if (config.locales) setSelectedLocales(config.locales);
      if (config.export_mdf_picklists !== undefined) setExportMDFPicklists(config.export_mdf_picklists);
      if (config.export_legacy_picklists !== undefined) setExportLegacyPicklists(config.export_legacy_picklists);
      if (config.ec_objects) setSelectedECObjects(config.ec_objects);
      if (config.mdf_objects) setSelectedMDFObjects(config.mdf_objects);
      if (config.fo_objects) setSelectedFOObjects(config.fo_objects);
      if (config.fo_translation_types) setSelectedFOTypes(config.fo_translation_types);
    }
  }, [currentProject]);

  // Load static definitions from backend on mount
  useEffect(() => {
    const loadStaticData = async () => {
      try {
        const [ecObjects, foObjects, foTypes] = await Promise.all([
          projectsApi.export.getECObjects(),
          projectsApi.export.getFOObjects(),
          projectsApi.export.getFOTranslationTypes(),
        ]);
        setStaticECObjects(ecObjects);
        setStaticFOObjects(foObjects);
        setFOTranslationTypes(foTypes);
      } catch (error) {
        console.error('Failed to load static object definitions:', error);
      }
    };
    loadStaticData();
  }, []);

  // Fetch SF data when connected
  const fetchSFData = async () => {
    if (!hasConnection) return;

    setIsLoadingSF(true);
    setSfError(null);
    try {
      const response = await projectsApi.connection.getSFObjects(projectId);
      if (response.success && response.data) {
        setSfData(response.data);
        // DON'T override locales - they should come from saved config
        // SF data only provides the list of AVAILABLE locales, not the selection
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

  // Compute available EC objects: static definitions filtered by SF availability
  const availableECObjects = useMemo(() => {
    if (!sfData) return staticECObjects;
    return staticECObjects.filter((obj) => sfData.entities.ec_objects.includes(obj.id));
  }, [staticECObjects, sfData]);

  // Compute available FO objects: show all objects (don't filter by SF availability)
  const availableFOObjects = useMemo(() => {
    return staticFOObjects;
  }, [staticFOObjects]);

  // Split EC objects into GLOBAL and LOCAL (country-specific)
  const { globalECObjects, localECObjects } = useMemo(() => {
    const global = availableECObjects.filter((obj) => !obj.id.startsWith('PerGlobalInfo'));
    const local = availableECObjects.filter((obj) => obj.id.startsWith('PerGlobalInfo'));
    return { globalECObjects: global, localECObjects: local };
  }, [availableECObjects]);

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

  // Select All / Deselect All handlers for GLOBAL EC objects
  const handleSelectAllGlobalEC = () => {
    const globalIds = globalECObjects.map((o) => o.id);
    setSelectedECObjects((prev) => [...new Set([...prev, ...globalIds])]);
  };
  const handleDeselectAllGlobalEC = () => {
    const globalIds = new Set(globalECObjects.map((o) => o.id));
    setSelectedECObjects((prev) => prev.filter((id) => !globalIds.has(id)));
  };

  // Select All / Deselect All handlers for LOCAL EC objects
  const handleSelectAllLocalEC = () => {
    const localIds = localECObjects.map((o) => o.id);
    setSelectedECObjects((prev) => [...new Set([...prev, ...localIds])]);
  };
  const handleDeselectAllLocalEC = () => {
    const localIds = new Set(localECObjects.map((o) => o.id));
    setSelectedECObjects((prev) => prev.filter((id) => !localIds.has(id)));
  };

  const handleSelectAllMDF = () => setSelectedMDFObjects(sfData?.entities.mdf_objects || []);
  const handleDeselectAllMDF = () => setSelectedMDFObjects([]);

  const handleSelectAllFO = () => setSelectedFOObjects(availableFOObjects.map((o) => o.id));
  const handleDeselectAllFO = () => setSelectedFOObjects([]);

  const handleSelectAllFOTypes = () => setSelectedFOTypes(foTranslationTypes.map((t) => t.id));
  const handleDeselectAllFOTypes = () => setSelectedFOTypes([]);

  const handleSave = async () => {
    setSaveSuccess(false);
    try {
      await updateConfig(projectId, {
        locales: selectedLocales,
        export_mdf_picklists: exportMDFPicklists,
        export_legacy_picklists: exportLegacyPicklists,
        ec_objects: selectedECObjects,
        mdf_objects: selectedMDFObjects,
        fo_objects: selectedFOObjects,
        fo_translation_types: selectedFOTypes,
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to save config:', error);
    }
  };

  // Available locales - from SF data (all available), fallback to languages.available
  const availableLocales: string[] =
    sfData?.locales ||
    currentProject?.config?.languages?.available?.map((l: { code: string }) => l.code) ||
    [];

  // Tab configuration
  const tabs = [
    { id: 'ec-hris' as TabId, label: 'EC HRIS Sections', icon: Database },
    { id: 'fo-translations' as TabId, label: 'FO Translations', icon: Globe },
    { id: 'mdf-objects' as TabId, label: 'MDF Object Definitions', icon: Layers },
    { id: 'picklists' as TabId, label: 'Picklists', icon: List },
  ];

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
          {/* Language Selection - Always visible above tabs */}
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
                <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
                  <label className="flex items-center p-2 rounded border border-sap-blue-500 bg-sap-blue-50 opacity-75">
                    <input type="checkbox" checked={true} disabled={true} className="mr-2" />
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

          {/* Tab Navigation */}
          <div className="card">
            <div className="border-b border-gray-200">
              <nav className="flex -mb-px">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex-1 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === tab.id
                        ? 'border-sap-blue-500 text-sap-blue-600 bg-sap-blue-50'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <tab.icon className="w-4 h-4 inline mr-2" />
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>

            <div className="card-body">
              {/* Tab 1: EC HRIS Sections */}
              {activeTab === 'ec-hris' && (
                <div className="space-y-6">
                  {/* GLOBAL Section */}
                  <div>
                    <div className="flex justify-between items-center mb-3">
                      <h5 className="font-medium text-gray-900">
                        GLOBAL Sections ({globalECObjects.length})
                      </h5>
                      <div className="flex space-x-2">
                        <button
                          type="button"
                          onClick={handleSelectAllGlobalEC}
                          className="text-xs text-sap-blue-600 hover:text-sap-blue-800"
                        >
                          All
                        </button>
                        <span className="text-gray-300">|</span>
                        <button
                          type="button"
                          onClick={handleDeselectAllGlobalEC}
                          className="text-xs text-sap-blue-600 hover:text-sap-blue-800"
                        >
                          None
                        </button>
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                      {globalECObjects.map((obj) => (
                        <label
                          key={obj.id}
                          className={`flex items-start p-3 rounded border cursor-pointer transition-colors ${
                            selectedECObjects.includes(obj.id)
                              ? 'border-sap-blue-500 bg-sap-blue-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={selectedECObjects.includes(obj.id)}
                            onChange={() => handleObjectToggle(obj.id, setSelectedECObjects)}
                            className="mt-0.5 mr-3"
                          />
                          <div className="min-w-0 flex-1">
                            <span className="font-medium block">{obj.name}</span>
                            <span className="text-xs text-gray-500">({obj.id})</span>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* LOCAL Section */}
                  <div>
                    <div className="flex justify-between items-center mb-3">
                      <h5 className="font-medium text-gray-900">
                        LOCAL Sections - Country-Specific ({localECObjects.length})
                      </h5>
                      <div className="flex space-x-2">
                        <button
                          type="button"
                          onClick={handleSelectAllLocalEC}
                          className="text-xs text-sap-blue-600 hover:text-sap-blue-800"
                        >
                          All
                        </button>
                        <span className="text-gray-300">|</span>
                        <button
                          type="button"
                          onClick={handleDeselectAllLocalEC}
                          className="text-xs text-sap-blue-600 hover:text-sap-blue-800"
                        >
                          None
                        </button>
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                      {localECObjects.map((obj) => (
                        <label
                          key={obj.id}
                          className={`flex items-start p-3 rounded border cursor-pointer transition-colors ${
                            selectedECObjects.includes(obj.id)
                              ? 'border-sap-blue-500 bg-sap-blue-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={selectedECObjects.includes(obj.id)}
                            onChange={() => handleObjectToggle(obj.id, setSelectedECObjects)}
                            className="mt-0.5 mr-3"
                          />
                          <div className="min-w-0 flex-1">
                            <span className="font-medium block">{obj.name}</span>
                            <span className="text-xs text-gray-500">({obj.id})</span>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 2: FO Translations */}
              {activeTab === 'fo-translations' && (
                <div>
                  <div className="flex justify-between items-center mb-3">
                    <h5 className="font-medium text-gray-900">
                      Translation Types ({selectedFOTypes.length}/{foTranslationTypes.length} selected)
                    </h5>
                    <div className="flex space-x-2">
                      <button
                        type="button"
                        onClick={handleSelectAllFOTypes}
                        className="text-xs text-sap-blue-600 hover:text-sap-blue-800"
                      >
                        All
                      </button>
                      <span className="text-gray-300">|</span>
                      <button
                        type="button"
                        onClick={handleDeselectAllFOTypes}
                        className="text-xs text-sap-blue-600 hover:text-sap-blue-800"
                      >
                        None
                      </button>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                    {foTranslationTypes.map((type) => (
                      <label
                        key={type.id}
                        className={`flex items-start p-3 rounded border cursor-pointer transition-colors ${
                          selectedFOTypes.includes(type.id)
                            ? 'border-sap-blue-500 bg-sap-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedFOTypes.includes(type.id)}
                          onChange={() => handleObjectToggle(type.id, setSelectedFOTypes)}
                          className="mt-0.5 mr-3"
                        />
                        <div className="min-w-0 flex-1">
                          <span className="font-medium block">{type.name}</span>
                          <span className="text-xs text-gray-500 block">{type.description}</span>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab 3: MDF Object Definitions */}
              {activeTab === 'mdf-objects' && (
                <div className="space-y-6">
                  {/* Standard FO Objects */}
                  <div>
                    <div className="flex justify-between items-center mb-3">
                      <h5 className="font-medium text-gray-900">
                        Standard Foundation Objects ({selectedFOObjects.length}/{availableFOObjects.length} selected)
                      </h5>
                      <div className="flex space-x-2">
                        <button
                          type="button"
                          onClick={handleSelectAllFO}
                          className="text-xs text-sap-blue-600 hover:text-sap-blue-800"
                        >
                          All
                        </button>
                        <span className="text-gray-300">|</span>
                        <button
                          type="button"
                          onClick={handleDeselectAllFO}
                          className="text-xs text-sap-blue-600 hover:text-sap-blue-800"
                        >
                          None
                        </button>
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                      {availableFOObjects.map((obj) => (
                        <label
                          key={obj.id}
                          className={`flex items-start p-3 rounded border cursor-pointer transition-colors ${
                            selectedFOObjects.includes(obj.id)
                              ? 'border-sap-blue-500 bg-sap-blue-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={selectedFOObjects.includes(obj.id)}
                            onChange={() => handleObjectToggle(obj.id, setSelectedFOObjects)}
                            className="mt-0.5 mr-3"
                          />
                          <div className="min-w-0 flex-1">
                            <span className="font-medium block">{obj.name}</span>
                            <span className="text-xs text-gray-500">({obj.id})</span>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Custom MDF Objects */}
                  {sfData && sfData.entities.mdf_objects.length > 0 && (
                    <div>
                      <div className="flex justify-between items-center mb-3">
                        <h5 className="font-medium text-gray-900">
                          Custom MDF Objects ({selectedMDFObjects.length}/{sfData.entities.mdf_objects.length} selected)
                        </h5>
                        <div className="flex space-x-2">
                          <button
                            type="button"
                            onClick={handleSelectAllMDF}
                            className="text-xs text-sap-blue-600 hover:text-sap-blue-800"
                          >
                            All
                          </button>
                          <span className="text-gray-300">|</span>
                          <button
                            type="button"
                            onClick={handleDeselectAllMDF}
                            className="text-xs text-sap-blue-600 hover:text-sap-blue-800"
                          >
                            None
                          </button>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-64 overflow-y-auto">
                        {sfData.entities.mdf_objects.map((obj) => (
                          <label
                            key={obj}
                            className={`flex items-center p-2 rounded border cursor-pointer transition-colors text-xs ${
                              selectedMDFObjects.includes(obj)
                                ? 'border-sap-blue-500 bg-sap-blue-50'
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={selectedMDFObjects.includes(obj)}
                              onChange={() => handleObjectToggle(obj, setSelectedMDFObjects)}
                              className="mr-2"
                            />
                            <span className="truncate">{obj}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 4: Picklists */}
              {activeTab === 'picklists' && (
                <div className="space-y-4">
                  <label
                    className={`flex items-center p-4 rounded-lg border cursor-pointer transition-colors ${
                      exportMDFPicklists
                        ? 'border-sap-blue-500 bg-sap-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={exportMDFPicklists}
                      onChange={(e) => setExportMDFPicklists(e.target.checked)}
                      className="mr-4"
                    />
                    <div>
                      <span className="font-medium">MDF Picklists</span>
                      <span className="text-gray-500 ml-2 text-sm">
                        ({sfData?.picklists.mdf_count || 0} available)
                      </span>
                      <p className="text-xs text-gray-500 mt-1">
                        Modern picklists using Metadata Framework
                      </p>
                    </div>
                  </label>

                  <label
                    className={`flex items-center p-4 rounded-lg border cursor-pointer transition-colors ${
                      exportLegacyPicklists
                        ? 'border-sap-blue-500 bg-sap-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={exportLegacyPicklists}
                      onChange={(e) => setExportLegacyPicklists(e.target.checked)}
                      className="mr-4"
                    />
                    <div>
                      <span className="font-medium">Legacy Picklists</span>
                      <span className="text-gray-500 ml-2 text-sm">
                        ({sfData?.picklists.legacy_count || 0} available)
                      </span>
                      <p className="text-xs text-gray-500 mt-1">
                        Traditional picklists from older configuration
                      </p>
                    </div>
                  </label>
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
              <li>
                • {selectedECObjects.length} EC HRIS sections selected
              </li>
              <li>
                • {selectedFOTypes.length} FO translation types selected
              </li>
              <li>
                • {selectedFOObjects.length} FO objects + {selectedMDFObjects.length} MDF objects selected
              </li>
              <li>
                • Picklists: {exportMDFPicklists ? 'MDF' : ''}{exportMDFPicklists && exportLegacyPicklists ? ' + ' : ''}{exportLegacyPicklists ? 'Legacy' : ''}{!exportMDFPicklists && !exportLegacyPicklists ? 'None' : ''}
              </li>
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
