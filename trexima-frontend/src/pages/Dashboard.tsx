/**
 * TREXIMA v2.0 - Dashboard Page
 *
 * Main dashboard showing user's projects.
 */

import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Folder, Clock, FileText, Trash2, MoreVertical } from 'lucide-react';
import { useProjectStore } from '../store/projectStore';
import { useAuthStore } from '../store/authStore';
import type { Project } from '../types';

// Max projects per user
const MAX_PROJECTS = 3;

export default function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { projects, fetchProjects, createProject, deleteProject, isLoading, error } =
    useProjectStore();
  const [showNewProject, setShowNewProject] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;

    setIsSaving(true);
    try {
      const project = await createProject({
        name: newProjectName.trim(),
        description: newProjectDesc.trim() || undefined,
      });
      setShowNewProject(false);
      setNewProjectName('');
      setNewProjectDesc('');
      navigate(`/projects/${project.id}`);
    } catch {
      // Error handled by store
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    try {
      await deleteProject(projectId);
      setDeleteConfirm(null);
    } catch {
      // Error handled by store
    }
  };

  const canCreateProject = projects.length < MAX_PROJECTS;

  const getStatusBadge = (status: Project['status']) => {
    const badges: Record<Project['status'], { class: string; label: string }> = {
      draft: { class: 'badge-gray', label: 'Draft' },
      configured: { class: 'badge-info', label: 'Configured' },
      exporting: { class: 'badge-warning', label: 'Exporting' },
      exported: { class: 'badge-success', label: 'Exported' },
      importing: { class: 'badge-warning', label: 'Importing' },
      imported: { class: 'badge-success', label: 'Imported' },
    };
    return badges[status] || badges.draft;
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
          <p className="mt-1 text-sm text-gray-500">
            {user?.display_name ? `Welcome back, ${user.display_name}` : 'Manage your translation projects'}
          </p>
        </div>

        <div className="mt-4 sm:mt-0">
          {canCreateProject ? (
            <button
              onClick={() => setShowNewProject(true)}
              className="btn-primary"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Project
            </button>
          ) : (
            <div className="text-sm text-gray-500">
              {MAX_PROJECTS} of {MAX_PROJECTS} projects used
            </div>
          )}
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* New Project Form */}
      {showNewProject && (
        <div className="mb-8 card">
          <div className="card-header">
            <h2 className="text-lg font-medium">Create New Project</h2>
          </div>
          <form onSubmit={handleCreateProject} className="card-body">
            <div className="space-y-4">
              <div>
                <label htmlFor="name" className="label">
                  Project Name
                </label>
                <input
                  type="text"
                  id="name"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="e.g., Q1 2026 Translation Update"
                  className="input"
                  required
                  autoFocus
                />
              </div>

              <div>
                <label htmlFor="description" className="label">
                  Description (optional)
                </label>
                <textarea
                  id="description"
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  placeholder="Brief description of the translation project"
                  className="input"
                  rows={2}
                />
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowNewProject(false);
                    setNewProjectName('');
                    setNewProjectDesc('');
                  }}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSaving || !newProjectName.trim()}
                  className="btn-primary"
                >
                  {isSaving ? 'Creating...' : 'Create Project'}
                </button>
              </div>
            </div>
          </form>
        </div>
      )}

      {/* Projects Grid */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sap-blue-500"></div>
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center py-12">
          <Folder className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">No projects yet</h3>
          <p className="mt-2 text-sm text-gray-500">
            Get started by creating your first translation project.
          </p>
          {canCreateProject && (
            <button
              onClick={() => setShowNewProject(true)}
              className="mt-4 btn-primary"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Project
            </button>
          )}
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => {
            const badge = getStatusBadge(project.status);

            return (
              <div key={project.id} className="card hover:shadow-md transition-shadow">
                <div className="card-body">
                  <div className="flex items-start justify-between">
                    <Link
                      to={`/projects/${project.id}`}
                      className="flex-1 min-w-0"
                    >
                      <h3 className="text-lg font-medium text-gray-900 truncate hover:text-sap-blue-600">
                        {project.name}
                      </h3>
                    </Link>

                    <div className="relative ml-2">
                      <button
                        onClick={() =>
                          setDeleteConfirm(deleteConfirm === project.id ? null : project.id)
                        }
                        className="p-1 text-gray-400 hover:text-gray-600 rounded"
                      >
                        <MoreVertical className="w-4 h-4" />
                      </button>

                      {deleteConfirm === project.id && (
                        <div className="absolute right-0 mt-1 w-32 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 z-10">
                          <button
                            onClick={() => handleDeleteProject(project.id)}
                            className="w-full flex items-center px-3 py-2 text-sm text-red-600 hover:bg-red-50"
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Delete
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {project.description && (
                    <p className="mt-1 text-sm text-gray-500 line-clamp-2">
                      {project.description}
                    </p>
                  )}

                  <div className="mt-4 flex items-center justify-between">
                    <span className={badge.class}>{badge.label}</span>

                    <div className="flex items-center text-xs text-gray-500">
                      <FileText className="w-3 h-3 mr-1" />
                      {project.file_count || 0} files
                    </div>
                  </div>

                  <div className="mt-3 flex items-center text-xs text-gray-400">
                    <Clock className="w-3 h-3 mr-1" />
                    Updated {new Date(project.updated_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            );
          })}

          {/* Empty slot for new project */}
          {canCreateProject && !showNewProject && (
            <button
              onClick={() => setShowNewProject(true)}
              className="card border-2 border-dashed border-gray-300 hover:border-sap-blue-400 hover:bg-gray-50 transition-colors"
            >
              <div className="card-body flex flex-col items-center justify-center py-8 text-gray-400 hover:text-sap-blue-500">
                <Plus className="w-8 h-8 mb-2" />
                <span className="text-sm font-medium">New Project</span>
              </div>
            </button>
          )}
        </div>
      )}

      {/* Project limit info */}
      <div className="mt-8 text-center">
        <p className="text-xs text-gray-400">
          {projects.length} of {MAX_PROJECTS} projects used
        </p>
      </div>
    </div>
  );
}
