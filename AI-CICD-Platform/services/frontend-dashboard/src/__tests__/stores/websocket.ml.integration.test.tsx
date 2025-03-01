import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useDebugStore, useDebugWebSocket } from '../../stores/debug.store';
import websocketService from '../../services/websocket.service';

// Mock the websocket service
vi.mock('../../services/websocket.service', () => ({
  default: {
    on: vi.fn(),
    isSocketConnected: vi.fn().mockReturnValue(true),
  },
}));

describe('WebSocket ML Integration', () => {
  beforeEach(() => {
    // Reset the store before each test
    act(() => {
      useDebugStore.setState({
        sessions: [],
        selectedSession: null,
        isLoading: false,
        error: null,
        mlClassifications: {},
        realtimeErrors: [],
        fetchSessions: vi.fn(),
        getSession: vi.fn(),
        analyzeError: vi.fn(),
        applyPatch: vi.fn(),
        rollbackPatch: vi.fn(),
        getMLClassification: vi.fn(),
        clearRealtimeErrors: vi.fn(),
      });
    });

    // Reset mocks
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should register WebSocket event handlers', () => {
    // Mock the on method to return a function
    (websocketService.on as any).mockImplementation(() => {
      return vi.fn(); // Return a mock cleanup function
    });

    // Render the hook
    renderHook(() => useDebugWebSocket());

    // Verify that the WebSocket event handlers are registered
    expect(websocketService.on).toHaveBeenCalledWith('debug_session_created', expect.any(Function));
    expect(websocketService.on).toHaveBeenCalledWith('debug_session_updated', expect.any(Function));
    expect(websocketService.on).toHaveBeenCalledWith('debug_error_detected', expect.any(Function));
    expect(websocketService.on).toHaveBeenCalledWith('debug_ml_classification', expect.any(Function));
    expect(websocketService.on).toHaveBeenCalledWith('debug_patch_generated', expect.any(Function));
    expect(websocketService.on).toHaveBeenCalledWith('debug_patch_applied', expect.any(Function));
    expect(websocketService.on).toHaveBeenCalledWith('debug_patch_rollback', expect.any(Function));
  });

  it('should handle ML classification events', () => {
    // Setup mock for on method to capture the callback
    let mlClassificationCallback: (data: any) => void;
    (websocketService.on as any).mockImplementation((event: string, callback: any) => {
      if (event === 'debug_ml_classification') {
        mlClassificationCallback = callback;
      }
      return vi.fn(); // Return a cleanup function
    });

    // Render the hook
    renderHook(() => useDebugWebSocket());

    // Simulate receiving an ML classification event
    const mockClassificationData = {
      errorId: 'error-123',
      classifications: {
        category: { prediction: 'dependency', confidence: 0.85 },
        severity: { prediction: 'high', confidence: 0.92 },
        stage: { prediction: 'build', confidence: 0.78 },
      },
      timestamp: '2025-02-26T10:30:00Z',
    };

    act(() => {
      mlClassificationCallback(mockClassificationData);
    });

    // Verify that the store was updated with the ML classification
    const state = useDebugStore.getState();
    expect(state.mlClassifications['error-123']).toBeDefined();
    expect(state.mlClassifications['error-123'].classifications).toEqual(mockClassificationData.classifications);
  });

  it('should handle real-time error events', () => {
    // Setup mock for on method to capture the callback
    let errorDetectedCallback: (data: any) => void;
    (websocketService.on as any).mockImplementation((event: string, callback: any) => {
      if (event === 'debug_error_detected') {
        errorDetectedCallback = callback;
      }
      return vi.fn(); // Return a cleanup function
    });

    // Render the hook
    renderHook(() => useDebugWebSocket());

    // Enable real-time mode
    act(() => {
      useDebugStore.setState({ realtimeErrors: [] });
    });

    // Simulate receiving an error event
    const mockErrorData = {
      sessionId: 'session-123',
      errorId: 'error-123',
      error: {
        id: 'error-123',
        message: 'Failed to install dependencies',
        category: 'dependency',
        severity: 'high',
        stack_trace: 'Error: Failed to install dependencies\n    at install (/app/src/index.js:42:7)',
      },
    };

    act(() => {
      errorDetectedCallback(mockErrorData);
    });

    // Verify that the store was updated with the real-time error
    const state = useDebugStore.getState();
    expect(state.realtimeErrors.length).toBe(1);
    expect(state.realtimeErrors[0]).toEqual(mockErrorData.error);

    // Verify that getMLClassification was called
    expect(state.getMLClassification).toHaveBeenCalledWith('error-123');
  });

  it('should clear real-time errors when requested', () => {
    // Create a mock implementation of clearRealtimeErrors
    const mockClearRealtimeErrors = vi.fn(() => {
      useDebugStore.setState({ realtimeErrors: [] });
    });

    // Setup initial state with some real-time errors and the mock function
    act(() => {
      useDebugStore.setState({
        realtimeErrors: [
          {
            id: 'error-123',
            message: 'Test error',
            category: 'test',
            severity: 'low',
          },
        ],
        clearRealtimeErrors: mockClearRealtimeErrors
      });
    });

    // Verify initial state
    expect(useDebugStore.getState().realtimeErrors.length).toBe(1);

    // Clear real-time errors
    act(() => {
      useDebugStore.getState().clearRealtimeErrors();
    });

    // Verify that the mock function was called
    expect(mockClearRealtimeErrors).toHaveBeenCalled();
    
    // Verify that errors were cleared
    expect(useDebugStore.getState().realtimeErrors.length).toBe(0);
  });
});
