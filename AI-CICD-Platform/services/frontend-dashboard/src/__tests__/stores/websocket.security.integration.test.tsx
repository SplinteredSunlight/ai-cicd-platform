import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import websocketService from '../../services/websocket.service';
import { useSecurityStore, useSecurityWebSocket } from '../../stores/security.store';

// Mock the WebSocket service
vi.mock('../../services/websocket.service', () => ({
  default: {
    on: vi.fn(),
    isSocketConnected: vi.fn(),
  },
}));

describe('Security WebSocket Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (websocketService.isSocketConnected as any).mockReturnValue(true);
  });

  afterEach(() => {
    // Reset the store state
    act(() => {
      useSecurityStore.setState({
        vulnerabilities: [],
        scans: [],
        selectedScan: null,
        isLoading: false,
        error: null,
      });
    });
  });

  it('should register WebSocket event handlers', () => {
    // Mock the on method to return a function
    (websocketService.on as any).mockImplementation(() => {
      return vi.fn(); // Return a mock cleanup function
    });

    // Render the hook
    renderHook(() => useSecurityWebSocket());

    // Verify that the WebSocket event handlers are registered
    expect(websocketService.on).toHaveBeenCalledWith('security_vulnerability_detected', expect.any(Function));
    expect(websocketService.on).toHaveBeenCalledWith('security_vulnerability_updated', expect.any(Function));
    expect(websocketService.on).toHaveBeenCalledWith('security_scan_started', expect.any(Function));
    expect(websocketService.on).toHaveBeenCalledWith('security_scan_updated', expect.any(Function));
    expect(websocketService.on).toHaveBeenCalledWith('security_scan_completed', expect.any(Function));
  });

  it('should update store when vulnerability detected event is received', async () => {
    // Mock the fetchVulnerabilities method
    const fetchVulnerabilitiesMock = vi.fn();
    vi.spyOn(useSecurityStore.getState(), 'fetchVulnerabilities').mockImplementation(fetchVulnerabilitiesMock);

    // Set up the WebSocket event callback capture
    let vulnerabilityDetectedCallback: (data: any) => void;
    (websocketService.on as any).mockImplementation((event: string, callback: any) => {
      if (event === 'security_vulnerability_detected') {
        vulnerabilityDetectedCallback = callback;
      }
      return vi.fn();
    });

    // Render the hook
    renderHook(() => useSecurityWebSocket());

    // Simulate receiving a vulnerability detected event
    act(() => {
      vulnerabilityDetectedCallback({
        vulnerabilityId: 'vuln-123',
        vulnerability: {
          id: 'vuln-123',
          title: 'Test Vulnerability',
          severity: 'high',
          affected_component: 'test-component',
          fix_available: true,
        },
      });
    });

    // Verify that fetchVulnerabilities was called
    expect(fetchVulnerabilitiesMock).toHaveBeenCalled();
  });

  it('should update store when scan completed event is received', async () => {
    // Mock the methods
    const fetchScansMock = vi.fn();
    const fetchVulnerabilitiesMock = vi.fn();
    const getScanDetailsMock = vi.fn();
    
    vi.spyOn(useSecurityStore.getState(), 'fetchScans').mockImplementation(fetchScansMock);
    vi.spyOn(useSecurityStore.getState(), 'fetchVulnerabilities').mockImplementation(fetchVulnerabilitiesMock);
    vi.spyOn(useSecurityStore.getState(), 'getScanDetails').mockImplementation(getScanDetailsMock);

    // Set up the selected scan
    act(() => {
      useSecurityStore.setState({
        selectedScan: {
          id: 'scan-123',
          status: 'completed',
          vulnerabilities_found: 5,
          started_at: '2025-02-27T12:00:00Z',
          completed_at: '2025-02-27T12:05:00Z',
        },
      });
    });

    // Set up the WebSocket event callback capture
    let scanCompletedCallback: (data: any) => void;
    (websocketService.on as any).mockImplementation((event: string, callback: any) => {
      if (event === 'security_scan_completed') {
        scanCompletedCallback = callback;
      }
      return vi.fn();
    });

    // Render the hook
    renderHook(() => useSecurityWebSocket());

    // Simulate receiving a scan completed event for the selected scan
    act(() => {
      scanCompletedCallback({
        scanId: 'scan-123',
        scan: {
          id: 'scan-123',
          status: 'completed',
          vulnerabilities_found: 5,
          started_at: '2025-02-27T12:00:00Z',
          completed_at: '2025-02-27T12:05:00Z',
        },
      });
    });

    // Verify that the methods were called
    expect(fetchScansMock).toHaveBeenCalled();
    expect(fetchVulnerabilitiesMock).toHaveBeenCalled();
    expect(getScanDetailsMock).toHaveBeenCalledWith('scan-123');
  });

  it('should update store when scan updated event is received for a different scan', async () => {
    // Mock the methods
    const fetchScansMock = vi.fn();
    const getScanDetailsMock = vi.fn();
    
    vi.spyOn(useSecurityStore.getState(), 'fetchScans').mockImplementation(fetchScansMock);
    vi.spyOn(useSecurityStore.getState(), 'getScanDetails').mockImplementation(getScanDetailsMock);

    // Set up the selected scan
    act(() => {
      useSecurityStore.setState({
        selectedScan: {
          id: 'scan-123',
          status: 'running',
          vulnerabilities_found: 2,
          started_at: '2025-02-27T12:00:00Z',
          completed_at: undefined,
        },
      });
    });

    // Set up the WebSocket event callback capture
    let scanUpdatedCallback: (data: any) => void;
    (websocketService.on as any).mockImplementation((event: string, callback: any) => {
      if (event === 'security_scan_updated') {
        scanUpdatedCallback = callback;
      }
      return vi.fn();
    });

    // Render the hook
    renderHook(() => useSecurityWebSocket());

    // Simulate receiving a scan updated event for a different scan
    act(() => {
      scanUpdatedCallback({
        scanId: 'scan-456',
        scan: {
          id: 'scan-456',
          status: 'running',
          vulnerabilities_found: 3,
          started_at: '2025-02-27T12:10:00Z',
          completed_at: undefined,
        },
      });
    });

    // Verify that fetchScans was called but getScanDetails was not
    expect(fetchScansMock).toHaveBeenCalled();
    expect(getScanDetailsMock).not.toHaveBeenCalled();
  });
});
