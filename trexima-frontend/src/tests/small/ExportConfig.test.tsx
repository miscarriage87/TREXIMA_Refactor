/**
 * SMALL Scale Tests - ExportConfig Component
 *
 * Unit tests for the ExportConfig component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ExportConfig from '../../components/project/ExportConfig';
import { useProjectStore } from '../../store/projectStore';
import projectsApi from '../../api/projects';
import { mockProject, mockECObjects, mockFOTranslationTypes } from '../mockData';

// Mock the stores and API
vi.mock('../../store/projectStore');
vi.mock('../../api/projects');

describe('ExportConfig Component - SMALL Scale', () => {
  const mockUpdateConfig = vi.fn();
  const projectId = 'proj-123';

  beforeEach(() => {
    vi.clearAllMocks();

    // Setup store mock
    vi.mocked(useProjectStore).mockReturnValue({
      currentProject: mockProject,
      updateConfig: mockUpdateConfig,
      isSaving: false,
    } as any);

    // Setup API mocks
    vi.mocked(projectsApi.export.getECObjects).mockResolvedValue(mockECObjects);
    vi.mocked(projectsApi.export.getFOTranslationTypes).mockResolvedValue(mockFOTranslationTypes);
  });

  describe('Rendering', () => {
    it('should render export configuration header', () => {
      render(<ExportConfig projectId={projectId} />);

      expect(screen.getByText('Export Configuration')).toBeInTheDocument();
      expect(screen.getByText(/Select languages and configure/i)).toBeInTheDocument();
    });

    it('should show loading state initially', async () => {
      render(<ExportConfig projectId={projectId} />);

      const loader = screen.getByRole('progressbar', { hidden: true }) || document.querySelector('.animate-spin');
      expect(loader).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText('Languages')).toBeInTheDocument();
      });
    });

    it('should load and display EC objects', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        expect(projectsApi.export.getECObjects).toHaveBeenCalled();
      });
    });

    it('should load and display FO translation types', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        expect(projectsApi.export.getFOTranslationTypes).toHaveBeenCalled();
      });
    });
  });

  describe('Language Selection', () => {
    it('should display language groups', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        expect(screen.getByText('English')).toBeInTheDocument();
        expect(screen.getByText('German')).toBeInTheDocument();
        expect(screen.getByText('French')).toBeInTheDocument();
      });
    });

    it('should have en_US pre-selected and disabled', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        const enUSCheckbox = screen.getByLabelText(/English \(US\)/i) as HTMLInputElement;
        expect(enUSCheckbox).toBeChecked();
        expect(enUSCheckbox).toBeDisabled();
      });
    });

    it('should load selected locales from project config', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        const deDE = screen.getByLabelText(/German \(Germany\)/i) as HTMLInputElement;
        const frFR = screen.getByLabelText(/French \(France\)/i) as HTMLInputElement;

        expect(deDE).toBeChecked();
        expect(frFR).toBeChecked();
      });
    });

    it('should toggle locale selection', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        const esES = screen.getByLabelText(/Spanish \(Spain\)/i) as HTMLInputElement;
        expect(esES).not.toBeChecked();

        fireEvent.click(esES);
        expect(esES).toBeChecked();
      });
    });

    it('should select all locales', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        const selectAllBtn = screen.getByText('Select All');
        fireEvent.click(selectAllBtn);
      });

      // Check that multiple locales are selected
      const checkboxes = screen.getAllByRole('checkbox', { checked: true });
      expect(checkboxes.length).toBeGreaterThan(10);
    });

    it('should deselect all locales except en_US', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        const deselectAllBtn = screen.getByText('Deselect All');
        fireEvent.click(deselectAllBtn);
      });

      const checkedBoxes = screen.getAllByRole('checkbox', { checked: true });
      expect(checkedBoxes).toHaveLength(1); // Only en_US should remain
    });

    it('should display selected locale count', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        expect(screen.getByText(/Selected: 3 languages/i)).toBeInTheDocument();
      });
    });
  });

  describe('Export Options', () => {
    it('should display all export option checkboxes', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        expect(screen.getByText('Export Picklists')).toBeInTheDocument();
        expect(screen.getByText('Export MDF Objects')).toBeInTheDocument();
        expect(screen.getByText('Export Foundation Object Translations')).toBeInTheDocument();
      });
    });

    it('should disable API options when not connected', async () => {
      const projectWithoutConnection = {
        ...mockProject,
        config: { ...mockProject.config, sf_connection: { ...mockProject.config.sf_connection!, connected: false } },
      };

      vi.mocked(useProjectStore).mockReturnValue({
        currentProject: projectWithoutConnection,
        updateConfig: mockUpdateConfig,
        isSaving: false,
      } as any);

      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        const picklistsCheckbox = screen.getByRole('checkbox', { name: /Export Picklists/i }) as HTMLInputElement;
        expect(picklistsCheckbox).toBeDisabled();
      });
    });

    it('should load export options from project config', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        const picklistsCheckbox = screen.getByRole('checkbox', { name: /Export Picklists/i }) as HTMLInputElement;
        const mdfCheckbox = screen.getByRole('checkbox', { name: /Export MDF Objects/i }) as HTMLInputElement;
        const foCheckbox = screen.getByRole('checkbox', { name: /Export Foundation Object/i }) as HTMLInputElement;

        expect(picklistsCheckbox).toBeChecked();
        expect(mdfCheckbox).toBeChecked();
        expect(foCheckbox).toBeChecked();
      });
    });

    it('should show EC objects selection when MDF is enabled', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        expect(screen.getByText(/Select EC Objects/i)).toBeInTheDocument();
        expect(screen.getByText('Personal Information')).toBeInTheDocument();
        expect(screen.getByText('Email Information')).toBeInTheDocument();
      });
    });

    it('should show FO types selection when FO is enabled', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        expect(screen.getByText(/Select FO Translation Types/i)).toBeInTheDocument();
        expect(screen.getByText('Event Reasons')).toBeInTheDocument();
        expect(screen.getByText('Locations')).toBeInTheDocument();
      });
    });

    it('should toggle EC object selection', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        const perPersonalCheckbox = screen.getByLabelText(/Personal Information/i) as HTMLInputElement;
        expect(perPersonalCheckbox).toBeChecked(); // From config

        fireEvent.click(perPersonalCheckbox);
        expect(perPersonalCheckbox).not.toBeChecked();
      });
    });

    it('should toggle FO type selection', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        const eventReasonCheckbox = screen.getByLabelText(/Event Reasons/i) as HTMLInputElement;
        expect(eventReasonCheckbox).toBeChecked(); // From config

        fireEvent.click(eventReasonCheckbox);
        expect(eventReasonCheckbox).not.toBeChecked();
      });
    });
  });

  describe('Configuration Summary', () => {
    it('should display configuration summary', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        expect(screen.getByText(/Configuration Summary:/i)).toBeInTheDocument();
        expect(screen.getByText(/3 languages selected/i)).toBeInTheDocument();
        expect(screen.getByText(/Picklists enabled/i)).toBeInTheDocument();
      });
    });

    it('should show EC object count in summary', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        expect(screen.getByText(/3 EC objects selected/i)).toBeInTheDocument();
      });
    });

    it('should show FO type count in summary', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        expect(screen.getByText(/3 FO translation types selected/i)).toBeInTheDocument();
      });
    });
  });

  describe('Save Configuration', () => {
    it('should have save button', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        expect(screen.getByText('Save Configuration')).toBeInTheDocument();
      });
    });

    it('should call updateConfig on save', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        const saveBtn = screen.getByText('Save Configuration');
        fireEvent.click(saveBtn);
      });

      await waitFor(() => {
        expect(mockUpdateConfig).toHaveBeenCalledWith(projectId, expect.objectContaining({
          locales: expect.arrayContaining(['en_US', 'de_DE', 'fr_FR']),
          export_picklists: true,
          export_mdf_objects: true,
          export_fo_translations: true,
          ec_objects: expect.arrayContaining(['PerPersonal', 'PerEmail', 'EmpJob']),
          fo_translation_types: expect.arrayContaining(['eventReason', 'location', 'payComponent']),
        }));
      });
    });

    it('should show success message after save', async () => {
      mockUpdateConfig.mockResolvedValue(undefined);

      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        const saveBtn = screen.getByText('Save Configuration');
        fireEvent.click(saveBtn);
      });

      await waitFor(() => {
        expect(screen.getByText(/Configuration saved successfully/i)).toBeInTheDocument();
      });
    });

    it('should show saving state', async () => {
      vi.mocked(useProjectStore).mockReturnValue({
        currentProject: mockProject,
        updateConfig: mockUpdateConfig,
        isSaving: true,
      } as any);

      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        expect(screen.getByText('Saving...')).toBeInTheDocument();
      });
    });

    it('should clear EC objects when MDF is disabled', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        const mdfCheckbox = screen.getByRole('checkbox', { name: /Export MDF Objects/i });
        fireEvent.click(mdfCheckbox); // Disable MDF
      });

      await waitFor(() => {
        const saveBtn = screen.getByText('Save Configuration');
        fireEvent.click(saveBtn);
      });

      await waitFor(() => {
        expect(mockUpdateConfig).toHaveBeenCalledWith(projectId, expect.objectContaining({
          ec_objects: [],
        }));
      });
    });

    it('should clear FO types when FO is disabled', async () => {
      render(<ExportConfig projectId={projectId} />);

      await waitFor(() => {
        const foCheckbox = screen.getByRole('checkbox', { name: /Export Foundation Object/i });
        fireEvent.click(foCheckbox); // Disable FO
      });

      await waitFor(() => {
        const saveBtn = screen.getByText('Save Configuration');
        fireEvent.click(saveBtn);
      });

      await waitFor(() => {
        expect(mockUpdateConfig).toHaveBeenCalledWith(projectId, expect.objectContaining({
          fo_translation_types: [],
        }));
      });
    });
  });
});
