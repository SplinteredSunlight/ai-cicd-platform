import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';
import { useEffect } from 'react';
import WebSocketService from '../services/websocket.service';
import { persist, createJSONStorage } from 'zustand/middleware';
import { api, endpoints } from '../config/api';

// Widget types
export type WidgetType =
  | 'metrics-summary'
  | 'pipeline-status'
  | 'error-classification'
  | 'security-vulnerabilities'
  | 'service-health'
  | 'recent-errors'
  | 'ml-classification'
  | 'custom-chart'
  | 'performance-metrics'
  | 'deployment-history'
  | 'code-quality'
  | 'architecture-diagram';

// Widget configuration
export interface WidgetConfig {
  id: string;
  type: WidgetType;
  title: string;
  size: {
    w: number;
    h: number;
    minW?: number;
    minH?: number;
    maxW?: number;
    maxH?: number;
  };
  position: {
    x: number;
    y: number;
  };
  settings: Record<string, any>;
  realtime: boolean;
  refreshInterval?: number; // in seconds, undefined means no auto-refresh
}

// Dashboard configuration
export interface DashboardConfig {
  id: string;
  name: string;
  description?: string;
  isDefault?: boolean;
  isTemplate?: boolean;
  createdBy?: string;
  createdAt?: string;
  updatedAt?: string;
  layout: {
    cols: number;
    rowHeight: number;
    containerPadding: [number, number];
    margin: [number, number];
  };
  widgets: WidgetConfig[];
  tags?: string[];
  category?: string;
}

// Dashboard template category
export type DashboardCategory = 
  | 'general'
  | 'development'
  | 'operations'
  | 'security'
  | 'analytics';

// Dashboard store state
interface DashboardState {
  dashboards: DashboardConfig[];
  templates: DashboardConfig[];
  activeDashboardId: string | null;
  isEditMode: boolean;
  realtimeEnabled: boolean;
  widgetData: Record<string, any>;
  isLoading: boolean;
  error: string | null;
  lastSyncTime: string | null;

  // Dashboard actions
  setActiveDashboard: (id: string) => void;
  addDashboard: (dashboard: Omit<DashboardConfig, 'id'>) => string;
  updateDashboard: (id: string, updates: Partial<DashboardConfig>) => void;
  deleteDashboard: (id: string) => void;
  duplicateDashboard: (id: string, newName?: string) => string;
  importDashboard: (dashboard: DashboardConfig) => string;
  exportDashboard: (id: string) => DashboardConfig | null;
  createFromTemplate: (templateId: string) => string;

  // Widget actions
  addWidget: (dashboardId: string, widget: Omit<WidgetConfig, 'id'>) => string;
  updateWidget: (dashboardId: string, widgetId: string, updates: Partial<WidgetConfig>) => void;
  deleteWidget: (dashboardId: string, widgetId: string) => void;
  duplicateWidget: (dashboardId: string, widgetId: string) => string;

  // UI state actions
  setEditMode: (isEditMode: boolean) => void;
  setRealtimeEnabled: (enabled: boolean) => void;

  // Widget data actions
  updateWidgetData: (widgetId: string, data: any) => void;
  getWidgetData: (widgetId: string) => any;
  clearWidgetData: (widgetId?: string) => void;
  refreshWidget: (dashboardId: string, widgetId: string) => Promise<void>;
  refreshAllWidgets: (dashboardId: string) => Promise<void>;

  // Server sync actions
  syncWithServer: () => Promise<void>;
  saveDashboardToServer: (dashboardId: string) => Promise<void>;
  loadDashboardsFromServer: () => Promise<void>;
  loadTemplatesFromServer: () => Promise<void>;
}

