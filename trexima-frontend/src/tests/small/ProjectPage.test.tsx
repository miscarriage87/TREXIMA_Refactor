/**
 * SMALL Scale Tests - ProjectPage Component (Updated)
 *
 * Unit tests focusing on the NEW 5-section workflow
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ProjectPage from '../../pages/ProjectPage';
import { useProjectStore } from '../../store/projectStore';
import wsService from '../../api/websocket';
import { mockProject } from '../mockData';

// Mock dependencies
vi.mock('../../store/projectStore');
vi.mock('../../api/websocket');
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ projectId: 'proj-123' }),
  };
});

// Mock child components
vi.mock('../../components/project/FileUploadZone', () => ({
  default: () => <div data-testid="file-upload-zone">FileUploadZone</div>,
}));

vi.mock('../../components/project/ConnectionConfig', () => ({
  default: () => <div data-testid="connection-config">ConnectionConfig</div>,
}));

vi.mock('../../components/project/ExportConfig', () => ({
  default: () => <div data-testid="export-config">ExportConfig</div>,
}));

vi.mock('../../components/project/ExportSummary', () => ({
  default: () => <div data-testid="export-summary">ExportSummary</div>,
}));

vi.mock('../../components/project/ImportSummary', () => ({
  default: () => <div data-testid="import-summary">ImportSummary</div>,
}));

vi.mock('../../components/project/ProgressOverlay', () => ({
  default: () => <div data-testid="progress-overlay">ProgressOverlay</div>,
}));

describe('ProjectPage Component - SMALL Scale (5 Sections)', () => {
  const mockFetchProject = vi.fn();
  const mockFetchDownloads = vi.fn();
  const mockUpdateProgress = vi.fn();
  const mockClearProgress = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // Setup store mock
    vi.mocked(useProjectStore).mockReturnValue({
      currentProject: mockProject,
      fetchProject: mockFetchProject,
      fetchDownloads: mockFetchDownloads,
      updateProgress: mockUpdateProgress,
      clearProgress: mockClearProgress,
      isLoading: false,
      error: null,
      activeOperation: {
        type: null,
        progress: null,
      },
    } as any);

    // Setup WebSocket mock
    vi.mocked(wsService.connect).mockResolvedValue(undefined);
    vi.mocked(wsService.subscribeToProject).mockReturnValue(undefined);
    vi.mocked(wsService.onProgress).mockReturnValue(() => {});
    vi.mocked(wsService.onComplete).mockReturnValue(() => {});
    vi.mocked(wsService.unsubscribeFromProject).mockReturnValue(undefined);
  });

  describe('Rendering - All 5 Sections', () => {
    it('should render project page with header', async () => {
      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Test Project')).toBeInTheDocument();
      });
    });

    it('should display all 5 workflow sections', async () => {
      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Data Models')).toBeInTheDocument();
        expect(screen.getByText('SF Connection')).toBeInTheDocument();
        expect(screen.getByText('Configuration')).toBeInTheDocument();
        expect(screen.getByText('Export')).toBeInTheDocument();
        expect(screen.getByText('Import')).toBeInTheDocument();
      });
    });

    it('should display section descriptions', async () => {
      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Upload XML files')).toBeInTheDocument();
        expect(screen.getByText('Connect to SF')).toBeInTheDocument();
        expect(screen.getByText('Select options')).toBeInTheDocument();
        expect(screen.getByText('Generate workbook')).toBeInTheDocument();
        expect(screen.getByText('Import translations')).toBeInTheDocument();
      });
    });

    it('should render section icons', async () => {
      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        // Icons are rendered via Lucide, check for section presence
        const sections = screen.getAllByRole('button');
        expect(sections.length).toBeGreaterThanOrEqual(5);
      });
    });

    it('should number sections 1-5', async () => {
      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('1')).toBeInTheDocument();
        expect(screen.getByText('2')).toBeInTheDocument();
        expect(screen.getByText('3')).toBeInTheDocument();
        expect(screen.getByText('4')).toBeInTheDocument();
        expect(screen.getByText('5')).toBeInTheDocument();
      });
    });
  });

  describe('Section Navigation', () => {
    it('should start with Data Models section active', async () => {
      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('file-upload-zone')).toBeInTheDocument();
      });
    });

    it('should switch to SF Connection section', async () => {
      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const connectionButton = screen.getByText('SF Connection').closest('button');
        fireEvent.click(connectionButton!);
      });

      await waitFor(() => {
        expect(screen.getByTestId('connection-config')).toBeInTheDocument();
      });
    });

    it('should switch to Configuration section (NEW)', async () => {
      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const configButton = screen.getByText('Configuration').closest('button');
        fireEvent.click(configButton!);
      });

      await waitFor(() => {
        expect(screen.getByTestId('export-config')).toBeInTheDocument();
      });
    });

    it('should switch to Export section', async () => {
      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const exportButton = screen.getByText('Export').closest('button');
        fireEvent.click(exportButton!);
      });

      await waitFor(() => {
        expect(screen.getByTestId('export-summary')).toBeInTheDocument();
      });
    });

    it('should switch to Import section (NEW)', async () => {
      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const importButton = screen.getByText('Import').closest('button');
        fireEvent.click(importButton!);
      });

      await waitFor(() => {
        expect(screen.getByTestId('import-summary')).toBeInTheDocument();
      });
    });

    it('should hide other sections when one is active', async () => {
      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      // Initially on Data Models
      await waitFor(() => {
        expect(screen.getByTestId('file-upload-zone')).toBeInTheDocument();
        expect(screen.queryByTestId('connection-config')).not.toBeInTheDocument();
      });

      // Switch to Connection
      const connectionButton = screen.getByText('SF Connection').closest('button');
      fireEvent.click(connectionButton!);

      await waitFor(() => {
        expect(screen.queryByTestId('file-upload-zone')).not.toBeInTheDocument();
        expect(screen.getByTestId('connection-config')).toBeInTheDocument();
      });
    });
  });

  describe('Section Status', () => {
    it('should show Data Models section as complete when files uploaded', async () => {
      const projectWithFiles = {
        ...mockProject,
        file_count: 3,
      };

      vi.mocked(useProjectStore).mockReturnValue({
        currentProject: projectWithFiles,
        fetchProject: mockFetchProject,
        fetchDownloads: mockFetchDownloads,
        updateProgress: mockUpdateProgress,
        clearProgress: mockClearProgress,
        isLoading: false,
        error: null,
        activeOperation: { type: null, progress: null },
      } as any);

      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const section = screen.getByText('Data Models').closest('button');
        expect(section).toHaveClass('border-green-200', 'bg-green-50', 'text-green-700');
      });
    });

    it('should show SF Connection as complete when connected', async () => {
      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const section = screen.getByText('SF Connection').closest('button');
        // Check for complete status (mockProject has connection)
        expect(section).toHaveClass('border-green-200');
      });
    });

    it('should show Configuration as complete when status is not draft', async () => {
      const configuredProject = {
        ...mockProject,
        status: 'configured' as const,
      };

      vi.mocked(useProjectStore).mockReturnValue({
        currentProject: configuredProject,
        fetchProject: mockFetchProject,
        fetchDownloads: mockFetchDownloads,
        updateProgress: mockUpdateProgress,
        clearProgress: mockClearProgress,
        isLoading: false,
        error: null,
        activeOperation: { type: null, progress: null },
      } as any);

      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const section = screen.getByText('Configuration').closest('button');
        expect(section).toHaveClass('border-green-200');
      });
    });

    it('should show Export as complete when exported', async () => {
      const exportedProject = {
        ...mockProject,
        status: 'exported' as const,
      };

      vi.mocked(useProjectStore).mockReturnValue({
        currentProject: exportedProject,
        fetchProject: mockFetchProject,
        fetchDownloads: mockFetchDownloads,
        updateProgress: mockUpdateProgress,
        clearProgress: mockClearProgress,
        isLoading: false,
        error: null,
        activeOperation: { type: null, progress: null },
      } as any);

      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const section = screen.getByText('Export').closest('button');
        expect(section).toHaveClass('border-green-200');
      });
    });

    it('should show Import as complete when imported (NEW)', async () => {
      const importedProject = {
        ...mockProject,
        status: 'imported' as const,
      };

      vi.mocked(useProjectStore).mockReturnValue({
        currentProject: importedProject,
        fetchProject: mockFetchProject,
        fetchDownloads: mockFetchDownloads,
        updateProgress: mockUpdateProgress,
        clearProgress: mockClearProgress,
        isLoading: false,
        error: null,
        activeOperation: { type: null, progress: null },
      } as any);

      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const section = screen.getByText('Import').closest('button');
        expect(section).toHaveClass('border-green-200');
      });
    });

    it('should show active section with blue styling', async () => {
      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        const dataModelsSection = screen.getByText('Data Models').closest('button');
        expect(dataModelsSection).toHaveClass('border-sap-blue-500', 'bg-sap-blue-50');
      });
    });
  });

  describe('WebSocket Integration', () => {
    it('should connect to WebSocket on mount', async () => {
      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(wsService.connect).toHaveBeenCalled();
        expect(wsService.subscribeToProject).toHaveBeenCalledWith('proj-123');
      });
    });

    it('should subscribe to progress updates', async () => {
      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(wsService.onProgress).toHaveBeenCalledWith('proj-123', expect.any(Function));
      });
    });

    it('should subscribe to completion events', async () => {
      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(wsService.onComplete).toHaveBeenCalledWith('proj-123', expect.any(Function));
      });
    });

    it('should unsubscribe on unmount', async () => {
      const { unmount } = render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(wsService.subscribeToProject).toHaveBeenCalled();
      });

      unmount();

      expect(wsService.unsubscribeFromProject).toHaveBeenCalledWith('proj-123');
    });

    it('should update progress when received', async () => {
      let progressCallback: any;
      vi.mocked(wsService.onProgress).mockImplementation((projectId, callback) => {
        progressCallback = callback;
        return () => {};
      });

      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(wsService.onProgress).toHaveBeenCalled();
      });

      // Simulate progress update
      const progressUpdate = {
        operation: 'export' as const,
        step: 2,
        step_name: 'Processing files',
        percent: 50,
        message: 'Processing 2 of 4 files',
        total_steps: 4,
        timestamp: new Date().toISOString(),
      };

      if (progressCallback) {
        progressCallback(progressUpdate);
        expect(mockUpdateProgress).toHaveBeenCalledWith(progressUpdate);
      }
    });

    it('should refresh project on completion', async () => {
      let completeCallback: any;
      vi.mocked(wsService.onComplete).mockImplementation((projectId, callback) => {
        completeCallback = callback;
        return () => {};
      });

      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(wsService.onComplete).toHaveBeenCalled();
      });

      // Simulate completion
      const result = {
        success: true,
        message: 'Export completed successfully',
        generated_files: [],
      };

      if (completeCallback) {
        completeCallback(result);
        expect(mockClearProgress).toHaveBeenCalled();
        expect(mockFetchProject).toHaveBeenCalledWith('proj-123');
      }
    });
  });

  describe('Progress Overlay', () => {
    it('should render progress overlay', async () => {
      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('progress-overlay')).toBeInTheDocument();
      });
    });

    it('should show progress when operation is active', async () => {
      const progressUpdate = {
        operation: 'export' as const,
        step: 2,
        step_name: 'Extracting translations',
        percent: 60,
        message: 'Processing...',
        total_steps: 5,
        timestamp: new Date().toISOString(),
      };

      vi.mocked(useProjectStore).mockReturnValue({
        currentProject: mockProject,
        fetchProject: mockFetchProject,
        fetchDownloads: mockFetchDownloads,
        updateProgress: mockUpdateProgress,
        clearProgress: mockClearProgress,
        isLoading: false,
        error: null,
        activeOperation: {
          type: 'export',
          progress: progressUpdate,
        },
      } as any);

      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('progress-overlay')).toBeInTheDocument();
      });
    });
  });

  describe('Data Loading', () => {
    it('should fetch project on mount', async () => {
      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(mockFetchProject).toHaveBeenCalledWith('proj-123');
      });
    });

    it('should fetch downloads on mount', async () => {
      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(mockFetchDownloads).toHaveBeenCalledWith('proj-123');
      });
    });

    it('should show loading state', () => {
      vi.mocked(useProjectStore).mockReturnValue({
        currentProject: null,
        fetchProject: mockFetchProject,
        fetchDownloads: mockFetchDownloads,
        updateProgress: mockUpdateProgress,
        clearProgress: mockClearProgress,
        isLoading: true,
        error: null,
        activeOperation: { type: null, progress: null },
      } as any);

      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      expect(screen.getByRole('progressbar', { hidden: true }) || document.querySelector('.animate-spin')).toBeInTheDocument();
    });

    it('should show error state', () => {
      vi.mocked(useProjectStore).mockReturnValue({
        currentProject: null,
        fetchProject: mockFetchProject,
        fetchDownloads: mockFetchDownloads,
        updateProgress: mockUpdateProgress,
        clearProgress: mockClearProgress,
        isLoading: false,
        error: 'Failed to load project',
        activeOperation: { type: null, progress: null },
      } as any);

      render(
        <BrowserRouter>
          <ProjectPage />
        </BrowserRouter>
      );

      expect(screen.getByText('Error loading project')).toBeInTheDocument();
      expect(screen.getByText('Failed to load project')).toBeInTheDocument();
    });
  });
});
