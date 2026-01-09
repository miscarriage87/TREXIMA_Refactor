/**
 * TREXIMA v4.0 - Project Store
 *
 * Zustand store for project state management.
 */

import { create } from 'zustand';
import type { Project, ProjectConfig, ProjectFile, GeneratedFile, ProgressUpdate, FileType } from '../types';
import projectsApi from '../api/projects';
import { logInfo, logError } from '../components/DebugConsole';

/**
 * Convert backend files dictionary to frontend array format.
 * Backend returns: { sdm: {id, name, size, uploaded_at} | null, cdm: ..., ... }
 * Frontend expects: ProjectFile[] with {id, file_type, original_filename, file_size, uploaded_at}
 */
function convertFilesToArray(filesDict: Record<string, { id: string; name: string; size: number; uploaded_at: string } | null> | undefined): ProjectFile[] {
  if (!filesDict || typeof filesDict !== 'object') {
    return [];
  }

  // If it's already an array, return it
  if (Array.isArray(filesDict)) {
    return filesDict;
  }

  const result: ProjectFile[] = [];
  for (const [fileType, fileData] of Object.entries(filesDict)) {
    if (fileData !== null && typeof fileData === 'object') {
      result.push({
        id: fileData.id,
        filename: fileData.name,
        original_filename: fileData.name,
        file_type: fileType as FileType,
        file_size: fileData.size,
        uploaded_at: fileData.uploaded_at,
      });
    }
  }
  return result;
}

interface ProjectState {
  // State
  projects: Project[];
  currentProject: Project | null;
  files: ProjectFile[];
  downloads: GeneratedFile[];
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;

  // Progress tracking
  activeOperation: {
    type: 'export' | 'import' | null;
    progress: ProgressUpdate | null;
  };

  // Actions
  fetchProjects: () => Promise<void>;
  fetchProject: (projectId: string) => Promise<Project>;
  createProject: (data: { name: string; description?: string }) => Promise<Project>;
  updateProject: (projectId: string, data: Partial<Project>) => Promise<void>;
  deleteProject: (projectId: string) => Promise<void>;
  setCurrentProject: (project: Project | null) => void;

  // Config
  updateConfig: (projectId: string, config: Partial<ProjectConfig>) => Promise<void>;

  // Files
  uploadFile: (projectId: string, file: File, fileType?: string) => Promise<ProjectFile>;
  deleteFile: (projectId: string, fileId: string) => Promise<void>;
  fetchDownloads: (projectId: string) => Promise<void>;

  // Export
  startExport: (projectId: string, options?: Partial<ProjectConfig>) => Promise<void>;
  cancelExport: (projectId: string) => Promise<void>;

  // Import
  startImport: (
    projectId: string,
    workbook: File,
    options?: { worksheets?: string[]; push_to_api?: boolean }
  ) => Promise<void>;
  cancelImport: (projectId: string) => Promise<void>;
  validateWorkbook: (
    projectId: string,
    workbook: File
  ) => Promise<{
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
  }>;

  // Progress
  updateProgress: (progress: ProgressUpdate) => void;
  clearProgress: () => void;

  // Error handling
  clearError: () => void;
}

