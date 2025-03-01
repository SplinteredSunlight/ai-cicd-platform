import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import App from '../App';
import { useAuthStore } from '../stores/auth.store';

// Mock all the page components
vi.mock('../pages/auth/LoginPage', () => ({
  default: () => <div data-testid="login-page">Login Page</div>
}));

vi.mock('../pages/dashboard/DashboardPage', () => ({
  default: () => <div data-testid="dashboard-page">Dashboard Page</div>
}));

vi.mock('../pages/pipelines/PipelinesPage', () => ({
  default: () => <div data-testid="pipelines-page">Pipelines Page</div>
}));

vi.mock('../pages/security/SecurityPage', () => ({
  default: () => <div data-testid="security-page">Security Page</div>
}));

vi.mock('../pages/debugger/DebuggerPage', () => ({
  default: () => <div data-testid="debugger-page">Debugger Page</div>
}));

vi.mock('../pages/settings/SettingsPage', () => ({
  default: () => <div data-testid="settings-page">Settings Page</div>
}));

vi.mock('../layouts/MainLayout', () => ({
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="main-layout">{children}</div>
  )
}));

vi.mock('../layouts/AuthLayout', () => ({
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="auth-layout">{children}</div>
  )
}));

// Mock the auth store
vi.mock('../stores/auth.store', () => ({
  useAuthStore: vi.fn()
}));

describe('App Component', () => {
  // Helper function to render the App with a specific route
  const renderWithRoute = (initialRoute: string) => {
    return render(
      <MemoryRouter initialEntries={[initialRoute]}>
        <App />
      </MemoryRouter>
    );
  };

  describe('When user is not authenticated', () => {
    beforeEach(() => {
      // Mock the auth store to return not authenticated
      (useAuthStore as any).mockReturnValue({
        isAuthenticated: false,
        login: vi.fn(),
        logout: vi.fn(),
      });
    });

    test('redirects to login page when accessing protected route', () => {
      renderWithRoute('/');
      
      // Should redirect to login page
      expect(screen.getByTestId('auth-layout')).toBeInTheDocument();
      expect(screen.getByTestId('login-page')).toBeInTheDocument();
      expect(screen.queryByTestId('dashboard-page')).not.toBeInTheDocument();
    });

    test('renders login page when accessing /login', () => {
      renderWithRoute('/login');
      
      expect(screen.getByTestId('auth-layout')).toBeInTheDocument();
      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });

    test('redirects to login page when accessing non-existent route', () => {
      renderWithRoute('/non-existent-route');
      
      // Should redirect to login page
      expect(screen.getByTestId('auth-layout')).toBeInTheDocument();
      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });
  });

  describe('When user is authenticated', () => {
    beforeEach(() => {
      // Mock the auth store to return authenticated
      (useAuthStore as any).mockReturnValue({
        isAuthenticated: true,
        user: { id: '1', name: 'Test User', email: 'test@example.com', role: 'admin' },
        login: vi.fn(),
        logout: vi.fn(),
      });
    });

    test('renders dashboard page when accessing /', () => {
      renderWithRoute('/');
      
      expect(screen.getByTestId('main-layout')).toBeInTheDocument();
      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
    });

    test('renders pipelines page when accessing /pipelines', () => {
      renderWithRoute('/pipelines');
      
      expect(screen.getByTestId('main-layout')).toBeInTheDocument();
      expect(screen.getByTestId('pipelines-page')).toBeInTheDocument();
    });

    test('renders security page when accessing /security', () => {
      renderWithRoute('/security');
      
      expect(screen.getByTestId('main-layout')).toBeInTheDocument();
      expect(screen.getByTestId('security-page')).toBeInTheDocument();
    });

    test('renders debugger page when accessing /debugger', () => {
      renderWithRoute('/debugger');
      
      expect(screen.getByTestId('main-layout')).toBeInTheDocument();
      expect(screen.getByTestId('debugger-page')).toBeInTheDocument();
    });

    test('renders settings page when accessing /settings', () => {
      renderWithRoute('/settings');
      
      expect(screen.getByTestId('main-layout')).toBeInTheDocument();
      expect(screen.getByTestId('settings-page')).toBeInTheDocument();
    });

    test('redirects to dashboard when accessing non-existent route', () => {
      renderWithRoute('/non-existent-route');
      
      // Should redirect to dashboard
      expect(screen.getByTestId('main-layout')).toBeInTheDocument();
      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
    });

    test('redirects to dashboard when accessing /login while authenticated', () => {
      renderWithRoute('/login');
      
      // Should redirect to dashboard
      expect(screen.getByTestId('main-layout')).toBeInTheDocument();
      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
      expect(screen.queryByTestId('login-page')).not.toBeInTheDocument();
    });
  });
});
