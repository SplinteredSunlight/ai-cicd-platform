import { create } from 'zustand';
import { api, endpoints, DebugSession, PipelineError, PatchSolution, ApiResponse } from '../config/api';

interface DebugState {
  sessions: DebugSession[];
  activeSession: DebugSession | null;
  isLoading: boolean;
  error: string | null;
  // Actions
  startDebugSession: (pipelineId: string) => Promise<DebugSession>;
  fetchSessions: () => Promise<void>;
  analyzeError: (error: PipelineError) => Promise<void>;
  applyPatch: (patch: PatchSolution) => Promise<boolean>;
  rollbackPatch: (patchId: string) => Promise<boolean>;
  setActiveSession: (session: DebugSession | null) => void;
  // Analysis helpers
  getErrorStats: () => {
    total: number;
    resolved: number;
    pending: number;
    by_severity: Record<string, number>;
  };
  getPatchingStats: () => {
    total_patches: number;
    successful_patches: number;
    failed_patches: number;
    success_rate: number;
  };
}

export const useDebugStore = create<DebugState>((set, get) => ({
  sessions: [],
  activeSession: null,
  isLoading: false,
  error: null,

  startDebugSession: async (pipelineId: string) => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await api.post<ApiResponse<DebugSession>>(
        endpoints.debug.analyze,
        { pipeline_id: pipelineId }
      );
      
      const newSession = response.data.data!;
      
      set(state => ({
        sessions: [...state.sessions, newSession],
        activeSession: newSession,
        isLoading: false,
      }));

      return newSession;
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Failed to start debug session',
        isLoading: false,
      });
      throw error;
    }
  },

  fetchSessions: async () => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await api.get<ApiResponse<DebugSession[]>>(
        endpoints.debug.sessions
      );
      
      set({
        sessions: response.data.data || [],
        isLoading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Failed to fetch debug sessions',
        isLoading: false,
      });
      throw error;
    }
  },

  analyzeError: async (error: PipelineError) => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await api.post<ApiResponse<PatchSolution[]>>(
        endpoints.debug.analyze,
        { error }
      );
      
      const patches = response.data.data || [];
      
      // Update active session with new patches
      set(state => {
        if (!state.activeSession) return state;
        
        return {
          ...state,
          activeSession: {
            ...state.activeSession,
            patches: [...state.activeSession.patches, ...patches],
          },
          isLoading: false,
        };
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Error analysis failed',
        isLoading: false,
      });
      throw error;
    }
  },

  applyPatch: async (patch: PatchSolution) => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await api.post<ApiResponse<{ success: boolean }>>(
        endpoints.debug.patch,
        { patch }
      );
      
      const success = response.data.data?.success || false;
      
      // Update patch status in active session
      set(state => {
        if (!state.activeSession) return state;
        
        const updatedPatches = state.activeSession.patches.map(p =>
          p.id === patch.id
            ? { ...p, applied: true, success }
            : p
        );
        
        return {
          ...state,
          activeSession: {
            ...state.activeSession,
            patches: updatedPatches,
          },
          isLoading: false,
        };
      });

      return success;
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Patch application failed',
        isLoading: false,
      });
      throw error;
    }
  },

  rollbackPatch: async (patchId: string) => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await api.post<ApiResponse<{ success: boolean }>>(
        `${endpoints.debug.patch}/rollback`,
        { patch_id: patchId }
      );
      
      const success = response.data.data?.success || false;
      
      // Update patch status in active session
      set(state => {
        if (!state.activeSession) return state;
        
        const updatedPatches = state.activeSession.patches.map(p =>
          p.id === patchId
            ? { ...p, applied: false, success: undefined }
            : p
        );
        
        return {
          ...state,
          activeSession: {
            ...state.activeSession,
            patches: updatedPatches,
          },
          isLoading: false,
        };
      });

      return success;
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Patch rollback failed',
        isLoading: false,
      });
      throw error;
    }
  },

  setActiveSession: (session: DebugSession | null) => {
    set({ activeSession: session });
  },

  getErrorStats: () => {
    const { activeSession } = get();
    if (!activeSession) {
      return {
        total: 0,
        resolved: 0,
        pending: 0,
        by_severity: {},
      };
    }

    const errors = activeSession.errors;
    const resolvedErrors = errors.filter(e => 
      activeSession.patches.some(p => 
        p.error_id === e.id && p.applied && p.success
      )
    );

    const bySeverity = errors.reduce((acc, error) => ({
      ...acc,
      [error.severity]: (acc[error.severity] || 0) + 1,
    }), {} as Record<string, number>);

    return {
      total: errors.length,
      resolved: resolvedErrors.length,
      pending: errors.length - resolvedErrors.length,
      by_severity: bySeverity,
    };
  },

  getPatchingStats: () => {
    const { activeSession } = get();
    if (!activeSession) {
      return {
        total_patches: 0,
        successful_patches: 0,
        failed_patches: 0,
        success_rate: 0,
      };
    }

    const appliedPatches = activeSession.patches.filter(p => p.applied);
    const successfulPatches = appliedPatches.filter(p => p.success);
    const failedPatches = appliedPatches.filter(p => !p.success);

    return {
      total_patches: activeSession.patches.length,
      successful_patches: successfulPatches.length,
      failed_patches: failedPatches.length,
      success_rate: appliedPatches.length
        ? successfulPatches.length / appliedPatches.length
        : 0,
    };
  },
}));

// Optional: Subscribe to debug session updates via WebSocket
if (typeof window !== 'undefined') {
  const ws = new WebSocket(
    `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/debug`
  );

  ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    
    // Update session in store
    useDebugStore.setState(state => {
      // Update in sessions list
      const updatedSessions = state.sessions.map(s =>
        s.id === update.session_id
          ? { ...s, ...update }
          : s
      );

      // Update active session if it's the one being updated
      const updatedActiveSession = state.activeSession?.id === update.session_id
        ? { ...state.activeSession, ...update }
        : state.activeSession;

      return {
        sessions: updatedSessions,
        activeSession: updatedActiveSession,
      };
    });
  };

  ws.onerror = (error) => {
    console.error('Debug WebSocket error:', error);
  };
}
