/**
 * Mock Data for Tests
 */

import type {
  Project,
  ProjectConfig,
  User,
  ECObject,
  FOTranslationType,
  ProjectFile,
  GeneratedFile,
} from '../types';

export const mockUser: User = {
  id: 'user-123',
  email: 'test@example.com',
  display_name: 'Test User',
  is_admin: false,
  created_at: '2026-01-01T00:00:00Z',
  last_login: '2026-01-08T00:00:00Z',
  project_count: 2,
};

export const mockAdminUser: User = {
  ...mockUser,
  id: 'admin-123',
  email: 'admin@example.com',
  display_name: 'Admin User',
  is_admin: true,
};

export const mockProjectConfig: ProjectConfig = {
  locales: ['en_US', 'de_DE', 'fr_FR'],
  sf_connection: {
    endpoint: 'https://api2.successfactors.com/odata/v2',
    company_id: 'SFPART123456',
    username: 'admin@company.com',
    connected: true,
    last_tested: '2026-01-08T10:00:00Z',
  },
  export_picklists: true,
  export_mdf_objects: true,
  export_fo_translations: true,
  ec_objects: ['PerPersonal', 'PerEmail', 'EmpJob'],
  fo_translation_types: ['eventReason', 'location', 'payComponent'],
  fo_objects: [],
};

export const mockProject: Project = {
  id: 'proj-123',
  name: 'Test Project',
  description: 'Test project description',
  status: 'draft',
  config: mockProjectConfig,
  created_at: '2026-01-05T00:00:00Z',
  updated_at: '2026-01-08T00:00:00Z',
  file_count: 2,
  files: [],
};

export const mockProjectFile: ProjectFile = {
  id: 'file-123',
  filename: 'test_sdm.xml',
  original_filename: 'EC_Standard_Data_Model.xml',
  file_type: 'sdm',
  file_size: 1024000,
  uploaded_at: '2026-01-08T09:00:00Z',
};

export const mockGeneratedFile: GeneratedFile = {
  id: 'gen-123',
  filename: 'translation_workbook_20260108.xlsx',
  file_type: 'translation_workbook',
  file_size: 5242880,
  created_at: '2026-01-08T10:30:00Z',
  expires_at: '2026-04-08T10:30:00Z',
  download_url: '/api/projects/proj-123/download/gen-123',
};

export const mockECObjects: ECObject[] = [
  {
    id: 'PerPersonal',
    name: 'Personal Information',
    description: 'Basic personal data (name, DOB, gender, etc.)',
  },
  {
    id: 'PerEmail',
    name: 'Email Information',
    description: 'Email addresses',
  },
  {
    id: 'EmpJob',
    name: 'Job Information',
    description: 'Employment and job data',
  },
];

export const mockFOTranslationTypes: FOTranslationType[] = [
  {
    id: 'eventReason',
    name: 'Event Reasons',
    object: 'FOEventReason',
    field: 'name',
    description: 'Reasons for HR events (hire, termination, transfer, etc.)',
  },
  {
    id: 'location',
    name: 'Locations',
    object: 'FOLocation',
    field: 'name',
    description: 'Physical work locations',
  },
  {
    id: 'payComponent',
    name: 'Pay Components',
    object: 'FOPayComponent',
    field: 'name',
    description: 'Compensation pay components',
  },
];

export const mockValidationResult = {
  valid: true,
  filename: 'translated_workbook.xlsx',
  sheets: {
    all: ['EC_SDM_en_US', 'EC_SDM_de_DE', 'Picklists', 'Summary'],
    datamodel: ['EC_SDM_en_US', 'EC_SDM_de_DE'],
    pm_templates: ['Picklists'],
    gm_templates: [],
    other: ['Summary'],
  },
  total_sheets: 4,
};
