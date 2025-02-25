import { create } from 'zustand';
import { api, endpoints, DebugSession, PatchSolution } from '../config/api';

interface DebugState {
  sessions: DebugSession[];
  selectedSession: DebugSession | null;
  isLoading: boolean;
  error: string | null;
  fetchSessions: () => Promise<void>;
  getSession: (sessionId: string) => Promise<void>;
  analyzeError: (errorId: string) => Promise<void>;
  applyPatch: (sessionId: string, patchId: string) => Promise<void>;
  rollbackPatch: (sessionId: string, patchId: string) => Promise<void>;
}

export const useDebugStore = create<DebugState>((set, get) => ({
  sessions: [],
  selectedSession: null,
  isLoading: false,
  error: null,

  fetchSessions: async () => {
    set({ isLoading: true, error: null });

    try {
      const response = await api.get(endpoints.debug.sessions);
      set({
        sessions: response.data.data,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch debug sessions',
      });
    }
  },

  getSession: async (sessionId: string) => {
    set({ isLoading: true, error: null });

    try {
      const response = await api.get(
        endpoints.debug.session.replace(':id', sessionId)
      );
      set({
        selectedSession: response.data.data,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch session details',
      });
    }
  },

  analyzeError: async (errorId: string) => {
    set({ isLoading: true, error: null });

    try {
      const response = await api.post(endpoints.debug.analyze, { errorId });
      const patches: PatchSolution[] = response.data.data;

      // Update the selected session with new patches
      const session = get().selectedSession;
      if (session) {
        set({
          selectedSession: {
            ...session,
            patches: [...session.patches, ...patches],
          },
          isLoading: false,
          error: null,
        });
      }
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to analyze error',
      });
    }
  },

  applyPatch: async (sessionId: string, patchId: string) => {
    set({ isLoading: true, error: null });

    try {
      await api.post(
        endpoints.debug.applyPatch
          .replace(':sessionId', sessionId)
          .replace(':patchId', patchId)
      );

      // Refresh session to get updated state
      await get().getSession(sessionId);
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to apply patch',
      });
    }
  },

  rollbackPatch: async (sessionId: string, patchId: string) => {
    set({ isLoading: true, error: null });

    try {
      await api.post(
        endpoints.debug.rollbackPatch
          .replace(':sessionId', sessionId)
          .replace(':patchId', patchId)
      );

      // Refresh session to get updated state
      await get().getSession(sessionId);
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to rollback patch',
      });
    }
  },
}));
