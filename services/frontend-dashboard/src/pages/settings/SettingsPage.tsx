import { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Switch,
  Divider,
  TextField,
  Button,
  Alert,
  Snackbar,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
} from '@mui/material';
import { useAuthStore } from '../../stores/auth.store';

interface Settings {
  notifications: boolean;
  autoDebug: boolean;
  theme: 'light' | 'dark' | 'system';
  pipelineTimeout: number;
  securityScanLevel: 'basic' | 'standard' | 'thorough';
}

const DEFAULT_SETTINGS: Settings = {
  notifications: true,
  autoDebug: false,
  theme: 'system',
  pipelineTimeout: 30,
  securityScanLevel: 'standard',
};

export default function SettingsPage() {
  const { user } = useAuthStore();
  const [settings, setSettings] = useState<Settings>(() => {
    const savedSettings = localStorage.getItem('dashboard_settings');
    return savedSettings ? JSON.parse(savedSettings) : DEFAULT_SETTINGS;
  });
  const [showSuccess, setShowSuccess] = useState(false);

  const handleToggle = (setting: keyof Settings) => {
    setSettings((prev) => {
      const newSettings = { ...prev, [setting]: !prev[setting] };
      localStorage.setItem('dashboard_settings', JSON.stringify(newSettings));
      return newSettings;
    });
    setShowSuccess(true);
  };

  const handleNumberChange = (setting: keyof Settings, value: string) => {
    const numValue = parseInt(value, 10);
    if (!isNaN(numValue)) {
      setSettings((prev) => {
        const newSettings = { ...prev, [setting]: numValue };
        localStorage.setItem('dashboard_settings', JSON.stringify(newSettings));
        return newSettings;
      });
      setShowSuccess(true);
    }
  };

  const handleSelectChange = (setting: keyof Settings) => (event: SelectChangeEvent) => {
    setSettings((prev) => {
      const newSettings = { ...prev, [setting]: event.target.value };
      localStorage.setItem('dashboard_settings', JSON.stringify(newSettings));
      return newSettings;
    });
    setShowSuccess(true);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      {/* User Info */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          User Information
        </Typography>
        <List>
          <ListItem>
            <ListItemText primary="Username" secondary={user?.username} />
          </ListItem>
          <ListItem>
            <ListItemText primary="Email" secondary={user?.email} />
          </ListItem>
          <ListItem>
            <ListItemText
              primary="Roles"
              secondary={user?.roles.join(', ')}
            />
          </ListItem>
        </List>
      </Paper>

      {/* Preferences */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Preferences
        </Typography>
        <List>
          <ListItem>
            <ListItemText
              primary="Desktop Notifications"
              secondary="Receive notifications for pipeline events"
            />
            <ListItemSecondaryAction>
              <Switch
                edge="end"
                checked={settings.notifications}
                onChange={() => handleToggle('notifications')}
              />
            </ListItemSecondaryAction>
          </ListItem>
          <Divider />
          <ListItem>
            <ListItemText
              primary="Automatic Debug Mode"
              secondary="Automatically start debug session on pipeline failure"
            />
            <ListItemSecondaryAction>
              <Switch
                edge="end"
                checked={settings.autoDebug}
                onChange={() => handleToggle('autoDebug')}
              />
            </ListItemSecondaryAction>
          </ListItem>
          <Divider />
          <ListItem>
            <ListItemText
              primary="Theme"
              secondary="Choose your preferred theme"
            />
            <ListItemSecondaryAction sx={{ minWidth: 120 }}>
              <FormControl size="small">
                <Select
                  value={settings.theme}
                  onChange={handleSelectChange('theme')}
                >
                  <MenuItem value="light">Light</MenuItem>
                  <MenuItem value="dark">Dark</MenuItem>
                  <MenuItem value="system">System</MenuItem>
                </Select>
              </FormControl>
            </ListItemSecondaryAction>
          </ListItem>
        </List>
      </Paper>

      {/* System Settings */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          System Settings
        </Typography>
        <List>
          <ListItem>
            <ListItemText
              primary="Pipeline Timeout"
              secondary="Maximum pipeline execution time (minutes)"
            />
            <ListItemSecondaryAction>
              <TextField
                type="number"
                size="small"
                value={settings.pipelineTimeout}
                onChange={(e) => handleNumberChange('pipelineTimeout', e.target.value)}
                sx={{ width: 80 }}
              />
            </ListItemSecondaryAction>
          </ListItem>
          <Divider />
          <ListItem>
            <ListItemText
              primary="Security Scan Level"
              secondary="Configure the depth of security scans"
            />
            <ListItemSecondaryAction sx={{ minWidth: 120 }}>
              <FormControl size="small">
                <Select
                  value={settings.securityScanLevel}
                  onChange={handleSelectChange('securityScanLevel')}
                >
                  <MenuItem value="basic">Basic</MenuItem>
                  <MenuItem value="standard">Standard</MenuItem>
                  <MenuItem value="thorough">Thorough</MenuItem>
                </Select>
              </FormControl>
            </ListItemSecondaryAction>
          </ListItem>
        </List>
      </Paper>

      <Snackbar
        open={showSuccess}
        autoHideDuration={3000}
        onClose={() => setShowSuccess(false)}
      >
        <Alert severity="success" sx={{ width: '100%' }}>
          Settings saved successfully
        </Alert>
      </Snackbar>
    </Box>
  );
}
