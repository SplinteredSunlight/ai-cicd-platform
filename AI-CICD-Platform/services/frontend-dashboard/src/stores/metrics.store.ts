import { create } from 'zustand';
import { api, endpoints, MetricsSummary } from '../config/api';

interface MetricsState {
  summary: MetricsSummary | null;
  isLoading: boolean;
  error: string | null;
  fetchSummary: () => Promise<void>;
}

export const useMetricsStore = create<MetricsState>((set) => ({
  summary: null,
  isLoading: false,
  error: null,

  fetchSummary: async () => {
    set({ isLoading: true, error: null });

    try {
      const response = await api.get(endpoints.metrics.summary);
      set({
        summary: response.data.data,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch metrics',
      });
    }
  },
}));
