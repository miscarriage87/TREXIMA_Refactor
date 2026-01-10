/**
 * TREXIMA v2.0 - Connection Configuration Component
 *
 * SF OData API connection configuration and testing.
 */

import { useState, useEffect } from 'react';
import { Globe, CheckCircle, AlertCircle, Loader2, Eye, EyeOff } from 'lucide-react';
import { useProjectStore } from '../../store/projectStore';
import projectsApi from '../../api/projects';
import type { SFEndpointCategory } from '../../types';

interface ConnectionConfigProps {
  projectId: string;
}

export default function ConnectionConfig({ projectId }: ConnectionConfigProps) {
  const { currentProject, updateConfig, isSaving } = useProjectStore();
  const [endpoints, setEndpoints] = useState<Record<string, SFEndpointCategory>>({});
  const [selectedCategory, setSelectedCategory] = useState<string>('production');
  const [selectedEndpoint, setSelectedEndpoint] = useState<string>('');
  const [companyId, setCompanyId] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message?: string;
    locales?: string[];
  } | null>(null);

  // Load endpoints on mount
  useEffect(() => {
    const loadEndpoints = async () => {
      try {
        const data = await projectsApi.connection.getEndpoints();
        setEndpoints(data);
      } catch (error) {
        console.error('Failed to load endpoints:', error);
      }
    };
    loadEndpoints();
  }, []);

  // Initialize from project config
  useEffect(() => {
    if (currentProject?.config?.sf_connection) {
      const conn = currentProject.config.sf_connection;
      if (conn.endpoint) {
        setSelectedEndpoint(conn.endpoint);
        // Find category
        for (const [cat, data] of Object.entries(endpoints)) {
          if (data.endpoints.some((e) => e.url === conn.endpoint)) {
            setSelectedCategory(cat);
            break;
          }
        }
      }
      if (conn.company_id) setCompanyId(conn.company_id);
      if (conn.username) setUsername(conn.username);
    }
  }, [currentProject, endpoints]);

  const handleTestConnection = async () => {
    if (!selectedEndpoint || !companyId || !username || !password) {
      setTestResult({
        success: false,
        message: 'Please fill in all connection details',
      });
      return;
    }

    setIsTesting(true);
    setTestResult(null);

    try {
      const result = await projectsApi.connection.test(projectId, {
        endpoint: selectedEndpoint,
        company_id: companyId,
        username,
        password,
      });

      setTestResult(result);

      if (result.success) {
        // Save successful connection to project config
        await updateConfig(projectId, {
          sf_connection: {
            endpoint: selectedEndpoint,
            company_id: companyId,
            username,
            password,
            connected: true,
            last_tested: new Date().toISOString(),
          },
        });
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: error instanceof Error ? error.message : 'Connection failed',
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSkip = async () => {
    // Save partial config without credentials
    await updateConfig(projectId, {
      sf_connection: {
        endpoint: selectedEndpoint || '',
        company_id: companyId || '',
        connected: false,
      },
    });
  };

  const currentEndpoints = endpoints[selectedCategory]?.endpoints || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <Globe className="mx-auto h-12 w-12 text-sap-blue-500 mb-4" />
        <h3 className="text-lg font-medium text-gray-900">
          Connect to SuccessFactors OData API
        </h3>
        <p className="mt-2 text-sm text-gray-600">
          Connection is required for fetching picklists, MDF objects, and Foundation Object
          translations. You can skip this step if you only need to process uploaded data models.
        </p>
      </div>

      {/* Endpoint Selection */}
      <div>
        <label className="label">Datacenter</label>
        <div className="grid grid-cols-2 gap-2 mb-3">
          {Object.entries(endpoints).map(([key, data]) => (
            <button
              key={key}
              onClick={() => {
                setSelectedCategory(key);
                setSelectedEndpoint('');
              }}
              className={`px-4 py-2 text-sm rounded-md border-2 transition-colors ${
                selectedCategory === key
                  ? 'border-sap-blue-500 bg-sap-blue-50 text-sap-blue-700'
                  : 'border-gray-200 text-gray-700 hover:border-gray-300'
              }`}
            >
              {data.label}
            </button>
          ))}
        </div>

        <select
          value={selectedEndpoint}
          onChange={(e) => setSelectedEndpoint(e.target.value)}
          className="input"
          required
        >
          <option value="">Select an endpoint...</option>
          {currentEndpoints.map((ep) => (
            <option key={ep.id} value={ep.url}>
              {ep.name} ({ep.region})
            </option>
          ))}
        </select>
        {selectedEndpoint && selectedCategory !== 'custom' && (
          <p className="mt-2 text-xs text-gray-500 font-mono bg-gray-50 p-2 rounded border">
            {selectedEndpoint}
          </p>
        )}
      </div>

      {/* Custom URL */}
      {selectedCategory === 'custom' && (
        <div>
          <label htmlFor="custom-url" className="label">
            Custom OData URL
          </label>
          <input
            type="url"
            id="custom-url"
            value={selectedEndpoint}
            onChange={(e) => setSelectedEndpoint(e.target.value)}
            placeholder="https://api.successfactors.com/odata/v2"
            className="input"
          />
          <p className="mt-1 text-xs text-gray-500">
            Enter the full OData v2 endpoint URL
          </p>
        </div>
      )}

      {/* Company ID */}
      <div>
        <label htmlFor="company-id" className="label">
          Company ID
        </label>
        <input
          type="text"
          id="company-id"
          value={companyId}
          onChange={(e) => setCompanyId(e.target.value)}
          placeholder="e.g., SFPART123456"
          className="input"
          required
        />
      </div>

      {/* Username */}
      <div>
        <label htmlFor="username" className="label">
          API Username
        </label>
        <input
          type="text"
          id="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="admin@company.com"
          className="input"
          autoComplete="username"
          required
        />
      </div>

      {/* Password */}
      <div>
        <label htmlFor="password" className="label">
          API Password
        </label>
        <div className="relative">
          <input
            type={showPassword ? 'text' : 'password'}
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="input pr-10"
            autoComplete="current-password"
            required
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>
        <p className="mt-1 text-xs text-gray-500">
          Note: Password is not stored permanently. You'll need to re-enter it each session.
        </p>
      </div>

      {/* Test Result */}
      {testResult && (
        <div
          className={`p-4 rounded-md border flex items-start ${
            testResult.success
              ? 'bg-green-50 border-green-200'
              : 'bg-red-50 border-red-200'
          }`}
        >
          {testResult.success ? (
            <CheckCircle className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-5 h-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" />
          )}
          <div className="flex-1">
            <p className={`text-sm font-medium ${
              testResult.success ? 'text-green-800' : 'text-red-800'
            }`}>
              {testResult.success ? 'Connection Successful!' : 'Connection Failed'}
            </p>
            {testResult.message && (
              <p className={`text-xs mt-1 ${
                testResult.success ? 'text-green-600' : 'text-red-600'
              }`}>
                {testResult.message}
              </p>
            )}
            {testResult.locales && (
              <p className="text-xs mt-2 text-green-600">
                Found {testResult.locales.length} active locales in the system
              </p>
            )}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-between items-center pt-4 border-t">
        <button onClick={handleSkip} className="btn-ghost" disabled={isSaving}>
          Skip for now
        </button>

        <button
          onClick={handleTestConnection}
          disabled={isTesting || isSaving || !selectedEndpoint || !companyId || !username || !password}
          className="btn-primary"
        >
          {isTesting ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Testing Connection...
            </>
          ) : (
            <>
              <CheckCircle className="w-4 h-4 mr-2" />
              Test Connection
            </>
          )}
        </button>
      </div>

      {/* Info Notice */}
      <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
        <p className="text-xs text-blue-800">
          <strong>Security Note:</strong> Connection credentials are encrypted and only used during
          your session. We recommend using a dedicated API user with read-only access.
        </p>
      </div>
    </div>
  );
}
