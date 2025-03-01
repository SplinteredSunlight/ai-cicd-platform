import { describe, test, expect, vi, beforeEach } from 'vitest';
import { useAuthStore } from '../../stores/auth.store';
import { api } from '../../config/api';

// Mock the API module
vi.mock('../../config/api', () => ({
  api: {
    post: vi.fn(),
    defaults: {
      headers: {
        common: {}
      }
    }
  },
  endpoints: {
    auth: {
      login: '/api/v1/auth/token'
    }
  }
}));

describe('Auth Store', () => {
  // Reset the store before each test
  beforeEach(() => {
    // Clear the store
    const store = useAuthStore.getState();
    store.logout();
    
    // Reset mocks
    vi.clearAllMocks();
    
    // Clear localStorage
    localStorage.clear();
  });

  describe('login', () => {
    test('successfully logs in with development credentials', async () => {
      // Get the store actions
      const { login, isAuthenticated, user, error } = useAuthStore.getState();
      
      // Initial state should be not authenticated
      expect(isAuthenticated).toBe(false);
      expect(user).toBeNull();
      expect(error).toBeNull();
      
      // Login with development credentials
      await login('admin@example.com', 'admin123');
      
      // Get the updated state
      const newState = useAuthStore.getState();
      
      // Should be authenticated
      expect(newState.isAuthenticated).toBe(true);
      expect(newState.user).not.toBeNull();
      expect(newState.user?.email).toBe('admin@example.com');
      expect(newState.user?.role).toBe('admin');
      expect(newState.error).toBeNull();
      
      // Should store token in localStorage
      expect(localStorage.getItem('auth_token')).toBe('mock-jwt-token');
      
      // Should set Authorization header
      expect(api.defaults.headers.common['Authorization']).toBe('Bearer mock-jwt-token');
      
      // API should not be called
      expect(api.post).not.toHaveBeenCalled();
    });
    
    test('successfully logs in with API credentials', async () => {
      // Mock API response
      const mockResponse = {
        data: {
          data: {
            user: {
              id: '2',
              name: 'API User',
              email: 'api@example.com',
              role: 'user'
            },
            token: 'api-jwt-token'
          }
        }
      };
      
      (api.post as any).mockResolvedValue(mockResponse);
      
      // Get the store actions
      const { login } = useAuthStore.getState();
      
      // Login with non-development credentials
      await login('api@example.com', 'password123');
      
      // Get the updated state
      const newState = useAuthStore.getState();
      
      // Should be authenticated
      expect(newState.isAuthenticated).toBe(true);
      expect(newState.user).not.toBeNull();
      expect(newState.user?.email).toBe('api@example.com');
      expect(newState.user?.role).toBe('user');
      expect(newState.error).toBeNull();
      
      // Should store token in localStorage
      expect(localStorage.getItem('auth_token')).toBe('api-jwt-token');
      
      // Should set Authorization header
      expect(api.defaults.headers.common['Authorization']).toBe('Bearer api-jwt-token');
      
      // API should be called
      expect(api.post).toHaveBeenCalledWith('/api/v1/auth/token', {
        email: 'api@example.com',
        password: 'password123'
      });
    });
    
    test('handles login failure', async () => {
      // Mock API error
      const mockError = new Error('Invalid credentials');
      (api.post as any).mockRejectedValue(mockError);
      
      // Get the store actions
      const { login } = useAuthStore.getState();
      
      // Login with invalid credentials
      await login('invalid@example.com', 'wrongpassword');
      
      // Get the updated state
      const newState = useAuthStore.getState();
      
      // Should not be authenticated
      expect(newState.isAuthenticated).toBe(false);
      expect(newState.user).toBeNull();
      expect(newState.error).toBe('Invalid credentials');
      
      // Should not store token in localStorage
      expect(localStorage.getItem('auth_token')).toBeNull();
      
      // Should not set Authorization header
      expect(api.defaults.headers.common['Authorization']).toBeUndefined();
      
      // API should be called
      expect(api.post).toHaveBeenCalledWith('/api/v1/auth/token', {
        email: 'invalid@example.com',
        password: 'wrongpassword'
      });
    });
  });
  
  describe('logout', () => {
    test('successfully logs out', async () => {
      // First login
      const { login, logout } = useAuthStore.getState();
      await login('admin@example.com', 'admin123');
      
      // Verify logged in
      expect(useAuthStore.getState().isAuthenticated).toBe(true);
      expect(localStorage.getItem('auth_token')).toBe('mock-jwt-token');
      
      // Logout
      logout();
      
      // Get the updated state
      const newState = useAuthStore.getState();
      
      // Should not be authenticated
      expect(newState.isAuthenticated).toBe(false);
      expect(newState.user).toBeNull();
      expect(newState.error).toBeNull();
      
      // Should remove token from localStorage
      expect(localStorage.getItem('auth_token')).toBeNull();
      
      // Should remove Authorization header
      expect(api.defaults.headers.common['Authorization']).toBeUndefined();
    });
  });
});
