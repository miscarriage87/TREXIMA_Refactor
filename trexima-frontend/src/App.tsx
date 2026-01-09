/**
 * TREXIMA v4.0 - Main Application Component
 */

import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Store
import { useAuthStore } from './store/authStore';

// Layout
import MainLayout from './components/layout/MainLayout';

// Pages
import Dashboard from './pages/Dashboard';
import ProjectPage from './pages/ProjectPage';
import AdminPage from './pages/AdminPage';
import LoginPage from './pages/LoginPage';
import NotFoundPage from './pages/NotFoundPage';

// Protected Route component
import ProtectedRoute from './components/common/ProtectedRoute';

// Debug Console
import DebugConsole from './components/DebugConsole';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 minute
      retry: 1,
    },
  },
});

function App() {
  const { checkAuth, fetchConfig, isLoading } = useAuthStore();

  useEffect(() => {
    // Check authentication status on mount
    const init = async () => {
      await fetchConfig();
      await checkAuth();
    };
    init();
  }, [checkAuth, fetchConfig]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sap-blue-500"></div>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="projects/:projectId" element={<ProjectPage />} />
            <Route path="admin" element={<AdminPage />} />
          </Route>

          {/* 404 */}
          <Route path="/404" element={<NotFoundPage />} />
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Routes>

        {/* Debug Console - always visible for debugging */}
        <DebugConsole isAdmin={true} />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
