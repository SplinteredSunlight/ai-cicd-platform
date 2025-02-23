import { useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
} from '@mui/material';
import {
  Error as CriticalIcon,
  Warning as HighIcon,
  Info as MediumIcon,
  CheckCircle as LowIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { useSecurityStore } from '../../stores/security.store';

const SEVERITY_CONFIG = {
  critical: {
    icon: CriticalIcon,
    color: 'error',
    label: 'Critical',
  },
  high: {
    icon: HighIcon,
    color: 'warning',
    label: 'High',
  },
  medium: {
    icon: MediumIcon,
    color: 'info',
    label: 'Medium',
  },
  low: {
    icon: LowIcon,
    color: 'success',
    label: 'Low',
  },
} as const;

export default function SecurityPage() {
  const {
    vulnerabilities,
    scans,
    isLoading,
    error,
    fetchVulnerabilities,
    fetchScans,
    startScan,
  } = useSecurityStore();

  useEffect(() => {
    fetchVulnerabilities();
    fetchScans();
  }, [fetchVulnerabilities, fetchScans]);

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  // Group vulnerabilities by severity
  const groupedVulnerabilities = vulnerabilities.reduce(
    (acc, vuln) => {
      if (!acc[vuln.severity]) {
        acc[vuln.severity] = [];
      }
      acc[vuln.severity].push(vuln);
      return acc;
    },
    {} as Record<string, typeof vulnerabilities>
  );

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Security</Typography>
        <Button
          variant="contained"
          onClick={() => {
            // TODO: Implement scan target selection
            startScan('default');
          }}
        >
          Start New Scan
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {Object.entries(SEVERITY_CONFIG).map(([severity, config]) => {
          const count = groupedVulnerabilities[severity]?.length || 0;
          const Icon = config.icon;
          return (
            <Grid item xs={12} sm={6} md={3} key={severity}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Icon color={config.color} sx={{ mr: 1 }} />
                    <Typography variant="h6">{config.label}</Typography>
                  </Box>
                  <Typography variant="h3">{count}</Typography>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Vulnerabilities List */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Recent Vulnerabilities
        </Typography>
        <List>
          {vulnerabilities.slice(0, 10).map((vuln) => {
            const config = SEVERITY_CONFIG[vuln.severity];
            const Icon = config.icon;
            return (
              <ListItem
                key={vuln.id}
                sx={{
                  borderBottom: '1px solid',
                  borderColor: 'divider',
                  '&:last-child': { borderBottom: 'none' },
                }}
              >
                <ListItemIcon>
                  <Icon color={config.color} />
                </ListItemIcon>
                <ListItemText
                  primary={vuln.title}
                  secondary={
                    <>
                      {vuln.description}
                      <Box component="span" sx={{ display: 'block', mt: 1 }}>
                        <Chip
                          size="small"
                          label={vuln.affected_component}
                          sx={{ mr: 1 }}
                        />
                        {vuln.fix_available && (
                          <Chip
                            size="small"
                            color="success"
                            label="Fix Available"
                          />
                        )}
                      </Box>
                    </>
                  }
                />
              </ListItem>
            );
          })}
        </List>
      </Paper>

      {/* Recent Scans */}
      <Paper sx={{ p: 2, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Recent Scans
        </Typography>
        <List>
          {scans.slice(0, 5).map((scan) => (
            <ListItem
              key={scan.id}
              sx={{
                borderBottom: '1px solid',
                borderColor: 'divider',
                '&:last-child': { borderBottom: 'none' },
              }}
            >
              <ListItemText
                primary={`Scan #${scan.id}`}
                secondary={`Started: ${format(
                  new Date(scan.created_at),
                  'MMM d, yyyy HH:mm'
                )}`}
              />
              <Chip
                label={scan.status}
                color={
                  scan.status === 'completed'
                    ? 'success'
                    : scan.status === 'failed'
                    ? 'error'
                    : 'default'
                }
              />
            </ListItem>
          ))}
        </List>
      </Paper>
    </Box>
  );
}
