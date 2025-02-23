import { create } from 'zustand';
import { api, endpoints, Pipeline, ApiResponse } from '../config/api';

interface PipelineState {
  pipelines: Pipeline[];
  activePipeline: Pipeline | null;
  isLoading: boolean;
  error: string | null;
  // Actions
  fetchPipelines: () => Promise<void>;
  generatePipeline: (description: string) => Promise<Pipeline>;
  validatePipeline: (pipeline: Pipeline) => Promise<boolean>;
  executePipeline: (pipelineId: string) => Promise<void>;
  setActivePipeline: (pipeline: Pipeline | null) => void;
}

export const usePipelineStore = create<PipelineState>((set, get) => ({
  pipelines: [],
  activePipeline: null,
  isLoading: false,
  error: null,

  fetchPipelines: async () => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await api.get<ApiResponse<Pipeline[]>>(
        endpoints.pipelines.list
      );
      
      set({
        pipelines: response.data.data || [],
        isLoading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Failed to fetch pipelines',
        isLoading: false,
      });
      throw error;
    }
  },

  generatePipeline: async (description: string) => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await api.post<ApiResponse<Pipeline>>(
        endpoints.pipelines.generate,
        { description }
      );
      
      const newPipeline = response.data.data!;
      
      set(state => ({
        pipelines: [...state.pipelines, newPipeline],
        activePipeline: newPipeline,
        isLoading: false,
      }));

      return newPipeline;
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Failed to generate pipeline',
        isLoading: false,
      });
      throw error;
    }
  },

  validatePipeline: async (pipeline: Pipeline) => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await api.post<ApiResponse<{ valid: boolean }>>(
        endpoints.pipelines.validate,
        pipeline
      );
      
      set({ isLoading: false });
      
      return response.data.data?.valid || false;
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Pipeline validation failed',
        isLoading: false,
      });
      throw error;
    }
  },

  executePipeline: async (pipelineId: string) => {
    try {
      set({ isLoading: true, error: null });
      
      await api.post<ApiResponse>(
        endpoints.pipelines.execute,
        { pipeline_id: pipelineId }
      );
      
      // Update pipeline status in state
      set(state => ({
        pipelines: state.pipelines.map(p =>
          p.id === pipelineId
            ? { ...p, status: 'running' }
            : p
        ),
        isLoading: false,
      }));
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Failed to execute pipeline',
        isLoading: false,
      });
      throw error;
    }
  },

  setActivePipeline: (pipeline: Pipeline | null) => {
    set({ activePipeline: pipeline });
  },
}));

// Optional: Subscribe to pipeline updates via WebSocket
if (typeof window !== 'undefined') {
  const ws = new WebSocket(
    `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/pipelines`
  );

  ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    
    // Update pipeline status in store
    usePipelineStore.setState(state => ({
      pipelines: state.pipelines.map(p =>
        p.id === update.pipeline_id
          ? { ...p, ...update }
          : p
      ),
    }));
  };

  ws.onerror = (error) => {
    console.error('Pipeline WebSocket error:', error);
  };
}