// Default dashboard configuration
const defaultDashboard: DashboardConfig = {
  id: 'default',
  name: 'System Overview',
  description: 'Overview of system metrics and status',
  isDefault: true,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
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
      refreshInterval: 60,
    },
    {
      id: 'pipeline-status',
      type: 'pipeline-status',
      title: 'Pipeline Status',
      size: { w: 6, h: 6, minW: 4, minH: 4 },
      position: { x: 0, y: 4 },
      settings: { showCount: 5 },
      realtime: true,
      refreshInterval: 30,
    },
    {
      id: 'error-classification',
      type: 'error-classification',
      title: 'Error Classification',
      size: { w: 6, h: 6, minW: 4, minH: 4 },
      position: { x: 6, y: 4 },
      settings: { chartType: 'pie', showLegend: true },
      realtime: true,
    },
    {
      id: 'security-vulnerabilities',
      type: 'security-vulnerabilities',
      title: 'Security Vulnerabilities',
      size: { w: 12, h: 5, minW: 6, minH: 4 },
      position: { x: 0, y: 10 },
      settings: { showCount: 5 },
      realtime: true,
      refreshInterval: 300,
    },
  ],
  tags: ['system', 'overview'],
  category: 'general',
};

// ML Dashboard template
const mlDashboardTemplate: DashboardConfig = {
  id: 'ml-template',
  name: 'ML Error Analysis',
  description: 'Comprehensive view of ML-based error analysis and classification',
  isDefault: false,
  isTemplate: true,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  layout: {
    cols: 12,
    rowHeight: 50,
    containerPadding: [10, 10],
    margin: [10, 10],
  },
  widgets: [
    {
      id: 'ml-classification-overview',
      type: 'ml-classification',
      title: 'ML Error Classification',
      size: { w: 12, h: 8, minW: 8, minH: 6 },
      position: { x: 0, y: 0 },
      settings: { showTabs: true, defaultTab: 'overview' },
      realtime: true,
    },
    {
      id: 'error-classification-chart',
      type: 'error-classification',
      title: 'Error Categories',
      size: { w: 6, h: 6, minW: 4, minH: 4 },
      position: { x: 0, y: 8 },
      settings: { chartType: 'pie', showLegend: true },
      realtime: true,
    },
    {
      id: 'recent-errors-list',
      type: 'recent-errors',
      title: 'Recent Errors',
      size: { w: 6, h: 6, minW: 4, minH: 4 },
      position: { x: 6, y: 8 },
      settings: { showCount: 10, showStackTrace: false },
      realtime: true,
      refreshInterval: 30,
    },
  ],
  tags: ['ml', 'errors', 'analysis'],
  category: 'analytics',
};

// DevOps Dashboard template
const devOpsDashboardTemplate: DashboardConfig = {
  id: 'devops-template',
  name: 'DevOps Overview',
  description: 'Monitor CI/CD pipelines and deployments',
  isDefault: false,
  isTemplate: true,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  layout: {
    cols: 12,
    rowHeight: 50,
    containerPadding: [10, 10],
    margin: [10, 10],
  },
  widgets: [
    {
      id: 'pipeline-status-overview',
      type: 'pipeline-status',
      title: 'Pipeline Status',
      size: { w: 12, h: 4, minW: 6, minH: 3 },
      position: { x: 0, y: 0 },
      settings: { showCount: 5 },
      realtime: true,
      refreshInterval: 30,
    },
    {
      id: 'deployment-history',
      type: 'deployment-history',
      title: 'Deployment History',
      size: { w: 6, h: 6, minW: 4, minH: 4 },
      position: { x: 0, y: 4 },
      settings: { timeRange: '7d' },
      realtime: true,
    },
    {
      id: 'performance-metrics',
      type: 'performance-metrics',
      title: 'Performance Metrics',
      size: { w: 6, h: 6, minW: 4, minH: 4 },
      position: { x: 6, y: 4 },
      settings: { metrics: ['cpu', 'memory', 'network'], timeRange: '1d' },
      realtime: true,
      refreshInterval: 60,
    },
    {
      id: 'code-quality',
      type: 'code-quality',
      title: 'Code Quality Metrics',
      size: { w: 12, h: 5, minW: 6, minH: 4 },
      position: { x: 0, y: 10 },
      settings: { metrics: ['coverage', 'bugs', 'vulnerabilities', 'code_smells'] },
      realtime: false,
      refreshInterval: 3600,
    },
  ],
  tags: ['devops', 'ci/cd', 'pipelines'],
  category: 'operations',
};

