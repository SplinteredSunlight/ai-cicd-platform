import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act } from '@testing-library/react';
import { useDashboardStore } from '../../stores/dashboard.store';

// Mock the websocket service
vi.mock('../../services/websocket.service', () => ({
  default: {
    on: vi.fn(() => vi.fn()),
    isSocketConnected: vi.fn().mockReturnValue(true),
  },
}));

describe('Dashboard Store', () => {
  beforeEach(() => {
    // Reset the store before each test
    act(() => {
      useDashboardStore.setState({
        dashboards: [
          {
            id: 'test-dashboard',
            name: 'Test Dashboard',
            description: 'Test dashboard for unit tests',
            layout: {
              cols: 12,
              rowHeight: 50,
              containerPadding: [10, 10],
              margin: [10, 10],
            },
            widgets: [
              {
                id: 'test-widget',
                type: 'metrics-summary',
                title: 'Test Widget',
                size: { w: 6, h: 4 },
                position: { x: 0, y: 0 },
                settings: {},
                realtime: true,
              },
            ],
          },
        ],
        activeDashboardId: 'test-dashboard',
        isEditMode: false,
        realtimeEnabled: true,
        widgetData: {},
      });
    });
  });

  it('should add a new dashboard', () => {
    const { addDashboard } = useDashboardStore.getState();
    
    // Mock uuid to return a predictable value
    vi.mock('uuid', () => ({
      v4: () => 'test-dashboard-id'
    }));
    
    act(() => {
      addDashboard({
        name: 'New Dashboard',
        description: 'A new dashboard',
        layout: {
          cols: 12,
          rowHeight: 50,
          containerPadding: [10, 10],
          margin: [10, 10],
        },
        widgets: [],
      });
    });
    
    const updatedState = useDashboardStore.getState();
    expect(updatedState.dashboards.length).toBe(2);
    expect(updatedState.dashboards[1].name).toBe('New Dashboard');
    expect(updatedState.dashboards[1].id).toBe('test-dashboard-id');
  });

  it('should update a dashboard', () => {
    const { updateDashboard } = useDashboardStore.getState();
    
    act(() => {
      updateDashboard('test-dashboard', {
        name: 'Updated Dashboard',
        description: 'Updated description',
      });
    });
    
    const updatedState = useDashboardStore.getState();
    expect(updatedState.dashboards[0].name).toBe('Updated Dashboard');
    expect(updatedState.dashboards[0].description).toBe('Updated description');
  });

  it('should delete a dashboard', () => {
    // First add a second dashboard so we can delete one
    const { addDashboard, deleteDashboard } = useDashboardStore.getState();
    
    act(() => {
      addDashboard({
        name: 'Second Dashboard',
        description: 'Another dashboard',
        layout: {
          cols: 12,
          rowHeight: 50,
          containerPadding: [10, 10],
          margin: [10, 10],
        },
        widgets: [],
      });
    });
    
    // Verify we have two dashboards
    let state = useDashboardStore.getState();
    expect(state.dashboards.length).toBe(2);
    
    // Delete the first dashboard
    act(() => {
      deleteDashboard('test-dashboard');
    });
    
    // Verify we now have one dashboard and the active dashboard has changed
    state = useDashboardStore.getState();
    expect(state.dashboards.length).toBe(1);
    expect(state.dashboards[0].name).toBe('Second Dashboard');
    expect(state.activeDashboardId).not.toBe('test-dashboard');
  });

  it('should not delete the last dashboard', () => {
    const { deleteDashboard } = useDashboardStore.getState();
    
    act(() => {
      deleteDashboard('test-dashboard');
    });
    
    const state = useDashboardStore.getState();
    expect(state.dashboards.length).toBe(1);
    expect(state.dashboards[0].id).toBe('test-dashboard');
  });

  it('should add a widget to a dashboard', () => {
    const { addWidget } = useDashboardStore.getState();
    
    act(() => {
      addWidget('test-dashboard', {
        type: 'error-classification',
        title: 'Error Classification',
        size: { w: 6, h: 6 },
        position: { x: 6, y: 0 },
        settings: { chartType: 'pie' },
        realtime: true,
      });
    });
    
    const state = useDashboardStore.getState();
    expect(state.dashboards[0].widgets.length).toBe(2);
    expect(state.dashboards[0].widgets[1].title).toBe('Error Classification');
    expect(state.dashboards[0].widgets[1].settings.chartType).toBe('pie');
  });

  it('should update a widget', () => {
    const { updateWidget } = useDashboardStore.getState();
    
    act(() => {
      updateWidget('test-dashboard', 'test-widget', {
        title: 'Updated Widget',
        settings: { showCount: 10 },
      });
    });
    
    const state = useDashboardStore.getState();
    expect(state.dashboards[0].widgets[0].title).toBe('Updated Widget');
    expect(state.dashboards[0].widgets[0].settings.showCount).toBe(10);
  });

  it('should delete a widget', () => {
    const { deleteWidget } = useDashboardStore.getState();
    
    act(() => {
      deleteWidget('test-dashboard', 'test-widget');
    });
    
    const state = useDashboardStore.getState();
    expect(state.dashboards[0].widgets.length).toBe(0);
  });

  it('should toggle edit mode', () => {
    const { setEditMode } = useDashboardStore.getState();
    
    act(() => {
      setEditMode(true);
    });
    
    let state = useDashboardStore.getState();
    expect(state.isEditMode).toBe(true);
    
    act(() => {
      setEditMode(false);
    });
    
    state = useDashboardStore.getState();
    expect(state.isEditMode).toBe(false);
  });

  it('should toggle realtime updates', () => {
    const { setRealtimeEnabled } = useDashboardStore.getState();
    
    act(() => {
      setRealtimeEnabled(false);
    });
    
    let state = useDashboardStore.getState();
    expect(state.realtimeEnabled).toBe(false);
    
    act(() => {
      setRealtimeEnabled(true);
    });
    
    state = useDashboardStore.getState();
    expect(state.realtimeEnabled).toBe(true);
  });

  it('should update widget data', () => {
    const { updateWidgetData, getWidgetData } = useDashboardStore.getState();
    
    const testData = { value: 42, label: 'Test Data' };
    
    act(() => {
      updateWidgetData('test-widget', testData);
    });
    
    const data = getWidgetData('test-widget');
    expect(data).toEqual(testData);
  });

  it('should clear widget data', () => {
    const { updateWidgetData, clearWidgetData, getWidgetData } = useDashboardStore.getState();
    
    // First add some data
    act(() => {
      updateWidgetData('test-widget', { value: 42 });
      updateWidgetData('another-widget', { value: 100 });
    });
    
    // Clear specific widget data
    act(() => {
      clearWidgetData('test-widget');
    });
    
    // Check that only the specified widget data was cleared
    let data = getWidgetData('test-widget');
    expect(data).toBeUndefined();
    data = getWidgetData('another-widget');
    expect(data).toEqual({ value: 100 });
    
    // Clear all widget data
    act(() => {
      clearWidgetData();
    });
    
    // Check that all widget data was cleared
    data = getWidgetData('another-widget');
    expect(data).toBeUndefined();
  });
});
