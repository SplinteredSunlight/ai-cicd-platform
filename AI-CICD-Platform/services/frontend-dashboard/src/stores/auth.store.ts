import { create } from 'zustand';
import { api, endpoints, ApiResponse } from '../config/api';

interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user';
}

interface AuthResponse {
  user: User;
  token: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });

    try {
      // For development, accept test credentials
      if (email === 'admin@example.com' && password === 'admin123') {
        const mockUser = {
          id: '1',
          name: 'Admin User',
          email: 'admin@example.com',
          role: 'admin' as const,
        };
        const mockToken = 'mock-jwt-token';

        // Store token in localStorage
        localStorage.setItem('auth_token', mockToken);
        // Update axios default headers
        api.defaults.headers.common['Authorization'] = `Bearer ${mockToken}`;

        set({
          user: mockUser,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
        return;
      }

      // In production, this would make a real API call
      const response = await api.post<ApiResponse<AuthResponse>>(
        endpoints.auth.login,
        { email, password }
      );

      const { user, token } = response.data.data;

      // Store token in localStorage
      localStorage.setItem('auth_token', token);
      // Update axios default headers
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;

      set({
        user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to login',
      });
    }
  },

  logout: () => {
    // Remove token from localStorage
    localStorage.removeItem('auth_token');
    // Remove Authorization header
    delete api.defaults.headers.common['Authorization'];

    set({
      user: null,
      isAuthenticated: false,
      error: null,
    });
  },
}));
