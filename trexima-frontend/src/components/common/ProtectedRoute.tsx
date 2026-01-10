/**
 * TREXIMA v2.0 - Protected Route Component
 *
 * Ensures user is authenticated before rendering children.
 */

import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAdmin?: boolean;
}

export default function ProtectedRoute({
  children,
  requireAdmin = false,
}: ProtectedRouteProps) {
  const { isAuthenticated, user } = useAuthStore();
  const location = useLocation();

  // Not authenticated - redirect to login
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Requires admin but user is not admin
  if (requireAdmin && !user?.is_admin) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
