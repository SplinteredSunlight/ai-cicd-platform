import { useEffect } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { Box, Container, Paper } from '@mui/material';
import { useAuthStore } from '../stores/auth.store';

export default function AuthLayout() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    // Redirect to dashboard if already authenticated
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
        py: 3,
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={3}
          sx={{
            p: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <Box
            component="img"
            src="/logo.png"
            alt="Logo"
            sx={{
              width: 200,
              height: 'auto',
              mb: 4,
            }}
          />
          <Outlet />
        </Paper>
      </Container>
    </Box>
  );
}
