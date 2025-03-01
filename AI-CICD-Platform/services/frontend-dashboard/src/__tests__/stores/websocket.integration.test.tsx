import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { usePipelineStore, usePipelineWebSocket } from '../../stores/pipeline.store';
import { useDebugStore, useDebugWebSocket } from '../../stores/debug.store';
import websocketService from '../../services/websocket.service';

// Mock the websocket service
vi.mock('../../services/websocket.service', () => ({
  default: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    on: vi.fn(),
  },
}));

// Mock API calls
vi.mock('../../config/api', () => ({
  api: {
    get: vi.fn().mockResolvedValue({ data: { data: [] } }),
    post: vi.fn().mockResolvedValue({ data: { data: {} } }),
  },
  endpoints: {
    pipelines: {
      list: '/api/pipelines',
      generate: '/api/pipelines/generate',
      validate: '/api/pipelines/validate',
      execute: '/api/pipelines/execute',
    },
    debug: {
      sessions: '/api/debug/sessions',
      session: '/api/debug/sessions/:id',
      analyze: '/api/debug/analyze',
      applyPatch: '/api/debug/sessions/:sessionId/patches/:patchId/apply',
      rollbackPatch: '/api/debug/sessions/:sessionId/patches/:patchId/rollback',
    },
  },
}));

describe('WebSocket Integration with Stores', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('Pipeline WebSocket Integration', () => {
    it('should register event handlers for pipeline events', () => {
      // Setup mock for on method
      const mockUnsubscribe = vi.fn();
      (websocketService.on as any).mockReturnValue(mockUnsubscribe);

      // Call the hook directly
      usePipelineWebSocket();

      // Verify that event handlers were registered
      expect(websocketService.on).toHaveBeenCalledWith('pipeline_created', expect.any(Function));
      expect(websocketService.on).toHaveBeenCalledWith('pipeline_updated', expect.any(Function));
      expect(websocketService.on).toHaveBeenCalledWith('pipeline_status_changed', expect.any(Function));
      expect(websocketService.on).toHaveBeenCalledWith('pipeline_deleted', expect.any(Function));
    });

    it('should fetch pipelines when receiving pipeline events', async () => {
      // Setup mock for on method to capture the callback
      const eventCallbacks: Record<string, Function> = {};
      (websocketService.on as any).mockImplementation((event: string, callback: Function) => {
        eventCallbacks[event] = callback;
        return vi.fn();
      });

      // Setup spy on fetchPipelines
      const fetchPipelinesSpy = vi.spyOn(usePipelineStore.getState(), 'fetchPipelines');

      // Call the hook directly
      usePipelineWebSocket();

      // Simulate receiving a pipeline_created event
      await eventCallbacks['pipeline_created']({ id: '123' });

      // Verify that fetchPipelines was called
      expect(fetchPipelinesSpy).toHaveBeenCalled();

      // Simulate receiving a pipeline_updated event
      await eventCallbacks['pipeline_updated']({ id: '123' });

      // Verify that fetchPipelines was called again
      expect(fetchPipelinesSpy).toHaveBeenCalledTimes(2);
    });
  });

  describe('Debug WebSocket Integration', () => {
    it('should register event handlers for debug events', () => {
      // Setup mock for on method
      const mockUnsubscribe = vi.fn();
      (websocketService.on as any).mockReturnValue(mockUnsubscribe);

      // Call the hook directly
      useDebugWebSocket();

      // Verify that event handlers were registered
      expect(websocketService.on).toHaveBeenCalledWith('debug_session_created', expect.any(Function));
      expect(websocketService.on).toHaveBeenCalledWith('debug_session_updated', expect.any(Function));
      expect(websocketService.on).toHaveBeenCalledWith('debug_error_detected', expect.any(Function));
      expect(websocketService.on).toHaveBeenCalledWith('debug_patch_generated', expect.any(Function));
      expect(websocketService.on).toHaveBeenCalledWith('debug_patch_applied', expect.any(Function));
      expect(websocketService.on).toHaveBeenCalledWith('debug_patch_rollback', expect.any(Function));
    });

    it('should fetch sessions when receiving debug events', async () => {
      // Setup mock for on method to capture the callback
      const eventCallbacks: Record<string, Function> = {};
      (websocketService.on as any).mockImplementation((event: string, callback: Function) => {
        eventCallbacks[event] = callback;
        return vi.fn();
      });

      // Setup spy on fetchSessions
      const fetchSessionsSpy = vi.spyOn(useDebugStore.getState(), 'fetchSessions');

      // Setup the store with a selected session
      useDebugStore.setState({
        selectedSession: { id: '123', errors: [], patches: [] } as any,
      });

      // Setup spy on getSession
      const getSessionSpy = vi.spyOn(useDebugStore.getState(), 'getSession');

      // Call the hook directly
      useDebugWebSocket();

      // Simulate receiving a debug_session_created event
      await eventCallbacks['debug_session_created']({ sessionId: '123' });

      // Verify that fetchSessions was called
      expect(fetchSessionsSpy).toHaveBeenCalled();

      // Simulate receiving a debug_patch_generated event for the selected session
      await eventCallbacks['debug_patch_generated']({ sessionId: '123' });

      // Verify that getSession was called for the selected session
      expect(getSessionSpy).toHaveBeenCalledWith('123');
    });
  });
});