export const useProjectStore = create<ProjectState>((set, _get) => ({
  projects: [],
  currentProject: null,
  files: [],
  downloads: [],
  isLoading: false,
  isSaving: false,
  error: null,
  activeOperation: {
    type: null,
    progress: null,
  },

  fetchProjects: async () => {
    set({ isLoading: true, error: null });
    try {
      const projects = await projectsApi.list();
      set({ projects });
    } catch (error) {
      set({ error: 'Failed to load projects' });
    } finally {
      set({ isLoading: false });
    }
  },

  fetchProject: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const project = await projectsApi.get(projectId);
      // Convert backend files dictionary to array format
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const filesArray = convertFilesToArray((project as any).files);
      logInfo('[Store] Converted files from backend', { original: (project as any).files, converted: filesArray });
      set({
        currentProject: project,
        files: filesArray,
      });
      return project;
    } catch (error) {
      set({ error: 'Failed to load project' });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  createProject: async (data) => {
    set({ isSaving: true, error: null });
    try {
      const project = await projectsApi.create(data);
      set((state) => ({
        projects: [...state.projects, project],
      }));
      return project;
    } catch (error) {
      set({ error: 'Failed to create project' });
      throw error;
    } finally {
      set({ isSaving: false });
    }
  },

  updateProject: async (projectId, data) => {
    set({ isSaving: true, error: null });
    try {
      const project = await projectsApi.update(projectId, data);
      set((state) => ({
        projects: state.projects.map((p) => (p.id === projectId ? project : p)),
        currentProject: state.currentProject?.id === projectId ? project : state.currentProject,
      }));
    } catch (error) {
      set({ error: 'Failed to update project' });
      throw error;
    } finally {
      set({ isSaving: false });
    }
  },

  deleteProject: async (projectId) => {
    set({ isLoading: true, error: null });
    try {
      await projectsApi.delete(projectId);
      set((state) => ({
        projects: state.projects.filter((p) => p.id !== projectId),
        currentProject: state.currentProject?.id === projectId ? null : state.currentProject,
      }));
    } catch (error) {
      set({ error: 'Failed to delete project' });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  setCurrentProject: (project) => {
    // Convert backend files dictionary to array format
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const filesArray = project ? convertFilesToArray((project as any).files) : [];
    set({
      currentProject: project,
      files: filesArray,
    });
  },

  updateConfig: async (projectId, config) => {
    set({ isSaving: true, error: null });
    try {
      const updatedConfig = await projectsApi.updateConfig(projectId, config);
      set((state) => ({
        currentProject: state.currentProject
          ? { ...state.currentProject, config: updatedConfig }
          : null,
      }));
    } catch (error) {
      set({ error: 'Failed to update configuration' });
      throw error;
    } finally {
      set({ isSaving: false });
    }
  },

  uploadFile: async (projectId, file, fileType) => {
    logInfo(`[Store] Starting upload for file: ${file.name}`, { projectId, fileType, size: file.size });
    set({ isSaving: true, error: null });
    try {
      logInfo('[Store] Calling projectsApi.files.upload...');
      const uploadedFile = await projectsApi.files.upload(projectId, file, fileType);
      logInfo('[Store] Upload API returned successfully', uploadedFile);
      set((state) => {
        // Ensure files is an array before spreading
        const currentFiles = Array.isArray(state.files) ? state.files : [];
        logInfo('[Store] Current files array', { isArray: Array.isArray(state.files), length: currentFiles.length });
        return {
          files: [...currentFiles, uploadedFile],
          currentProject: state.currentProject
            ? {
                ...state.currentProject,
                file_count: (state.currentProject.file_count || 0) + 1,
              }
            : null,
        };
      });
      logInfo('[Store] State updated with new file');
      return uploadedFile;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      logError(`[Store] Upload failed: ${errorMessage}`, error);
      set({ error: 'Failed to upload file' });
      throw error;
    } finally {
      set({ isSaving: false });
    }
  },

  deleteFile: async (projectId, fileId) => {
    set({ isSaving: true, error: null });
    try {
      await projectsApi.files.delete(projectId, fileId);
      set((state) => {
        // Ensure files is an array before filtering
        const currentFiles = Array.isArray(state.files) ? state.files : [];
        return {
          files: currentFiles.filter((f) => f.id !== fileId),
          currentProject: state.currentProject
            ? {
                ...state.currentProject,
                file_count: Math.max((state.currentProject.file_count || 1) - 1, 0),
              }
            : null,
        };
      });
    } catch (error) {
      set({ error: 'Failed to delete file' });
      throw error;
    } finally {
      set({ isSaving: false });
    }
  },

  fetchDownloads: async (projectId) => {
    try {
      const downloads = await projectsApi.files.listDownloads(projectId);
      set({ downloads });
    } catch (error) {
      console.error('Failed to fetch downloads:', error);
    }
  },

  startExport: async (projectId, options) => {
    set({ error: null, activeOperation: { type: 'export', progress: null } });
    try {
      await projectsApi.export.start(projectId, options);
    } catch (error) {
      set({ error: 'Failed to start export', activeOperation: { type: null, progress: null } });
      throw error;
    }
  },

  cancelExport: async (projectId) => {
    try {
      await projectsApi.export.cancel(projectId);
    } catch (error) {
      console.error('Failed to cancel export:', error);
    }
  },

  startImport: async (projectId, workbook, options) => {
    set({ error: null, activeOperation: { type: 'import', progress: null } });
    try {
      await projectsApi.import.start(projectId, workbook, options);
    } catch (error) {
      set({ error: 'Failed to start import', activeOperation: { type: null, progress: null } });
      throw error;
    }
  },

  cancelImport: async (projectId) => {
    try {
      await projectsApi.import.cancel(projectId);
    } catch (error) {
      console.error('Failed to cancel import:', error);
    }
  },

  validateWorkbook: async (projectId, workbook) => {
    return projectsApi.import.validate(projectId, workbook);
  },

  updateProgress: (progress) => {
    set((state) => ({
      activeOperation: {
        ...state.activeOperation,
        progress,
      },
    }));
  },

  clearProgress: () => {
    set({
      activeOperation: { type: null, progress: null },
    });
  },

  clearError: () => set({ error: null }),
}));

export default useProjectStore;
