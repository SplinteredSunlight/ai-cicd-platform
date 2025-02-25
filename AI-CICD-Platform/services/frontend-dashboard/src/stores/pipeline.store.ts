import { create } from 'zustand';
import { api, endpoints, Pipeline } from '../config/api';

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
