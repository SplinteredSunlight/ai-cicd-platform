import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material';
import { theme } from './config/theme';
import MainLayout from './layouts/MainLayout';
import AuthLayout from './layouts/AuthLayout';
import LoginPage from './pages/auth/LoginPage';
import DashboardPage from './pages/dashboard/DashboardPage';
import PipelinesPage from './pages/pipelines/PipelinesPage';
import SecurityPage from './pages/security/SecurityPage';
import DebuggerPage from './pages/debugger/DebuggerPage';
import SettingsPage from './pages/settings/SettingsPage';
import { useAuthStore } from './stores/auth.store';

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? children : <Navigate to="/login" />;
}

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <Router>
        <Routes>
          {/* Auth Routes */}
          <Route
            path="/login"
            element={
              <AuthLayout>
                <LoginPage />
              </AuthLayout>
            }
          />

          {/* Protected Routes */}
          <Route
            path="/"
            element={
              <PrivateRoute>
                <MainLayout>
                  <DashboardPage />
                </MainLayout>
              </PrivateRoute>
            }
          />
          <Route
            path="/pipelines"
            element={
              <PrivateRoute>
                <MainLayout>
                  <PipelinesPage />
                </MainLayout>
              </PrivateRoute>
            }
          />
          <Route
            path="/security"
            element={
              <PrivateRoute>
                <MainLayout>
                  <SecurityPage />
                </MainLayout>
              </PrivateRoute>
            }
          />
          <Route
            path="/debugger"
            element={
              <PrivateRoute>
                <MainLayout>
                  <DebuggerPage />
                </MainLayout>
              </PrivateRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <PrivateRoute>
                <MainLayout>
                  <SettingsPage />
                </MainLayout>
              </PrivateRoute>
            }
          />

          {/* Catch-all redirect to dashboard */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}
