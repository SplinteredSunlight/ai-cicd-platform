import { create } from 'zustand';
import { api, endpoints, DebugSession, PatchSolution, PipelineError } from '../config/api';
import websocketService from '../services/websocket.service';
import { useEffect } from 'react';

interface MLClassification {
  errorId: string;
  classifications: {
    category?: { prediction: string; confidence: number };
    severity?: { prediction: string; confidence: number };
    stage?: { prediction: string; confidence: number };
  };
  timestamp: string;
}

interface DebugState {
  sessions: DebugSession[];
  selectedSession: DebugSession | null;
  isLoading: boolean;
  error: string | null;
  mlClassifications: Record<string, MLClassification>; // Map of errorId to classification
  realtimeErrors: PipelineError[];
  fetchSessions: () => Promise<void>;
  getSession: (sessionId: string) => Promise<void>;
  analyzeError: (errorId: string) => Promise<void>;
  applyPatch: (sessionId: string, patchId: string) => Promise<void>;
  rollbackPatch: (sessionId: string, patchId: string) => Promise<void>;
  getMLClassification: (errorId: string) => Promise<void>;
  clearRealtimeErrors: () => void;
}

export const useDebugStore = create<DebugState>((set, get) => ({
  sessions: [],
  selectedSession: null,
  isLoading: false,
  error: null,
  mlClassifications: {},
  realtimeErrors: [],

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

  getMLClassification: async (errorId: string) => {
    set({ isLoading: true, error: null });

    try {
      const response = await api.get(`${endpoints.debug.analyze}/${errorId}/ml-classification`);
      const classification = response.data.data;

      set(state => ({
        mlClassifications: {
          ...state.mlClassifications,
          [errorId]: {
            errorId,
            classifications: classification.classifications,
            timestamp: new Date().toISOString(),
          },
        },
        isLoading: false,
        error: null,
      }));
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to get ML classification',
      });
    }
  },

  clearRealtimeErrors: () => {
    set({ realtimeErrors: [] });
  },
}));

// Custom hook for WebSocket integration
export const useDebugWebSocket = () => {
  const { 
    fetchSessions, 
    getSession, 
    selectedSession, 
    getMLClassification
  } = useDebugStore();
  const setStore = useDebugStore.setState;

  useEffect(() => {
    // Handle debug session created event
    const unsubscribeSessionCreated = websocketService.on('debug_session_created', (data) => {
      console.log('WebSocket: Debug session created', data);
      fetchSessions();
    });

    // Handle debug session updated event
    const unsubscribeSessionUpdated = websocketService.on('debug_session_updated', (data) => {
      console.log('WebSocket: Debug session updated', data);
      fetchSessions();
      
      // If this is the currently selected session, refresh it
      if (selectedSession && data.sessionId === selectedSession.id) {
        getSession(data.sessionId);
      }
    });

    // Handle new error detected event
    const unsubscribeErrorDetected = websocketService.on('debug_error_detected', (data) => {
      console.log('WebSocket: New error detected', data);
      fetchSessions();
      
      // If this is the currently selected session, refresh it
      if (selectedSession && data.sessionId === selectedSession.id) {
        getSession(data.sessionId);
      }

      // Get ML classification for the new error
      if (data.errorId) {
        getMLClassification(data.errorId);
      }

      // Add to realtime errors list
      if (data.error) {
        setStore((state: DebugState) => ({
          ...state,
          realtimeErrors: [data.error, ...state.realtimeErrors].slice(0, 50) // Keep last 50 errors
        }));
      }
    });

      // Handle ML classification event
    const unsubscribeMLClassification = websocketService.on('debug_ml_classification', (data) => {
      console.log('WebSocket: ML classification received', data);
      
      if (data.errorId && data.classifications) {
        setStore((state: DebugState) => ({
          ...state,
          mlClassifications: {
            ...state.mlClassifications,
            [data.errorId]: {
              errorId: data.errorId,
              classifications: data.classifications,
              timestamp: new Date().toISOString(),
            },
          },
        }));
      }
    });

    // Handle patch solution generated event
    const unsubscribePatchGenerated = websocketService.on('debug_patch_generated', (data) => {
      console.log('WebSocket: Patch solution generated', data);
      
      // If this is the currently selected session, refresh it
      if (selectedSession && data.sessionId === selectedSession.id) {
        getSession(data.sessionId);
      }
    });

    // Handle patch applied event
    const unsubscribePatchApplied = websocketService.on('debug_patch_applied', (data) => {
      console.log('WebSocket: Patch applied', data);
      
      // If this is the currently selected session, refresh it
      if (selectedSession && data.sessionId === selectedSession.id) {
        getSession(data.sessionId);
      }
    });

    // Handle patch rollback event
    const unsubscribePatchRollback = websocketService.on('debug_patch_rollback', (data) => {
      console.log('WebSocket: Patch rolled back', data);
      
      // If this is the currently selected session, refresh it
      if (selectedSession && data.sessionId === selectedSession.id) {
        getSession(data.sessionId);
      }
    });

    // Cleanup function to unsubscribe from all events
    return () => {
      unsubscribeSessionCreated();
      unsubscribeSessionUpdated();
      unsubscribeErrorDetected();
      unsubscribePatchGenerated();
      unsubscribePatchApplied();
      unsubscribePatchRollback();
      unsubscribeMLClassification();
    };
  }, [fetchSessions, getSession, selectedSession, getMLClassification, setStore]);
};
