import { create } from 'zustand';
import { api, endpoints, MetricsSummary, ServiceHealth, ApiResponse } from '../config/api';

interface Alert {
  id: string;
  service: string;
  message: string;
  severity: 'critical' | 'warning' | 'info';
  timestamp: string;
}

interface MetricsState {
  summary: MetricsSummary | null;
  serviceHealth: Record<string, ServiceHealth>;
  alerts: Alert[];
  isLoading: boolean;
  error: string | null;
  // Actions
  fetchMetricsSummary: () => Promise<void>;
  fetchServiceHealth: () => Promise<void>;
  fetchAlerts: () => Promise<void>;
  // Analysis helpers
  getServiceHealthStatus: () => {
    healthy: number;
    degraded: number;
    down: number;
    total: number;
  };
  getAverageResponseTime: () => number;
  getErrorRates: () => Record<string, number>;
  getAlertsByService: () => Record<string, Alert[]>;
}

export const useMetricsStore = create<MetricsState>((set, get) => ({
  summary: null,
  serviceHealth: {},
  alerts: [],
  isLoading: false,
  error: null,

  fetchMetricsSummary: async () => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await api.get<ApiResponse<MetricsSummary>>(
        endpoints.metrics.summary
      );
      
      set({
        summary: response.data.data || null,
        isLoading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Failed to fetch metrics summary',
        isLoading: false,
      });
      throw error;
    }
  },

  fetchServiceHealth: async () => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await api.get<ApiResponse<Record<string, ServiceHealth>>>(
        endpoints.metrics.services
      );
      
      set({
        serviceHealth: response.data.data || {},
        isLoading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Failed to fetch service health',
        isLoading: false,
      });
      throw error;
    }
  },

  fetchAlerts: async () => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await api.get<ApiResponse<Alert[]>>(
        endpoints.metrics.alerts
      );
      
      set({
        alerts: response.data.data || [],
        isLoading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Failed to fetch alerts',
        isLoading: false,
      });
      throw error;
    }
  },

  getServiceHealthStatus: () => {
    const { serviceHealth } = get();
    const services = Object.values(serviceHealth);
    
    return {
      healthy: services.filter(s => s.status === 'healthy').length,
      degraded: services.filter(s => s.status === 'degraded').length,
      down: services.filter(s => s.status === 'down').length,
      total: services.length,
    };
  },

  getAverageResponseTime: () => {
    const { serviceHealth } = get();
    const services = Object.values(serviceHealth);
    
    if (!services.length) return 0;
    
    const totalResponseTime = services.reduce(
      (sum, service) => sum + service.response_time,
      0
    );
    
    return totalResponseTime / services.length;
  },

  getErrorRates: () => {
    const { serviceHealth } = get();
    
    return Object.entries(serviceHealth).reduce(
      (acc, [service, health]) => ({
        ...acc,
        [service]: health.error_rate,
      }),
      {} as Record<string, number>
    );
  },

  getAlertsByService: () => {
    const { alerts } = get();
    
    return alerts.reduce((acc, alert) => {
      if (!acc[alert.service]) {
        acc[alert.service] = [];
      }
      acc[alert.service].push(alert);
      return acc;
    }, {} as Record<string, Alert[]>);
  },
}));

// Optional: Subscribe to metrics updates via WebSocket
if (typeof window !== 'undefined') {
  const ws = new WebSocket(
    `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/metrics`
  );

  ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    
    // Update metrics in store based on update type
    useMetricsStore.setState(state => {
      switch (update.type) {
        case 'service_health':
          return {
            ...state,
            serviceHealth: {
              ...state.serviceHealth,
              [update.service]: update.health,
            },
          };
        
        case 'alert':
          return {
            ...state,
            alerts: [...state.alerts, update.alert],
          };
        
        case 'metrics_summary':
          return {
            ...state,
            summary: update.summary,
          };
        
        default:
          return state;
      }
    });
  };

  ws.onerror = (error) => {
    console.error('Metrics WebSocket error:', error);
  };

  // Cleanup function
  const cleanup = () => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.close();
    }
  };

  // Add cleanup to window unload event
  window.addEventListener('unload', cleanup);
}
