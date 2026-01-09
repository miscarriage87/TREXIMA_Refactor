/**
 * TREXIMA v4.0 - Projects API
 */

import apiClient from './client';
import { logInfo, logError } from '../components/DebugConsole';
import type {
  Project,
  ProjectConfig,
  ProjectFile,
  GeneratedFile,
  SFEndpointCategory,
  Locale,
  ECObject,
  FOObject,
  FOTranslationType,
} from '../types';

export const projectsApi = {
  /**
   * List all projects for current user
   */
  list: async (): Promise<Project[]> => {
    const response = await apiClient.get<{ projects: Project[] }>('/projects');
    return response.data.projects;
  },

  /**
   * Get a single project by ID
   */
  get: async (projectId: string): Promise<Project> => {
    const response = await apiClient.get<{ project: Project }>(`/projects/${projectId}`);
    return response.data.project;
  },

  /**
   * Create a new project
   */
  create: async (data: { name: string; description?: string }): Promise<Project> => {
    const response = await apiClient.post<{ project: Project }>('/projects', data);
    return response.data.project;
  },

  /**
   * Update a project
   */
  update: async (projectId: string, data: Partial<Project>): Promise<Project> => {
    const response = await apiClient.put<{ project: Project }>(`/projects/${projectId}`, data);
    return response.data.project;
  },

  /**
   * Delete a project
   */
  delete: async (projectId: string): Promise<void> => {
    await apiClient.delete(`/projects/${projectId}`);
  },

  /**
   * Get project configuration
   */
  getConfig: async (projectId: string): Promise<ProjectConfig> => {
    const response = await apiClient.get<{ config: ProjectConfig }>(`/projects/${projectId}/config`);
    return response.data.config;
  },

  /**
   * Update project configuration
   */
  updateConfig: async (projectId: string, config: Partial<ProjectConfig>): Promise<ProjectConfig> => {
    const response = await apiClient.put<{ config: ProjectConfig }>(`/projects/${projectId}/config`, config);
    return response.data.config;
  },

  // File operations
  files: {
    /**
     * Upload a file to a project
     */
    upload: async (projectId: string, file: File, fileType?: string): Promise<ProjectFile> => {
      logInfo(`Starting file upload: ${file.name} (${file.size} bytes)`, { projectId, fileType });

      const formData = new FormData();
      formData.append('file', file);
      if (fileType) {
        formData.append('file_type', fileType);
      }

      try {
        const response = await apiClient.post<{
          uploaded: Array<{
            id: string;
            file_type: string;
            original_name: string;
            file_size: number;
          }>;
          errors?: Array<{ filename: string; error: string }>;
        }>(
          `/projects/${projectId}/files`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        );

        logInfo(`Upload response received`, response.data);

        // Check for errors
        if (response.data.errors && response.data.errors.length > 0) {
          const errorMsg = response.data.errors[0].error;
          logError(`Upload error from server: ${errorMsg}`, response.data.errors);
          throw new Error(errorMsg);
        }

        // Backend returns array of uploaded files, get the first one
        const uploaded = response.data.uploaded;
        if (!uploaded || uploaded.length === 0) {
          logError('No file in upload response', response.data);
          throw new Error('No file was uploaded');
        }

        // Convert backend response to ProjectFile format
        const uploadedFile = uploaded[0];
        const result: ProjectFile = {
          id: uploadedFile.id,
          filename: uploadedFile.original_name,
          original_filename: uploadedFile.original_name,
          file_type: uploadedFile.file_type as ProjectFile['file_type'],
          file_size: uploadedFile.file_size,
          uploaded_at: new Date().toISOString(),
        };

        logInfo(`File upload successful: ${uploadedFile.original_name}`, result);
        return result;
      } catch (error) {
        logError(`File upload failed: ${file.name}`, error);
        throw error;
      }
    },

    /**
     * Delete a file from a project
     */
    delete: async (projectId: string, fileId: string): Promise<void> => {
      await apiClient.delete(`/projects/${projectId}/files/${fileId}`);
    },

    /**
     * List generated/downloadable files
     */
    listDownloads: async (projectId: string): Promise<GeneratedFile[]> => {
      const response = await apiClient.get<{ files: GeneratedFile[] }>(
        `/projects/${projectId}/downloads`
      );
      return response.data.files;
    },

    /**
     * Get download URL for a generated file
     */
    getDownloadUrl: async (projectId: string, fileId: string): Promise<string> => {
      const response = await apiClient.get<{ download_url: string }>(
        `/projects/${projectId}/download/${fileId}`
      );
      return response.data.download_url;
    },
  },

  // SF Connection
  connection: {
    /**
     * Test SF connection
     */
    test: async (
      projectId: string,
      connection: { endpoint: string; company_id: string; username: string; password: string }
    ): Promise<{ success: boolean; message?: string; locales?: string[] }> => {
      // Backend expects endpoint_url, not endpoint
      const payload = {
        endpoint_url: connection.endpoint,
        company_id: connection.company_id,
        username: connection.username,
        password: connection.password,
      };
      const response = await apiClient.post(`/projects/${projectId}/connect`, payload);
      return response.data;
    },

    /**
     * Get available SF endpoints
     */
    getEndpoints: async (): Promise<Record<string, SFEndpointCategory>> => {
      const response = await apiClient.get<{ endpoints: Record<string, SFEndpointCategory> }>(
        '/projects/sf-endpoints'
      );
      return response.data.endpoints;
    },

    /**
     * Get available locales for a connected project
     */
    getLocales: async (projectId: string): Promise<Locale[]> => {
      const response = await apiClient.get<{ locales: Locale[] }>(
        `/projects/${projectId}/locales`
      );
      return response.data.locales;
    },

    /**
     * Fetch dynamic SF objects from the connected instance
     */
    getSFObjects: async (projectId: string): Promise<{
      success: boolean;
      data?: {
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
      };
      error?: string;
    }> => {
      const response = await apiClient.get(`/projects/${projectId}/sf-objects`);
      return response.data;
    },

    /**
     * Fetch picklist details from SF
     */
    getPicklists: async (
      projectId: string,
      type: 'mdf' | 'legacy' = 'mdf',
      limit: number = 100,
      offset: number = 0
    ): Promise<{
      success: boolean;
      type: string;
      total: number;
      picklists: Array<{ id: string; name: string; value_count?: number; option_count?: number }>;
    }> => {
      const response = await apiClient.get(
        `/projects/${projectId}/sf-picklists?type=${type}&limit=${limit}&offset=${offset}`
      );
      return response.data;
    },
  },

  // Operation status (for polling)
  status: {
    /**
     * Get current operation status for project
     */
    get: async (projectId: string): Promise<{
      has_active_operation: boolean;
      operation?: {
        type: string;
        progress?: number;
        message?: string;
      };
    }> => {
      const response = await apiClient.get(`/projects/${projectId}/status`);
      return response.data;
    },
  },

  // Export operations
  export: {
    /**
     * Start export operation
     */
    start: async (projectId: string, options?: Partial<ProjectConfig>): Promise<void> => {
      await apiClient.post(`/projects/${projectId}/export`, options);
    },

    /**
     * Get export status
     */
    getStatus: async (projectId: string): Promise<{
      status: string;
      is_active: boolean;
      latest_export?: GeneratedFile;
    }> => {
      const response = await apiClient.get(`/projects/${projectId}/export/status`);
      return response.data;
    },

    /**
     * Cancel export operation
     */
    cancel: async (projectId: string): Promise<void> => {
      await apiClient.post(`/projects/${projectId}/export/cancel`);
    },

    /**
     * Get available EC objects
     */
    getECObjects: async (): Promise<ECObject[]> => {
      const response = await apiClient.get<{ ec_objects: ECObject[] }>('/export/ec-objects');
      return response.data.ec_objects;
    },

    /**
     * Get available FO objects
     */
    getFOObjects: async (): Promise<FOObject[]> => {
      const response = await apiClient.get<{ fo_objects: FOObject[] }>('/export/fo-objects');
      return response.data.fo_objects;
    },

    /**
     * Get available FO translation types
     */
    getFOTranslationTypes: async (): Promise<FOTranslationType[]> => {
      const response = await apiClient.get<{ fo_translation_types: FOTranslationType[] }>(
        '/export/fo-translation-types'
      );
      return response.data.fo_translation_types;
    },
  },

  // Import operations
  import: {
    /**
     * Start import operation
     */
    start: async (
      projectId: string,
      workbook: File,
      options?: { worksheets?: string[]; push_to_api?: boolean }
    ): Promise<void> => {
      const formData = new FormData();
      formData.append('workbook', workbook);
      if (options?.worksheets) {
        formData.append('worksheets', JSON.stringify(options.worksheets));
      }

      const params = new URLSearchParams();
      if (options?.push_to_api) {
        params.append('push_to_api', 'true');
      }

      await apiClient.post(
        `/projects/${projectId}/import${params.toString() ? `?${params}` : ''}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
    },

    /**
     * Get import status
     */
    getStatus: async (projectId: string): Promise<{
      status: string;
      is_active: boolean;
      generated_files: GeneratedFile[];
    }> => {
      const response = await apiClient.get(`/projects/${projectId}/import/status`);
      return response.data;
    },

    /**
     * Cancel import operation
     */
    cancel: async (projectId: string): Promise<void> => {
      await apiClient.post(`/projects/${projectId}/import/cancel`);
    },

    /**
     * Validate workbook before import
     */
    validate: async (projectId: string, workbook: File): Promise<{
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
    }> => {
      const formData = new FormData();
      formData.append('workbook', workbook);

      const response = await apiClient.post(
        `/projects/${projectId}/import/validate`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      return response.data;
    },
  },
};

export default projectsApi;
