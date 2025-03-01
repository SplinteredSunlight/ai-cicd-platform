import { create } from 'zustand';
import { api, endpoints, Pipeline } from '../config/api';
import websocketService from '../services/websocket.service';
import { useEffect } from 'react';

interface PipelineState {
  pipelines: Pipeline[];
  selectedPipeline: Pipeline | null;
  isLoading: boolean;
  error: string | null;
  fetchPipelines: () => Promise<void>;
  generatePipeline: (repository: string, branch: string) => Promise<void>;
  validatePipeline: (pipelineId: string) => Promise<void>;
  executePipeline: (pipelineId: string) => Promise<void>;
  selectPipeline: (pipeline: Pipeline | null) => void;
}

// Create the store
export const usePipelineStore = create<PipelineState>((set, get) => ({
  pipelines: [],
  selectedPipeline: null,
  isLoading: false,
  error: null,

  fetchPipelines: async () => {
    set({ isLoading: true, error: null });

    try {
      const response = await api.get(endpoints.pipelines.list);
      set({
        pipelines: response.data.data,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch pipelines',
      });
    }
  },

  generatePipeline: async (repository: string, branch: string) => {
    set({ isLoading: true, error: null });

    try {
      const response = await api.post(endpoints.pipelines.generate, {
        repository,
        branch,
      });
      
      const newPipeline = response.data.data;
      set((state) => ({
        pipelines: [...state.pipelines, newPipeline],
        selectedPipeline: newPipeline,
        isLoading: false,
        error: null,
      }));
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to generate pipeline',
      });
    }
  },

  validatePipeline: async (pipelineId: string) => {
    set({ isLoading: true, error: null });

    try {
      await api.post(`${endpoints.pipelines.validate}/${pipelineId}`);
      
      // Refresh pipeline list to get updated status
      await get().fetchPipelines();
      
      set({ isLoading: false, error: null });
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to validate pipeline',
      });
    }
  },

  executePipeline: async (pipelineId: string) => {
    set({ isLoading: true, error: null });

    try {
      await api.post(`${endpoints.pipelines.execute}/${pipelineId}`);
      
      // Refresh pipeline list to get updated status
      await get().fetchPipelines();
      
      set({ isLoading: false, error: null });
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to execute pipeline',
      });
    }
  },

  selectPipeline: (pipeline: Pipeline | null) => {
    set({ selectedPipeline: pipeline });
  },
}));

// Custom hook for WebSocket integration
export const usePipelineWebSocket = () => {
  const { fetchPipelines } = usePipelineStore();

  useEffect(() => {
    // Handle pipeline created event
    const unsubscribePipelineCreated = websocketService.on('pipeline_created', (data) => {
      console.log('WebSocket: Pipeline created', data);
      fetchPipelines();
    });

    // Handle pipeline updated event
    const unsubscribePipelineUpdated = websocketService.on('pipeline_updated', (data) => {
      console.log('WebSocket: Pipeline updated', data);
      fetchPipelines();
    });

    // Handle pipeline status changed event
    const unsubscribePipelineStatusChanged = websocketService.on('pipeline_status_changed', (data) => {
      console.log('WebSocket: Pipeline status changed', data);
      fetchPipelines();
    });

    // Handle pipeline deleted event
    const unsubscribePipelineDeleted = websocketService.on('pipeline_deleted', (data) => {
      console.log('WebSocket: Pipeline deleted', data);
      fetchPipelines();
    });

    // Cleanup function to unsubscribe from all events
    return () => {
      unsubscribePipelineCreated();
      unsubscribePipelineUpdated();
      unsubscribePipelineStatusChanged();
      unsubscribePipelineDeleted();
    };
  }, [fetchPipelines]);
};