// Architecture Dashboard template
const architectureDashboardTemplate: DashboardConfig = {
  id: 'architecture-template',
  name: 'Architecture Overview',
  description: 'Visualize system architecture and component relationships',
  isDefault: false,
  isTemplate: true,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  layout: {
    cols: 12,
    rowHeight: 50,
    containerPadding: [10, 10],
    margin: [10, 10],
  },
  widgets: [
    {
      id: 'system-architecture-diagram',
      type: 'architecture-diagram',
      title: 'System Architecture',
      size: { w: 12, h: 8, minW: 8, minH: 6 },
      position: { x: 0, y: 0 },
      settings: { showTabs: true, defaultTab: 'system' },
      realtime: true,
    },
    {
      id: 'service-architecture-diagram',
      type: 'architecture-diagram',
      title: 'Service Architecture',
      size: { w: 12, h: 8, minW: 8, minH: 6 },
      position: { x: 0, y: 8 },
      settings: { showTabs: true, defaultTab: 'service' },
      realtime: true,
    },
  ],
  tags: ['architecture', 'system', 'diagrams'],
  category: 'development',
};

// Create the dashboard store
export const useDashboardStore = create<DashboardState>()(
  persist(
    (set, get) => ({
      dashboards: [defaultDashboard],
      templates: [mlDashboardTemplate, devOpsDashboardTemplate, architectureDashboardTemplate],
      activeDashboardId: defaultDashboard.id,
      isEditMode: false,
      realtimeEnabled: true,
      widgetData: {},
      isLoading: false,
      error: null,
      lastSyncTime: null,

      // Dashboard actions
      setActiveDashboard: (id) => {
        set({ activeDashboardId: id });
      },

      addDashboard: (dashboard) => {
        const id = uuidv4();
        const now = new Date().toISOString();
        
        set((state) => ({
          dashboards: [
            ...state.dashboards,
            {
              ...dashboard,
              id,
              createdAt: now,
              updatedAt: now,
            },
          ],
        }));
        
        // Save to server if possible
        const { saveDashboardToServer } = get();
        setTimeout(() => saveDashboardToServer(id), 0);
        
        return id;
      },

      updateDashboard: (id, updates) => {
        set((state) => ({
          dashboards: state.dashboards.map((dashboard) =>
            dashboard.id === id
              ? {
                  ...dashboard,
                  ...updates,
                  updatedAt: new Date().toISOString(),
                }
              : dashboard
          ),
        }));
        
        // Save to server if possible
        const { saveDashboardToServer } = get();
        setTimeout(() => saveDashboardToServer(id), 0);
      },

      deleteDashboard: (id) => {
        const { dashboards, activeDashboardId } = get();

        // Don't delete the last dashboard
        if (dashboards.length <= 1) {
          return;
        }

        // Update active dashboard if the deleted one is active
        let newActiveDashboardId = activeDashboardId;
        if (activeDashboardId === id) {
          const remainingDashboards = dashboards.filter((d) => d.id !== id);
          newActiveDashboardId = remainingDashboards[0]?.id || null;
        }

        set((state) => ({
          dashboards: state.dashboards.filter((dashboard) => dashboard.id !== id),
          activeDashboardId: newActiveDashboardId,
        }));
        
        // Sync with server
        const { syncWithServer } = get();
        setTimeout(() => syncWithServer(), 0);
      },

      duplicateDashboard: (id, newName) => {
        const { dashboards } = get();
        const dashboard = dashboards.find((d) => d.id === id);
        
        if (!dashboard) {
          return id; // Return original id if not found
        }
        
        const newId = uuidv4();
        const now = new Date().toISOString();
        
        const { widgets, ...dashboardWithoutWidgets } = dashboard;
        
        // Create new widgets with new IDs
        const newWidgets = widgets.map((widget) => ({
          ...widget,
          id: uuidv4(),
        }));
        
        set((state) => ({
          dashboards: [
            ...state.dashboards,
            {
              ...dashboardWithoutWidgets,
              id: newId,
              name: newName || `${dashboard.name} (Copy)`,
              isDefault: false,
              createdAt: now,
              updatedAt: now,
              widgets: newWidgets,
            },
          ],
        }));
        
        // Save to server if possible
        const { saveDashboardToServer } = get();
        setTimeout(() => saveDashboardToServer(newId), 0);
        
        return newId;
      },

      importDashboard: (dashboard) => {
        const id = uuidv4();
        const now = new Date().toISOString();
        
        // Create new widgets with new IDs
        const newWidgets = dashboard.widgets.map((widget) => ({
          ...widget,
          id: uuidv4(),
        }));
        
        set((state) => ({
          dashboards: [
            ...state.dashboards,
            {
              ...dashboard,
              id,
              isDefault: false,
              createdAt: now,
              updatedAt: now,
              widgets: newWidgets,
            },
          ],
        }));
        
        // Save to server if possible
        const { saveDashboardToServer } = get();
        setTimeout(() => saveDashboardToServer(id), 0);
        
        return id;
      },

      exportDashboard: (id) => {
        const { dashboards } = get();
        return dashboards.find((d) => d.id === id) || null;
      },

      createFromTemplate: (templateId) => {
        const { templates } = get();
        const template = templates.find((t) => t.id === templateId);
        
        if (!template) {
          return ''; // Return empty string if template not found
        }
        
        const id = uuidv4();
        const now = new Date().toISOString();
        
        // Create new widgets with new IDs
        const newWidgets = template.widgets.map((widget) => ({
          ...widget,
          id: uuidv4(),
        }));
        
        set((state) => ({
          dashboards: [
            ...state.dashboards,
            {
              ...template,
              id,
              name: `${template.name}`,
              isDefault: false,
              isTemplate: false,
              createdAt: now,
              updatedAt: now,
              widgets: newWidgets,
            },
          ],
        }));
        
        // Save to server if possible
        const { saveDashboardToServer } = get();
        setTimeout(() => saveDashboardToServer(id), 0);
        
        return id;
      },

      // Widget actions
      addWidget: (dashboardId, widget) => {
        const id = uuidv4();
        set((state) => ({
          dashboards: state.dashboards.map((dashboard) =>
            dashboard.id === dashboardId
              ? {
                  ...dashboard,
                  widgets: [
                    ...dashboard.widgets,
                    {
                      ...widget,
                      id,
                    },
                  ],
                  updatedAt: new Date().toISOString(),
                }
              : dashboard
          ),
        }));
        
        // Save to server if possible
        const { saveDashboardToServer } = get();
        setTimeout(() => saveDashboardToServer(dashboardId), 0);
        
        return id;
      },

      updateWidget: (dashboardId, widgetId, updates) => {
        set((state) => ({
          dashboards: state.dashboards.map((dashboard) =>
            dashboard.id === dashboardId
              ? {
                  ...dashboard,
                  widgets: dashboard.widgets.map((widget) =>
                    widget.id === widgetId
                      ? {
                          ...widget,
                          ...updates,
                        }
                      : widget
                  ),
                  updatedAt: new Date().toISOString(),
                }
              : dashboard
          ),
        }));
        
        // Save to server if possible
        const { saveDashboardToServer } = get();
        setTimeout(() => saveDashboardToServer(dashboardId), 0);
      },

      deleteWidget: (dashboardId, widgetId) => {
        set((state) => ({
          dashboards: state.dashboards.map((dashboard) =>
            dashboard.id === dashboardId
              ? {
                  ...dashboard,
                  widgets: dashboard.widgets.filter((widget) => widget.id !== widgetId),
                  updatedAt: new Date().toISOString(),
                }
              : dashboard
          ),
        }));
        
        // Save to server if possible
        const { saveDashboardToServer } = get();
        setTimeout(() => saveDashboardToServer(dashboardId), 0);
      },

      duplicateWidget: (dashboardId, widgetId) => {
        const { dashboards } = get();
        const dashboard = dashboards.find((d) => d.id === dashboardId);
        
        if (!dashboard) {
          return ''; // Return empty string if dashboard not found
        }
        
        const widget = dashboard.widgets.find((w) => w.id === widgetId);
        
        if (!widget) {
          return ''; // Return empty string if widget not found
        }
        
        const newId = uuidv4();
        
        set((state) => ({
          dashboards: state.dashboards.map((d) =>
            d.id === dashboardId
              ? {
                  ...d,
                  widgets: [
                    ...d.widgets,
                    {
                      ...widget,
                      id: newId,
                      title: `${widget.title} (Copy)`,
                      position: {
                        x: (widget.position.x + 1) % d.layout.cols,
                        y: widget.position.y + (widget.position.x + 1 >= d.layout.cols ? 1 : 0),
                      },
                    },
                  ],
                  updatedAt: new Date().toISOString(),
                }
              : d
          ),
        }));
        
        // Save to server if possible
        const { saveDashboardToServer } = get();
        setTimeout(() => saveDashboardToServer(dashboardId), 0);
        
        return newId;
      },

      // UI state actions
      setEditMode: (isEditMode) => {
        set({ isEditMode });
      },

      setRealtimeEnabled: (enabled) => {
        set({ realtimeEnabled: enabled });
      },

      // Widget data actions
      updateWidgetData: (widgetId, data) => {
        set((state) => ({
          widgetData: {
            ...state.widgetData,
            [widgetId]: {
              data,
              timestamp: new Date().toISOString(),
            },
          },
        }));
      },

      getWidgetData: (widgetId) => {
        const widgetData = get().widgetData[widgetId];
        return widgetData ? widgetData.data : null;
      },

      clearWidgetData: (widgetId) => {
        if (widgetId) {
          // Clear specific widget data
          set((state) => {
            const newWidgetData = { ...state.widgetData };
            delete newWidgetData[widgetId];
            return { widgetData: newWidgetData };
          });
        } else {
          // Clear all widget data
          set({ widgetData: {} });
        }
      },

      refreshWidget: async (dashboardId, widgetId) => {
        const { dashboards } = get();
        const dashboard = dashboards.find((d) => d.id === dashboardId);
        
        if (!dashboard) {
          return;
        }
        
        const widget = dashboard.widgets.find((w) => w.id === widgetId);
        
        if (!widget) {
          return;
        }
        
        try {
          // Request fresh data from the server
          const response = await api.get(`${endpoints.dashboard.widgetData}/${widget.type}`, {
            params: {
              widgetId,
              settings: JSON.stringify(widget.settings),
            },
          });
          
          // Update widget data
          get().updateWidgetData(widgetId, response.data.data);
        } catch (error) {
          console.error(`Failed to refresh widget ${widgetId}:`, error);
        }
      },

      refreshAllWidgets: async (dashboardId) => {
        const { dashboards } = get();
        const dashboard = dashboards.find((d) => d.id === dashboardId);
        
        if (!dashboard) {
          return;
        }
        
        // Refresh all widgets in parallel
        await Promise.all(
          dashboard.widgets.map((widget) => get().refreshWidget(dashboardId, widget.id))
        );
      },

      // Server sync actions
      syncWithServer: async () => {
        set({ isLoading: true, error: null });
        
        try {
          // Save all dashboards to server
          await get().loadDashboardsFromServer();
          
          set({
            isLoading: false,
            lastSyncTime: new Date().toISOString(),
          });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Failed to sync with server',
          });
        }
      },

      saveDashboardToServer: async (dashboardId) => {
        const { dashboards } = get();
        const dashboard = dashboards.find((d) => d.id === dashboardId);
        
        if (!dashboard) {
          return;
        }
        
        try {
          await api.post(endpoints.dashboard.save, { dashboard });
        } catch (error) {
          console.error(`Failed to save dashboard ${dashboardId} to server:`, error);
        }
      },

      loadDashboardsFromServer: async () => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await api.get(endpoints.dashboard.list);
          
          if (response.data.data && Array.isArray(response.data.data)) {
            // Merge server dashboards with local ones
            // Keep local dashboards that don't exist on server
            const serverDashboards = response.data.data;
            const localDashboards = get().dashboards;
            
            const mergedDashboards = [
              ...serverDashboards,
              ...localDashboards.filter(
                (local) => !serverDashboards.some((server: DashboardConfig) => server.id === local.id)
              ),
            ];
            
            set({
              dashboards: mergedDashboards,
              isLoading: false,
              lastSyncTime: new Date().toISOString(),
            });
          }
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Failed to load dashboards from server',
          });
        }
      },

      loadTemplatesFromServer: async () => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await api.get(endpoints.dashboard.templates);
          
          if (response.data.data && Array.isArray(response.data.data)) {
            set({
              templates: response.data.data,
              isLoading: false,
            });
          }
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Failed to load dashboard templates',
          });
        }
      },
    }),
    {
      name: 'dashboard-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        dashboards: state.dashboards,
        activeDashboardId: state.activeDashboardId,
        realtimeEnabled: state.realtimeEnabled,
      }),
    }
  )
);

