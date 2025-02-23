import { create } from 'zustand';
import { api, endpoints, AuthResponse, LoginRequest } from '../config/api';
import jwt_decode from 'jwt-decode';

interface AuthState {
  token: string | null;
  user: {
    id: string;
    username: string;
    email: string;
    roles: string[];
  } | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: localStorage.getItem('auth_token'),
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,

  login: async (credentials) => {
    try {
      set({ isLoading: true, error: null });
      
      const response = await api.post<AuthResponse>(
        endpoints.auth.login,
        credentials
      );
      
      const { access_token } = response.data;
      
      // Decode token to get user info
      const decoded: any = jwt_decode(access_token);
      
      // Store token
      localStorage.setItem('auth_token', access_token);
      
      set({
        token: access_token,
        user: {
          id: decoded.sub,
          username: decoded.username,
          email: decoded.email,
          roles: decoded.roles,
        },
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.message || 'Login failed',
        isLoading: false,
      });
      throw error;
    }
  },

  logout: async () => {
    try {
      // Call logout endpoint if needed
      await api.post(endpoints.auth.logout);
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage and state
      localStorage.removeItem('auth_token');
      set({
        token: null,
        user: null,
        isAuthenticated: false,
        error: null,
      });
    }
  },

  checkAuth: async () => {
    try {
      set({ isLoading: true });
      
      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('No token found');
      }

      // Verify token is valid
      const decoded: any = jwt_decode(token);
      const currentTime = Date.now() / 1000;
      
      if (decoded.exp < currentTime) {
        throw new Error('Token expired');
      }

      // Set authenticated state
      set({
        token,
        user: {
          id: decoded.sub,
          username: decoded.username,
          email: decoded.email,
          roles: decoded.roles,
        },
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      // Clear invalid auth state
      localStorage.removeItem('auth_token');
      set({
        token: null,
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },
}));
