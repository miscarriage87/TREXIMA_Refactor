/**
 * TREXIMA v2.0 - Login Page
 *
 * Handles authentication flow.
 * In production: Redirects to XSUAA login
 * In development: Shows dev login options
 */

import { useEffect, useState, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { LogIn, Loader2, AlertCircle } from 'lucide-react';
import { useAuthStore } from '../store/authStore';

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, login, devLogin, config, error, clearError, fetchConfig } = useAuthStore();

  // Fetch config on mount if not already loaded
  useEffect(() => {
    if (!config) {
      fetchConfig();
    }
  }, [config, fetchConfig]);

  // Compute dev mode based on config - reactive to config changes
  const isDevMode = useMemo(() => {
    // In production build with valid config, use production auth
    if (config?.is_initialized) {
      return false;
    }
    // Only dev mode if explicitly in dev environment AND config says not initialized
    return import.meta.env.DEV && !config?.is_initialized;
  }, [config]);

  const [isLoading, setIsLoading] = useState(false);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  // Clear error on mount
  useEffect(() => {
    clearError();
  }, [clearError]);

  const handleLogin = async () => {
    setIsLoading(true);
    try {
      if (isDevMode) {
        // Development mode - use dev login
        await devLogin();
      } else {
        // Production mode - redirect to XSUAA
        await login();
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Logo */}
        <div className="text-center">
          <div className="mx-auto w-16 h-16 bg-sap-blue-500 rounded-xl flex items-center justify-center">
            <span className="text-3xl font-bold text-white">T</span>
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">TREXIMA</h2>
          <p className="mt-2 text-sm text-gray-600">
            SAP SuccessFactors Translation Management
          </p>
        </div>

        {/* Login Card */}
        <div className="card">
          <div className="card-body">
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-start">
                <AlertCircle className="w-5 h-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            <div className="text-center">
              {!config ? (
                // Loading config
                <div className="flex flex-col items-center justify-center py-4">
                  <Loader2 className="w-8 h-8 animate-spin text-sap-blue-500 mb-2" />
                  <p className="text-sm text-gray-500">Loading authentication...</p>
                </div>
              ) : (
                <>
                  <p className="text-sm text-gray-600 mb-6">
                    {isDevMode
                      ? 'Click below to sign in with a development account.'
                      : 'Click below to sign in with your SAP ID.'}
                  </p>

                  <button
                    onClick={handleLogin}
                    disabled={isLoading}
                    className="w-full btn-primary py-3"
                  >
                    {isLoading ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <>
                        <LogIn className="w-5 h-5 mr-2" />
                        {isDevMode ? 'Sign in (Development)' : 'Sign in with SAP ID'}
                      </>
                    )}
                  </button>
                </>
              )}
            </div>

            {isDevMode && config && (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                <p className="text-xs text-yellow-800">
                  <strong>Development Mode:</strong> XSUAA authentication is not configured.
                  Using mock authentication.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-gray-500">
          Version 4.0 · Enterprise Translation Tool
        </p>
      </div>
    </div>
  );
}
