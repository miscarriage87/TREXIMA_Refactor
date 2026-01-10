/**
 * TREXIMA v2.0 - TypeScript Type Definitions
 */

// =============================================================================
// USER & AUTH TYPES
// =============================================================================

export interface User {
  id: string;
  email: string;
  display_name: string;
  is_admin: boolean;
  created_at: string;
  last_login: string;
  project_count: number;
}

export interface AuthConfig {
  is_initialized: boolean;
  login_url?: string;
  logout_url?: string;
}

// =============================================================================
// PROJECT TYPES
// =============================================================================

export type ProjectStatus = 'draft' | 'configured' | 'exporting' | 'exported' | 'importing' | 'imported';

export type FileType = 'sdm' | 'cdm' | 'ec_sdm' | 'ec_cdm' | 'picklist';

export interface Project {
  id: string;
  name: string;
  description?: string;
  status: ProjectStatus;
  config: ProjectConfig;
  created_at: string;
  updated_at: string;
  file_count: number;
  files?: ProjectFile[];
}

/**
 * Backend API returns files as a dictionary format.
 * This type represents the raw API response before conversion.
 */
export interface BackendFileDict {
  id: string;
  name: string;
  size: number;
  uploaded_at: string;
}

export interface BackendProject extends Omit<Project, 'files'> {
  files?: Record<string, BackendFileDict | null>;
}

export interface ProjectConfig {
  locales: string[];
  sf_connection?: SFConnection;
  // Picklist exports (separated by type)
  export_mdf_picklists: boolean;
  export_legacy_picklists: boolean;
  // Legacy properties (for backward compatibility)
  export_picklists?: boolean;
  export_mdf_objects?: boolean;
  export_fo_translations?: boolean;
  // Selected objects
  fo_translation_types: string[];
  ec_objects: string[];
  fo_objects: string[];
  mdf_objects: string[];
}

export interface SFConnection {
  endpoint: string;
  company_id: string;
  username?: string;
  password?: string;
  connected?: boolean;
  last_tested?: string;
}

export interface ProjectFile {
  id: string;
  filename: string;
  original_filename: string;
  file_type: FileType;
  file_size: number;
  uploaded_at: string;
}

export interface GeneratedFile {
  id: string;
  filename: string;
  file_type: 'translation_workbook' | 'import_xml' | 'changelog_workbook' | 'import_log';
  file_size: number;
  created_at: string;
  expires_at: string;
  download_url?: string;
}

// =============================================================================
// SF API TYPES
// =============================================================================

export interface SFEndpoint {
  id: string;
  name: string;
  url: string;
  region: string;
}

export interface SFEndpointCategory {
  label: string;
  endpoints: SFEndpoint[];
}

export interface ECObject {
  id: string;
  name: string;
  description: string;
}

export interface FOObject {
  id: string;
  name: string;
  description: string;
  translatable: boolean;
}

export interface FOTranslationType {
  id: string;
  name: string;
  object: string;
  field: string;
  description: string;
}

export interface Locale {
  code: string;
  name: string;
}

// =============================================================================
// WEBSOCKET / PROGRESS TYPES
// =============================================================================

export type OperationType = 'export' | 'import' | 'connect';

export interface ProgressStep {
  step: number;
  name: string;
  description: string;
}

export interface ProgressUpdate {
  project_id: string;
  operation: OperationType;
  step: number;
  total_steps: number;
  step_name: string;
  percent: number;
  message: string;
  details?: Record<string, unknown>;
  timestamp: string;
}

export interface OperationResult {
  project_id: string;
  operation: OperationType;
  success: boolean;
  result?: Record<string, unknown>;
  error?: string;
  timestamp: string;
}

// =============================================================================
// API RESPONSE TYPES
// =============================================================================

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy';
  app: string;
  version: string;
  checks: {
    database: string;
    storage: string;
    auth: string;
  };
}

// =============================================================================
// ADMIN TYPES
// =============================================================================

export interface SystemStats {
  users: {
    total: number;
    admins: number;
    active_7d: number;
    active_30d: number;
  };
  projects: {
    total: number;
    by_status: Record<ProjectStatus, number>;
  };
  files: {
    uploaded: number;
    generated: number;
    expired: number;
  };
  storage: {
    total_files: number;
    total_size: number;
  };
  operations: {
    active: number;
    details: Record<string, unknown>;
  };
  generated_at: string;
}
