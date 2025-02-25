import { create } from 'zustand';
import { api, endpoints, Vulnerability, SecurityScan } from '../config/api';

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