/**
 * WebSocket integration for real-time dashboard updates
 */
export function useDashboardWebSocket() {
  const dashboardStore = useDashboardStore();

  // Set up WebSocket event handlers for dashboard updates
  useEffect(() => {
    if (!WebSocketService.isSocketConnected()) {
      return;
    }

    // Handle widget data updates
    const handleWidgetDataUpdate = (data: { widgetId: string; data: any }) => {
      if (dashboardStore.realtimeEnabled) {
        dashboardStore.updateWidgetData(data.widgetId, data.data);
      }
    };

    // Handle dashboard configuration updates
    const handleDashboardUpdate = (data: { dashboardId: string; dashboard: DashboardConfig }) => {
      // Find the dashboard in our store
      const existingDashboard = dashboardStore.dashboards.find(
        (d) => d.id === data.dashboardId
      );
      
      if (existingDashboard) {
        // Update existing dashboard
        dashboardStore.updateDashboard(data.dashboardId, data.dashboard);
      } else {
        // Import new dashboard
        dashboardStore.importDashboard(data.dashboard);
      }
    };

    // Handle dashboard deletion
    const handleDashboardDelete = (data: { dashboardId: string }) => {
      const existingDashboard = dashboardStore.dashboards.find(
        (d) => d.id === data.dashboardId
      );
      
      if (existingDashboard && !existingDashboard.isDefault) {
        dashboardStore.deleteDashboard(data.dashboardId);
      }
    };

    // Handle template updates
    const handleTemplateUpdate = (data: { templates: DashboardConfig[] }) => {
      // Replace all templates
      dashboardStore.loadTemplatesFromServer();
    };

    // Subscribe to events
    const unsubscribeWidgetData = WebSocketService.on('widget_data_update', handleWidgetDataUpdate);
    const unsubscribeDashboardUpdate = WebSocketService.on('dashboard_update', handleDashboardUpdate);
    const unsubscribeDashboardDelete = WebSocketService.on('dashboard_delete', handleDashboardDelete);
    const unsubscribeTemplateUpdate = WebSocketService.on('dashboard_templates_update', handleTemplateUpdate);

    // Set up auto-refresh for widgets
    const refreshIntervals: Record<string, number> = {};
    
    // Clear any existing intervals
    const clearAllIntervals = () => {
      Object.values(refreshIntervals).forEach((interval) => clearInterval(interval));
    };
    
    // Set up new intervals for each widget that has a refresh interval
    const setupRefreshIntervals = () => {
      clearAllIntervals();
      
      const { dashboards, activeDashboardId, realtimeEnabled } = dashboardStore;
      
      if (!realtimeEnabled || !activeDashboardId) {
        return;
      }
      
      const activeDashboard = dashboards.find((d) => d.id === activeDashboardId);
      
      if (!activeDashboard) {
        return;
      }
      
      activeDashboard.widgets.forEach((widget) => {
        if (widget.refreshInterval && widget.refreshInterval > 0) {
          refreshIntervals[widget.id] = window.setInterval(() => {
            dashboardStore.refreshWidget(activeDashboardId, widget.id);
          }, widget.refreshInterval * 1000);
        }
      });
    };
    
    // Set up refresh intervals initially
    setupRefreshIntervals();
    
    // Watch for changes to active dashboard or realtime setting
    useEffect(() => {
      setupRefreshIntervals();
      
      return () => clearAllIntervals();
    }, [dashboardStore.activeDashboardId, dashboardStore.realtimeEnabled]);

    // Clean up all subscriptions and intervals
    return () => {
      unsubscribeWidgetData();
      unsubscribeDashboardUpdate();
      unsubscribeDashboardDelete();
      unsubscribeTemplateUpdate();
      clearAllIntervals();
    };
  }, [dashboardStore]);

  return null;
}

export default useDashboardStore;
