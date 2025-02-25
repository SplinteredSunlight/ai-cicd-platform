import { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  FormControlLabel,
  Grid,
  Paper,
  Switch,
  TextField,
  Typography,
} from '@mui/material';
import { Save as SaveIcon } from '@mui/icons-material';

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    debugMode: import.meta.env.VITE_ENABLE_DEBUG_MODE === 'true',
    analytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
    pollingInterval: Number(import.meta.env.VITE_POLLING_INTERVAL) || 30000,
    maxConcurrentRequests: Number(import.meta.env.VITE_MAX_CONCURRENT_REQUESTS) || 5,
  });

  const [saved, setSaved] = useState(false);

  const handleChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
    setSettings((prev) => ({
      ...prev,
      [field]: value,
    }));
    setSaved(false);
  };

  const handleSave = () => {
    // In a real app, this would persist settings to backend/localStorage
    localStorage.setItem('app_settings', JSON.stringify(settings));
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              API Configuration
            </Typography>
            <Box sx={{ mb: 3 }}>
              <TextField
                fullWidth
                label="API URL"
                value={settings.apiUrl}
                onChange={handleChange('apiUrl')}
                margin="normal"
              />
              <TextField
                fullWidth
                type="number"
                label="Polling Interval (ms)"
                value={settings.pollingInterval}
                onChange={handleChange('pollingInterval')}
                margin="normal"
              />
              <TextField
                fullWidth
                type="number"
                label="Max Concurrent Requests"
                value={settings.maxConcurrentRequests}
                onChange={handleChange('maxConcurrentRequests')}
                margin="normal"
              />
            </Box>

            <Divider sx={{ my: 3 }} />

            <Typography variant="h6" gutterBottom>
              Feature Flags
            </Typography>
            <Box>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.debugMode}
                    onChange={handleChange('debugMode')}
                  />
                }
                label="Debug Mode"
              />
              <Typography variant="body2" color="text.secondary" sx={{ ml: 4, mb: 2 }}>
                Enable detailed logging and debugging features
              </Typography>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.analytics}
                    onChange={handleChange('analytics')}
                  />
                }
                label="Analytics"
              />
              <Typography variant="body2" color="text.secondary" sx={{ ml: 4 }}>
                Allow collection of anonymous usage data
              </Typography>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              About
            </Typography>
            <Box sx={{ mb: 3 }}>
              <Typography variant="body1" paragraph>
                AI CI/CD Platform is an intelligent continuous integration and
                delivery platform that leverages artificial intelligence to automate
                and optimize your development workflow.
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Version: {import.meta.env.VITE_APP_VERSION || '0.1.0'}
              </Typography>
            </Box>

            <Divider sx={{ my: 3 }} />

            <Typography variant="h6" gutterBottom>
              Documentation
            </Typography>
            <Typography variant="body2" paragraph>
              For detailed documentation, API references, and guides, visit our
              documentation portal.
            </Typography>
            <Button
              variant="outlined"
              href="https://docs.example.com"
              target="_blank"
              rel="noopener noreferrer"
            >
              View Documentation
            </Button>
          </Paper>
        </Grid>
      </Grid>

      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={handleSave}
          sx={{ minWidth: 200 }}
        >
          Save Settings
        </Button>
      </Box>

      {saved && (
        <Card sx={{ mt: 2, bgcolor: 'success.light' }}>
          <CardContent>
            <Typography color="success.dark">Settings saved successfully!</Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
