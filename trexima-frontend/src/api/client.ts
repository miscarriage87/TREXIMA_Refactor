/**
 * TREXIMA v4.0 - API Client
 *
 * Axios-based HTTP client with authentication and error handling.
 */

import axios, { type AxiosInstance, type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { logApiRequest, logApiResponse, logApiError } from '../components/DebugConsole';

// Determine base URL based on environment
const getBaseUrl = (): string => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  // In development, use relative URL (Vite proxy will handle it)
  // In production on BTP, use the same origin
  return '/api';
};

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: getBaseUrl(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Send cookies for XSUAA
});

// Request interceptor for authentication and logging
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get token from localStorage if available (dev mode)
    const token = localStorage.getItem('auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Log the request
    const method = config.method?.toUpperCase() || 'GET';
    const url = config.url || '';
    logApiRequest(method, url, config.data);

    // Store request start time for duration calculation
    (config as InternalAxiosRequestConfig & { _startTime: number })._startTime = Date.now();

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and logging
apiClient.interceptors.response.use(
  (response) => {
    // Log successful response
    const config = response.config as InternalAxiosRequestConfig & { _startTime?: number };
    const duration = config._startTime ? Date.now() - config._startTime : 0;
    const method = config.method?.toUpperCase() || 'GET';
    const url = config.url || '';

    logApiResponse(method, url, response.status, duration, response.data);

    return response;
  },
  (error: AxiosError) => {
    // Log error response
    const config = error.config as (InternalAxiosRequestConfig & { _startTime?: number }) | undefined;
    const duration = config?._startTime ? Date.now() - config._startTime : 0;
    const method = config?.method?.toUpperCase() || 'GET';
    const url = config?.url || '';

    if (error.response) {
      logApiResponse(method, url, error.response.status, duration, error.response.data);
    } else {
      logApiError(method, url, error.message);
    }

    // Handle specific error cases
    if (error.response) {
      const status = error.response.status;

      if (status === 401) {
        // Unauthorized - clear local storage and redirect to login
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');

        // Don't redirect if already on auth routes
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = '/login';
        }
      }

      if (status === 403) {
        // Forbidden - user doesn't have permission
        console.error('Access denied:', error.response.data);
      }

      if (status === 500) {
        // Server error
        console.error('Server error:', error.response.data);
      }
    } else if (error.request) {
      // Network error
      console.error('Network error:', error.message);
    }

    return Promise.reject(error);
  }
);

export default apiClient;

// Helper function to handle API errors
export const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ error?: string; message?: string }>;
    if (axiosError.response?.data) {
      return axiosError.response.data.error ||
             axiosError.response.data.message ||
             'An error occurred';
    }
    if (axiosError.message) {
      return axiosError.message;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
};
