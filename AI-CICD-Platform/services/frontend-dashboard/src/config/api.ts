import axios from 'axios';

// Create axios instance with default config
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if it exists
const token = localStorage.getItem('auth_token');
if (token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

// API endpoints
export const endpoints = {
  auth: {
    login: '/auth/login',
    logout: '/auth/logout',
  },
  metrics: {
    summary: '/metrics/summary',
    history: '/metrics/history',
  },
  pipelines: {
    list: '/pipelines',
    generate: '/pipelines/generate',
    validate: '/pipelines/validate',
    execute: '/pipelines/execute',
  },
  security: {
    vulnerabilities: '/security/vulnerabilities',
    scans: '/security/scans',
    startScan: '/security/scans/start',
    scan: '/security/scans/:id',
  },
  debug: {
    sessions: '/debug/sessions',
    session: '/debug/sessions/:id',
    analyze: '/debug/analyze',
    applyPatch: '/debug/sessions/:sessionId/patches/:patchId/apply',
    rollbackPatch: '/debug/sessions/:sessionId/patches/:patchId/rollback',
  },
};

// API response types
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

// User types
export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user';
}

// Pipeline types
export interface Pipeline {
  id: string;
  name: string;
  repository: string;
  branch: string;
  commit_hash: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
}

// Security types
export interface Vulnerability {
  id: string;
  title: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  affected_component: string;
  fix_available: boolean;
  created_at: string;
}

export interface SecurityScan {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  vulnerabilities_found: number;
  started_at: string;
  completed_at?: string;
}

// Debug types
export interface PipelineError {
  id: string;
  message: string;
  category: string;
  severity: string;
  stack_trace?: string;
}

export interface PatchSolution {
  id: string;
  error_id: string;
  description: string;
  type: string;
  applied: boolean;
  success?: boolean;
  is_reversible: boolean;
}

export interface DebugSession {
  id: string;
  pipeline_id: string;
  status: string;
  errors: PipelineError[];
  patches: PatchSolution[];
  created_at: string;
  updated_at: string;
}

// Metrics types
export interface ServiceHealth {
  status: 'healthy' | 'degraded' | 'down';
  response_time: number;
  error_rate: number;
  last_error?: string;
  last_checked: string;
}

export interface MetricsSummary {
  total_pipelines: number;
  active_pipelines: number;
  success_rate: number;
  avg_duration: number;
  service_health: Record<string, ServiceHealth>;
}
