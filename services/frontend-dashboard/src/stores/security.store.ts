import { create } from 'zustand';
import { api, endpoints, SecurityScan, Vulnerability, ApiResponse } from '../config/api';

interface SecurityState {
  scans: SecurityScan[];
  activeScan: SecurityScan | null;
  vulnerabilities: Vulnerability[];
  isLoading: boolean;
  error: string | null;
  // Actions
  startScan: (pipelineId: string) => Promise<SecurityScan>;
  fetchScans: () => Promise<void>;
  fetchVulnerabilities: () => Promise<void>;
  getScanStatus: (scanId: string) => Promise<void>;
  setActiveScan: (scan: SecurityScan | null) => void;
  // Filters and stats
  filterVulnerabilities: (severity: string[]) => Vulnerability[];
  getVulnerabilityStats: () => {
    total: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}

export const useSecurityStore = create<SecurityState>((set, get) => ({
  scans: [],
  activeScan: null,
  vulnerabilities: [],
  isLoading: false,
  error: null,

  startScan: async (pipelineId: string) => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await api.post<ApiResponse<SecurityScan>>(
        endpoints.security.scan,
        { pipeline_id: pipelineId }
      );
      
      const newScan = response.data.data!;
      
      set(state => ({
        scans: [...state.scans, newScan],
        activeScan: newScan,
        isLoading: false,
      }));

      return newScan;
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Failed to start security scan',
        isLoading: false,
      });
      throw error;
    }
  },

  fetchScans: async () => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await api.get<ApiResponse<SecurityScan[]>>(
        endpoints.security.scan
      );
      
      set({
        scans: response.data.data || [],
        isLoading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Failed to fetch security scans',
        isLoading: false,
      });
      throw error;
    }
  },

  fetchVulnerabilities: async () => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await api.get<ApiResponse<Vulnerability[]>>(
        endpoints.security.vulnerabilities
      );
      
      set({
        vulnerabilities: response.data.data || [],
        isLoading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Failed to fetch vulnerabilities',
        isLoading: false,
      });
      throw error;
    }
  },

  getScanStatus: async (scanId: string) => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await api.get<ApiResponse<SecurityScan>>(
        `${endpoints.security.scan}/${scanId}`
      );
      
      const updatedScan = response.data.data!;
      
      set(state => ({
        scans: state.scans.map(s =>
          s.id === scanId ? updatedScan : s
        ),
        activeScan: state.activeScan?.id === scanId
          ? updatedScan
          : state.activeScan,
        isLoading: false,
      }));
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Failed to get scan status',
        isLoading: false,
      });
      throw error;
    }
  },

  setActiveScan: (scan: SecurityScan | null) => {
    set({ activeScan: scan });
  },

  filterVulnerabilities: (severities: string[]) => {
    const { vulnerabilities } = get();
    if (!severities.length) return vulnerabilities;
    return vulnerabilities.filter(v => severities.includes(v.severity));
  },

  getVulnerabilityStats: () => {
    const { vulnerabilities } = get();
    return {
      total: vulnerabilities.length,
      critical: vulnerabilities.filter(v => v.severity === 'critical').length,
      high: vulnerabilities.filter(v => v.severity === 'high').length,
      medium: vulnerabilities.filter(v => v.severity === 'medium').length,
      low: vulnerabilities.filter(v => v.severity === 'low').length,
    };
  },
}));

// Optional: Subscribe to security scan updates via WebSocket
if (typeof window !== 'undefined') {
  const ws = new WebSocket(
    `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/security`
  );

  ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    
    // Update scan status in store
    useSecurityStore.setState(state => ({
      scans: state.scans.map(s =>
        s.id === update.scan_id
          ? { ...s, ...update }
          : s
      ),
      // Update active scan if it's the one being updated
      activeScan: state.activeScan?.id === update.scan_id
        ? { ...state.activeScan, ...update }
        : state.activeScan,
    }));
  };

  ws.onerror = (error) => {
    console.error('Security WebSocket error:', error);
  };
}
