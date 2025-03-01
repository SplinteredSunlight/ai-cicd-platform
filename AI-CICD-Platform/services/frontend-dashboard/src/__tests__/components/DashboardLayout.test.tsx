import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import { useDashboardStore } from '../../stores/dashboard.store';
import { useDebugStore } from '../../stores/debug.store';

// Mock the stores
vi.mock('../../stores/dashboard.store', () => ({
  useDashboardStore: vi.fn(),
  useDashboardWebSocket: vi.fn(),
}));

vi.mock('../../stores/debug.store', () => ({
  useDebugStore: vi.fn(),
}));

// Mock react-grid-layout
vi.mock('react-grid-layout', () => ({
  Responsive: vi.fn(() => null),
  WidthProvider: vi.fn((comp) => comp),
}));

describe('DashboardLayout', () => {
  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();

    // Mock dashboard store
    (useDashboardStore as any).mockReturnValue({
      dashboards: [
        {
          id: 'default',
          name: 'Default Dashboard',
          description: 'Default dashboard with overview of the system',
          isDefault: true,
          layout: {
            cols: 12,
            rowHeight: 50,
            containerPadding: [10, 10],
            margin: [10, 10],
          },
          widgets: [
            {
              id: 'metrics-summary',
              type: 'metrics-summary',
              title: 'System Metrics',
              size: { w: 12, h: 4, minW: 6, minH: 3 },
              position: { x: 0, y: 0 },
              settings: {},
              realtime: true,
            },
          ],
        },
      ],
      activeDashboardId: 'default',
      isEditMode: false,
      realtimeEnabled: true,
      widgetData: {},
      setActiveDashboard: vi.fn(),
      addDashboard: vi.fn(),
      updateDashboard: vi.fn(),
      deleteDashboard: vi.fn(),
      addWidget: vi.fn(),
      updateWidget: vi.fn(),
      deleteWidget: vi.fn(),
      setEditMode: vi.fn(),
      setRealtimeEnabled: vi.fn(),
      updateWidgetData: vi.fn(),
      getWidgetData: vi.fn(),
    });

    // Mock debug store
    (useDebugStore as any).mockReturnValue({
      mlClassifications: {},
      realtimeErrors: [],
    });
  });

  it('renders the dashboard layout with header', () => {
    render(<DashboardLayout />);
    
    // Check for dashboard name in header
    expect(screen.getByText('Default Dashboard')).toBeInTheDocument();
    
    // Check for real-time toggle
    expect(screen.getByText('Real-time')).toBeInTheDocument();
    
    // Check for edit layout button
    expect(screen.getByText('Edit Layout')).toBeInTheDocument();
  });

  it('toggles edit mode when edit button is clicked', () => {
    const setEditMode = vi.fn();
    (useDashboardStore as any).mockReturnValue({
      ...useDashboardStore(),
      setEditMode,
    });

    render(<DashboardLayout />);
    
    // Click edit layout button
    fireEvent.click(screen.getByText('Edit Layout'));
    
    // Check if setEditMode was called with true
    expect(setEditMode).toHaveBeenCalledWith(true);
  });

  it('toggles real-time updates when switch is clicked', () => {
    const setRealtimeEnabled = vi.fn();
    (useDashboardStore as any).mockReturnValue({
      ...useDashboardStore(),
      setRealtimeEnabled,
    });

    render(<DashboardLayout />);
    
    // Find the real-time switch and click it
    const switchElement = screen.getByRole('checkbox');
    fireEvent.click(switchElement);
    
    // Check if setRealtimeEnabled was called with false (toggling from true)
    expect(setRealtimeEnabled).toHaveBeenCalledWith(false);
  });
});
