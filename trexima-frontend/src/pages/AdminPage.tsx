/**
 * TREXIMA v2.0 - Admin Page
 *
 * Administrator dashboard for system management.
 */

import { useEffect, useState } from 'react';
import {
  Users,
  Folder,
  HardDrive,
  Activity,
  RefreshCw,
  Trash2,
  Shield,
} from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import apiClient from '../api/client';
import type { SystemStats } from '../types';

export default function AdminPage() {
  const { user } = useAuthStore();
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.get('/admin/stats');
      setStats(response.data);
    } catch (err) {
      setError('Failed to load system statistics');
      console.error('Error fetching stats:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCleanupExpired = async () => {
    try {
      await apiClient.post('/admin/cleanup/expired');
      fetchStats();
    } catch (err) {
      console.error('Cleanup failed:', err);
    }
  };

  if (!user?.is_admin) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8 text-center">
        <Shield className="mx-auto h-12 w-12 text-gray-400" />
        <h2 className="mt-4 text-lg font-medium text-gray-900">Access Denied</h2>
        <p className="mt-2 text-sm text-gray-500">
          You don't have permission to access this page.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">System overview and management</p>
        </div>

        <button onClick={fetchStats} className="btn-secondary" disabled={isLoading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sap-blue-500"></div>
        </div>
      ) : stats ? (
        <>
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {/* Users */}
            <div className="card">
              <div className="card-body">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Users className="h-8 w-8 text-sap-blue-500" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Total Users</p>
                    <p className="text-2xl font-semibold text-gray-900">{stats.users.total}</p>
                  </div>
                </div>
                <div className="mt-4 text-xs text-gray-500">
                  <span className="text-sap-blue-600">{stats.users.admins}</span> admins ·{' '}
                  <span className="text-green-600">{stats.users.active_7d}</span> active (7d)
                </div>
              </div>
            </div>

            {/* Projects */}
            <div className="card">
              <div className="card-body">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Folder className="h-8 w-8 text-sap-orange-500" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Total Projects</p>
                    <p className="text-2xl font-semibold text-gray-900">{stats.projects.total}</p>
                  </div>
                </div>
                <div className="mt-4 text-xs text-gray-500">
                  {Object.entries(stats.projects.by_status || {}).map(([status, count]) => (
                    <span key={status} className="mr-2">
                      {status}: {count}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Files */}
            <div className="card">
              <div className="card-body">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <HardDrive className="h-8 w-8 text-sap-green-500" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Storage</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {stats.storage.total_files}
                    </p>
                  </div>
                </div>
                <div className="mt-4 text-xs text-gray-500">
                  {(stats.storage.total_size / (1024 * 1024)).toFixed(1)} MB total
                </div>
              </div>
            </div>

            {/* Active Operations */}
            <div className="card">
              <div className="card-body">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Activity className="h-8 w-8 text-purple-500" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Active Operations</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {stats.operations.active}
                    </p>
                  </div>
                </div>
                <div className="mt-4 text-xs text-gray-500">
                  {stats.files.expired} expired files
                </div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="card">
            <div className="card-header">
              <h2 className="text-lg font-medium">Maintenance Actions</h2>
            </div>
            <div className="card-body">
              <div className="flex flex-wrap gap-4">
                <button onClick={handleCleanupExpired} className="btn-secondary">
                  <Trash2 className="w-4 h-4 mr-2" />
                  Clean Expired Files ({stats.files.expired})
                </button>
              </div>
            </div>
          </div>

          {/* Generated timestamp */}
          <p className="mt-4 text-xs text-gray-400 text-right">
            Last updated: {new Date(stats.generated_at).toLocaleString()}
          </p>
        </>
      ) : null}
    </div>
  );
}
