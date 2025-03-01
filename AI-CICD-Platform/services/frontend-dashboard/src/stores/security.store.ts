import { create } from 'zustand';
import { api, endpoints, Vulnerability, SecurityScan } from '../config/api';
import websocketService from '../services/websocket.service';
import { useEffect } from 'react';

interface SecurityState {
  vulnerabilities: Vulnerability[];
  scans: SecurityScan[];
  selectedScan: SecurityScan | null;
  isLoading: boolean;
  error: string | null;
  fetchVulnerabilities: () => Promise<void>;
  fetchScans: () => Promise<void>;
  startScan: () => Promise<void>;
  getScanDetails: (scanId: string) => Promise<void>;
}

export const useSecurityStore = create<SecurityState>((set, get) => ({
  vulnerabilities: [],
  scans: [],
  selectedScan: null,
  isLoading: false,
  error: null,

  fetchVulnerabilities: async () => {
    set({ isLoading: true, error: null });

    try {
      const response = await api.get(endpoints.security.vulnerabilities);
      set({
        vulnerabilities: response.data.data,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch vulnerabilities',
      });
    }
  },

  fetchScans: async () => {
    set({ isLoading: true, error: null });

    try {
      const response = await api.get(endpoints.security.scans);
      set({
        scans: response.data.data,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch scans',
      });
    }
  },

  startScan: async () => {
    set({ isLoading: true, error: null });

    try {
      const response = await api.post(endpoints.security.startScan);
      const newScan = response.data.data;
      
      set((state) => ({
        scans: [newScan, ...state.scans],
        selectedScan: newScan,
        isLoading: false,
        error: null,
      }));
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to start scan',
      });
    }
  },

  getScanDetails: async (scanId: string) => {
    set({ isLoading: true, error: null });

    try {
      const response = await api.get(
        endpoints.security.scan.replace(':id', scanId)
      );
      
      set({
        selectedScan: response.data.data,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch scan details',
      });
    }
  },
}));

// Custom hook for WebSocket integration
export const useSecurityWebSocket = () => {
  const { fetchVulnerabilities, fetchScans, getScanDetails, selectedScan } = useSecurityStore();

  useEffect(() => {
    // Handle new vulnerability detected event
    const unsubscribeVulnerabilityDetected = websocketService.on('security_vulnerability_detected', (data) => {
      console.log('WebSocket: New vulnerability detected', data);
      fetchVulnerabilities();
    });

    // Handle vulnerability status updated event
    const unsubscribeVulnerabilityUpdated = websocketService.on('security_vulnerability_updated', (data) => {
      console.log('WebSocket: Vulnerability updated', data);
      fetchVulnerabilities();
    });

    // Handle scan started event
    const unsubscribeScanStarted = websocketService.on('security_scan_started', (data) => {
      console.log('WebSocket: Security scan started', data);
      fetchScans();
    });

    // Handle scan status updated event
    const unsubscribeScanUpdated = websocketService.on('security_scan_updated', (data) => {
      console.log('WebSocket: Security scan updated', data);
      fetchScans();
      
      // If this is the currently selected scan, refresh it
      if (selectedScan && data.scanId === selectedScan.id) {
        getScanDetails(data.scanId);
      }
    });

    // Handle scan completed event
    const unsubscribeScanCompleted = websocketService.on('security_scan_completed', (data) => {
      console.log('WebSocket: Security scan completed', data);
      fetchScans();
      fetchVulnerabilities(); // Refresh vulnerabilities as new ones might have been found
      
      // If this is the currently selected scan, refresh it
      if (selectedScan && data.scanId === selectedScan.id) {
        getScanDetails(data.scanId);
      }
    });

    // Cleanup function to unsubscribe from all events
    return () => {
      unsubscribeVulnerabilityDetected();
      unsubscribeVulnerabilityUpdated();
      unsubscribeScanStarted();
      unsubscribeScanUpdated();
      unsubscribeScanCompleted();
    };
  }, [fetchVulnerabilities, fetchScans, getScanDetails, selectedScan]);
};
