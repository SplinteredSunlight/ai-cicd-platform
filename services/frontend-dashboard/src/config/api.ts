import axios from 'axios';

// API base URL from environment variable or default
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for authentication
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Clear invalid token
      localStorage.removeItem('auth_token');
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const endpoints = {
  auth: {
    login: '/api/v1/auth/token',
    logout: '/api/v1/auth/logout',
    refresh: '/api/v1/auth/refresh',
  },
  pipelines: {
    list: '/api/v1/pipeline/list',
    generate: '/api/v1/pipeline/generate',
    validate: '/api/v1/pipeline/validate',
    execute: '/api/v1/pipeline/execute',
  },
  security: {
    scan: '/api/v1/security/scan',
    vulnerabilities: '/api/v1/security/vulnerabilities',
    sbom: '/api/v1/security/sbom',
  },
  debug: {
    analyze: '/api/v1/debug/analyze',
    patch: '/api/v1/debug/patch',
    sessions: '/api/v1/debug/sessions',
  },
  metrics: {
    summary: '/api/v1/metrics/summary',
    services: '/api/v1/metrics/services',
    alerts: '/api/v1/metrics/alerts',
  },
} as const;

// API response types
export interface ApiResponse<T = any> {
  status: 'success' | 'error';
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}

// Authentication types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
}

// Pipeline types
export interface Pipeline {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  config: Record<string, any>;
}

// Security types
export interface SecurityScan {
  id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  vulnerabilities: Vulnerability[];
  created_at: string;
  completed_at?: string;
}

export interface Vulnerability {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  affected_component: string;
  fix_available: boolean;
  fix_description?: string;
}

// Debug types
export interface DebugSession {
  id: string;
  pipeline_id: string;
  status: 'active' | 'completed';
  errors: PipelineError[];
  patches: PatchSolution[];
  created_at: string;
  updated_at: string;
}

export interface PipelineError {
  id: string;
  message: string;
  stack_trace?: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  category: string;
  context: Record<string, any>;
}

export interface PatchSolution {
  id: string;
  error_id: string;
  type: string;
  description: string;
  script: string;
  is_reversible: boolean;
  applied: boolean;
  success?: boolean;
}

// Metrics types
export interface MetricsSummary {
  total_pipelines: number;
  active_pipelines: number;
  failed_pipelines: number;
  total_vulnerabilities: number;
  critical_vulnerabilities: number;
  service_health: Record<string, ServiceHealth>;
}

export interface ServiceHealth {
  status: 'healthy' | 'degraded' | 'down';
  response_time: number;
  error_rate: number;
  last_error?: string;
  last_checked: string;
}
