import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Button, 
  Card, 
  CardContent, 
  Typography, 
  Chip, 
  Grid, 
  IconButton, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Paper,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress
} from '@mui/material';
import { 
  Refresh as RefreshIcon, 
  Notifications as NotificationIcon,
  NotificationsActive as AlertIcon,
  Speed as SpeedIcon,
  Timeline as TimelineIcon,
  CheckCircle as HealthyIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { useWebSocketEvent } from '../../hooks/useWebSocket';
// Note: In a real implementation, you would need to install the recharts library:
// npm install recharts @types/recharts
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts';

// Types
interface HealthCheck {
  id: string;
  deploymentId: string;
  environmentId: string;
  status: string;
  timestamp: string;
  checks: {
    name: string;
    status: string;
    message: string;
    details: any;
  }[];
}

interface Metric {
  id: string;
  deploymentId: string;
  environmentId: string;
  name: string;
  type: string;
  unit: string;
  description: string;
  values: {
    timestamp: string;
    value: number;
  }[];
  baseline?: {
    min: number;
    max: number;
    avg: number;
    p95: number;
    p99: number;
  };
  tags: any;
}

interface Alert {
  id: string;
  deploymentId: string;
  environmentId: string;
  severity: string;
  message: string;
  timestamp: string;
  status: string;
  metric?: {
    id: string;
    name: string;
    value: number;
    threshold: number;
  };
  details: any;
}

interface Deployment {
  id: string;
  name: string;
  environmentId: string;
}

interface Environment {
  id: string;
  name: string;
  type: string;
}

// Mock data for development
const mockHealthChecks: HealthCheck[] = [
  {
    id: '1',
    deploymentId: '1',
    environmentId: '3', // production
    status: 'healthy',
    timestamp: '2025-03-01T15:00:00Z',
    checks: [
      {
        name: 'API Endpoint',
        status: 'healthy',
        message: 'API endpoint is responding',
        details: {
          endpoint: '/api/v1/health',
          response_time: '50ms'
        }
      },
      {
        name: 'Database Connection',
        status: 'healthy',
        message: 'Database connection is established',
        details: {
          database: 'postgres',
          response_time: '20ms'
        }
      }
    ]
  },
  {
    id: '2',
    deploymentId: '2',
    environmentId: '3', // production
    status: 'degraded',
    timestamp: '2025-03-01T15:05:00Z',
    checks: [
      {
        name: 'API Endpoint',
        status: 'healthy',
        message: 'API endpoint is responding',
        details: {
          endpoint: '/api/v1/health',
          response_time: '120ms'
        }
      },
      {
        name: 'Database Connection',
        status: 'degraded',
        message: 'Database connection is slow',
        details: {
          database: 'postgres',
          response_time: '500ms'
        }
      }
    ]
  }
];

const mockMetrics: Metric[] = [
  {
    id: '1',
    deploymentId: '1',
    environmentId: '3', // production
    name: 'Response Time',
    type: 'gauge',
    unit: 'ms',
    description: 'API response time',
    values: [
      { timestamp: '2025-03-01T14:00:00Z', value: 50 },
      { timestamp: '2025-03-01T14:05:00Z', value: 55 },
      { timestamp: '2025-03-01T14:10:00Z', value: 48 },
      { timestamp: '2025-03-01T14:15:00Z', value: 52 },
      { timestamp: '2025-03-01T14:20:00Z', value: 60 },
      { timestamp: '2025-03-01T14:25:00Z', value: 58 },
      { timestamp: '2025-03-01T14:30:00Z', value: 53 }
    ],
    baseline: {
      min: 10,
      max: 100,
      avg: 50,
      p95: 80,
      p99: 90
    },
    tags: {
      service: 'api',
      endpoint: '/api/v1/users'
    }
  },
  {
    id: '2',
    deploymentId: '1',
    environmentId: '3', // production
    name: 'CPU Usage',
    type: 'gauge',
    unit: '%',
    description: 'CPU usage percentage',
    values: [
      { timestamp: '2025-03-01T14:00:00Z', value: 30 },
      { timestamp: '2025-03-01T14:05:00Z', value: 35 },
      { timestamp: '2025-03-01T14:10:00Z', value: 40 },
      { timestamp: '2025-03-01T14:15:00Z', value: 38 },
      { timestamp: '2025-03-01T14:20:00Z', value: 42 },
      { timestamp: '2025-03-01T14:25:00Z', value: 45 },
      { timestamp: '2025-03-01T14:30:00Z', value: 39 }
    ],
    baseline: {
      min: 0,
      max: 80,
      avg: 40,
      p95: 70,
      p99: 75
    },
    tags: {
      service: 'api',
      resource: 'cpu'
    }
  },
  {
    id: '3',
    deploymentId: '2',
    environmentId: '3', // production
    name: 'Response Time',
    type: 'gauge',
    unit: 'ms',
    description: 'API response time',
    values: [
      { timestamp: '2025-03-01T14:00:00Z', value: 100 },
      { timestamp: '2025-03-01T14:05:00Z', value: 110 },
      { timestamp: '2025-03-01T14:10:00Z', value: 120 },
      { timestamp: '2025-03-01T14:15:00Z', value: 115 },
      { timestamp: '2025-03-01T14:20:00Z', value: 130 },
      { timestamp: '2025-03-01T14:25:00Z', value: 140 },
      { timestamp: '2025-03-01T14:30:00Z', value: 125 }
    ],
    baseline: {
      min: 50,
      max: 150,
      avg: 100,
      p95: 140,
      p99: 145
    },
    tags: {
      service: 'api',
      endpoint: '/api/v1/products'
    }
  }
];

const mockAlerts: Alert[] = [
  {
    id: '1',
    deploymentId: '1',
    environmentId: '3', // production
    severity: 'high',
    message: 'High CPU usage',
    timestamp: '2025-03-01T14:25:00Z',
    status: 'active',
    metric: {
      id: '2',
      name: 'CPU Usage',
      value: 85,
      threshold: 80
    },
    details: {
      service: 'api',
      duration: '5m'
    }
  },
  {
    id: '2',
    deploymentId: '2',
    environmentId: '3', // production
    severity: 'medium',
    message: 'Elevated response time',
    timestamp: '2025-03-01T14:20:00Z',
    status: 'active',
    metric: {
      id: '3',
      name: 'Response Time',
      value: 130,
      threshold: 120
    },
    details: {
      service: 'api',
      endpoint: '/api/v1/products',
      duration: '10m'
    }
  }
];

const mockDeployments: Deployment[] = [
  {
    id: '1',
    name: 'API Service',
    environmentId: '3' // production
  },
  {
    id: '2',
    name: 'Web Frontend',
    environmentId: '3' // production
  },
  {
    id: '3',
    name: 'Database Service',
    environmentId: '3' // production
  }
];

const mockEnvironments: Environment[] = [
  {
    id: '1',
    name: 'Development',
    type: 'development'
  },
  {
    id: '2',
    name: 'Staging',
    type: 'staging'
  },
  {
    id: '3',
    name: 'Production',
    type: 'production'
  }
];

// Component
const DeploymentMonitor: React.FC = () => {
  const theme = useTheme();
  const { data: lastMessage } = useWebSocketEvent('monitoring_update');
  
  const [healthChecks, setHealthChecks] = useState<HealthCheck[]>(mockHealthChecks);
  const [metrics, setMetrics] = useState<Metric[]>(mockMetrics);
  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts);
  const [deployments, setDeployments] = useState<Deployment[]>(mockDeployments);
  const [environments, setEnvironments] = useState<Environment[]>(mockEnvironments);
  const [selectedDeployment, setSelectedDeployment] = useState<string>('');
  const [selectedEnvironment, setSelectedEnvironment] = useState<string>('3'); // Default to production
  const [selectedMetric, setSelectedMetric] = useState<Metric | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  
  // Dialog states
  const [metricDetailsDialogOpen, setMetricDetailsDialogOpen] = useState<boolean>(false);
  const [healthCheckDetailsDialogOpen, setHealthCheckDetailsDialogOpen] = useState<boolean>(false);
  const [alertDetailsDialogOpen, setAlertDetailsDialogOpen] = useState<boolean>(false);
  
  // Selected items for dialogs
  const [selectedHealthCheck, setSelectedHealthCheck] = useState<HealthCheck | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  
  // Effect to handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      try {
        if (typeof lastMessage === 'object') {
          // Handle health check updates
          if (lastMessage.type === 'health_check_update' && lastMessage.healthCheck) {
            setHealthChecks(prevHealthChecks => {
              const index = prevHealthChecks.findIndex(h => h.id === lastMessage.healthCheck.id);
              if (index >= 0) {
                const updatedHealthChecks = [...prevHealthChecks];
                updatedHealthChecks[index] = lastMessage.healthCheck;
                return updatedHealthChecks;
              }
              return [...prevHealthChecks, lastMessage.healthCheck];
            });
          } 
          // Handle metric updates
          else if (lastMessage.type === 'metric_update' && lastMessage.metric) {
            setMetrics(prevMetrics => {
              const index = prevMetrics.findIndex(m => m.id === lastMessage.metric.id);
              if (index >= 0) {
                const updatedMetrics = [...prevMetrics];
                updatedMetrics[index] = lastMessage.metric;
                return updatedMetrics;
              }
              return [...prevMetrics, lastMessage.metric];
            });
          }
          // Handle alert updates
          else if (lastMessage.type === 'alert_update' && lastMessage.alert) {
            setAlerts(prevAlerts => {
              const index = prevAlerts.findIndex(a => a.id === lastMessage.alert.id);
              if (index >= 0) {
                const updatedAlerts = [...prevAlerts];
                updatedAlerts[index] = lastMessage.alert;
                return updatedAlerts;
              }
              return [...prevAlerts, lastMessage.alert];
            });
          }
        }
      } catch (error) {
        console.error('Error handling WebSocket message:', error);
      }
    }
  }, [lastMessage]);
  
  // Fetch health checks
  const fetchHealthChecks = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would fetch from the API
      // const response = await fetch(`/api/deployment-automation/health-checks?environmentId=${selectedEnvironment}&deploymentId=${selectedDeployment}`);
      // const data = await response.json();
      // setHealthChecks(data);
      
      // For now, filter mock data
      const filteredHealthChecks = mockHealthChecks.filter(h => 
        (selectedEnvironment ? h.environmentId === selectedEnvironment : true) &&
        (selectedDeployment ? h.deploymentId === selectedDeployment : true)
      );
      setHealthChecks(filteredHealthChecks);
    } catch (error) {
      console.error('Error fetching health checks:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Fetch metrics
  const fetchMetrics = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would fetch from the API
      // const response = await fetch(`/api/deployment-automation/metrics?environmentId=${selectedEnvironment}&deploymentId=${selectedDeployment}`);
      // const data = await response.json();
      // setMetrics(data);
      
      // For now, filter mock data
      const filteredMetrics = mockMetrics.filter(m => 
        (selectedEnvironment ? m.environmentId === selectedEnvironment : true) &&
        (selectedDeployment ? m.deploymentId === selectedDeployment : true)
      );
      setMetrics(filteredMetrics);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Fetch alerts
  const fetchAlerts = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would fetch from the API
      // const response = await fetch(`/api/deployment-automation/alerts?environmentId=${selectedEnvironment}&deploymentId=${selectedDeployment}`);
      // const data = await response.json();
      // setAlerts(data);
      
      // For now, filter mock data
      const filteredAlerts = mockAlerts.filter(a => 
        (selectedEnvironment ? a.environmentId === selectedEnvironment : true) &&
        (selectedDeployment ? a.deploymentId === selectedDeployment : true)
      );
      setAlerts(filteredAlerts);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Effect to fetch data when filters change
  useEffect(() => {
    fetchHealthChecks();
    fetchMetrics();
    fetchAlerts();
  }, [selectedEnvironment, selectedDeployment]);
  
  // Get deployment name by ID
  const getDeploymentName = (deploymentId: string): string => {
    const deployment = deployments.find(d => d.id === deploymentId);
    return deployment ? deployment.name : `Deployment ${deploymentId}`;
  };
  
  // Get environment name by ID
  const getEnvironmentName = (environmentId: string): string => {
    const environment = environments.find(e => e.id === environmentId);
    return environment ? environment.name : `Environment ${environmentId}`;
  };
  
  // Get status color
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'completed':
      case 'resolved':
        return 'success';
      case 'degraded':
      case 'warning':
        return 'warning';
      case 'unhealthy':
      case 'failed':
      case 'critical':
        return 'error';
      case 'unknown':
        return 'default';
      case 'active':
        return 'info';
      default:
        return 'default';
    }
  };
  
  // Get severity color
  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'low':
        return 'info';
      case 'medium':
        return 'warning';
      case 'high':
        return 'error';
      case 'critical':
        return 'error';
      default:
        return 'default';
    }
  };
  
  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'completed':
      case 'resolved':
        return <HealthyIcon color="success" />;
      case 'degraded':
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'unhealthy':
      case 'failed':
      case 'critical':
        return <ErrorIcon color="error" />;
      case 'unknown':
        return <InfoIcon color="disabled" />;
      case 'active':
        return <AlertIcon color="info" />;
      default:
        return <InfoIcon color="disabled" />;
    }
  };
  
  // Format date
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString();
  };
  
  // Format metric value
  const formatMetricValue = (value: number, unit: string): string => {
    return `${value}${unit}`;
  };
  
  // Render health check card
  const renderHealthCheckCard = (healthCheck: HealthCheck) => {
    return (
      <Card key={healthCheck.id} sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="h6">{getDeploymentName(healthCheck.deploymentId)}</Typography>
            <Chip 
              label={healthCheck.status} 
              size="small" 
              color={getStatusColor(healthCheck.status)}
              icon={getStatusIcon(healthCheck.status)}
            />
          </Box>
          
          <Typography variant="body2" color="text.secondary" mb={2}>
            Environment: {getEnvironmentName(healthCheck.environmentId)} • Last Check: {formatDate(healthCheck.timestamp)}
          </Typography>
          
          <Box>
            {healthCheck.checks.map((check, index) => (
              <Box key={index} display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Typography variant="body2">{check.name}</Typography>
                <Chip 
                  label={check.status} 
                  size="small" 
                  color={getStatusColor(check.status)}
                />
              </Box>
            ))}
          </Box>
          
          <Box display="flex" justifyContent="flex-end" mt={2}>
            <Button 
              variant="outlined" 
              size="small"
              onClick={() => {
                setSelectedHealthCheck(healthCheck);
                setHealthCheckDetailsDialogOpen(true);
              }}
            >
              View Details
            </Button>
          </Box>
        </CardContent>
      </Card>
    );
  };
  
  // Render metric card
  const renderMetricCard = (metric: Metric) => {
    // Get latest value
    const latestValue = metric.values.length > 0 ? metric.values[metric.values.length - 1].value : 0;
    
    // Check if value exceeds baseline
    const isExceedingBaseline = metric.baseline && latestValue > metric.baseline.max;
    
    // Prepare chart data
    const chartData = metric.values.map(v => ({
      time: new Date(v.timestamp).toLocaleTimeString(),
      value: v.value
    }));
    
    return (
      <Card key={metric.id} sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="h6">{metric.name}</Typography>
            <Chip 
              label={formatMetricValue(latestValue, metric.unit)} 
              size="small" 
              color={isExceedingBaseline ? 'error' : 'default'}
            />
          </Box>
          
          <Typography variant="body2" color="text.secondary" mb={2}>
            Deployment: {getDeploymentName(metric.deploymentId)} • Environment: {getEnvironmentName(metric.environmentId)}
          </Typography>
          
          <Box height={100} mb={2}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <RechartsTooltip />
                <Line type="monotone" dataKey="value" stroke={theme.palette.primary.main} />
                {metric.baseline && (
                  <Line 
                    type="monotone" 
                    dataKey={() => metric.baseline?.max} 
                    stroke={theme.palette.error.main} 
                    strokeDasharray="5 5" 
                    dot={false}
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </Box>
          
          <Box display="flex" justifyContent="flex-end">
            <Button 
              variant="outlined" 
              size="small"
              onClick={() => {
                setSelectedMetric(metric);
                setMetricDetailsDialogOpen(true);
              }}
            >
              View Details
            </Button>
          </Box>
        </CardContent>
      </Card>
    );
  };
  
  // Render alert card
  const renderAlertCard = (alert: Alert) => {
    return (
      <Card key={alert.id} sx={{ 
        mb: 2, 
        borderLeft: `4px solid ${
          getSeverityColor(alert.severity) === 'default' 
            ? theme.palette.grey[500] 
            : theme.palette[getSeverityColor(alert.severity) as 'info' | 'warning' | 'error'].main
        }` 
      }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="h6">{alert.message}</Typography>
            <Chip 
              label={alert.severity} 
              size="small" 
              color={getSeverityColor(alert.severity)}
            />
          </Box>
          
          <Typography variant="body2" color="text.secondary" mb={2}>
            Deployment: {getDeploymentName(alert.deploymentId)} • Environment: {getEnvironmentName(alert.environmentId)}
          </Typography>
          
          <Typography variant="body2" color="text.secondary" mb={2}>
            Triggered: {formatDate(alert.timestamp)} • Status: {alert.status}
          </Typography>
          
          {alert.metric && (
            <Box mb={2}>
              <Typography variant="body2" gutterBottom>
                {alert.metric.name}: {alert.metric.value} (Threshold: {alert.metric.threshold})
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={(alert.metric.value / alert.metric.threshold) * 100} 
                color={alert.metric.value > alert.metric.threshold ? "error" : "primary"}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>
          )}
          
          <Box display="flex" justifyContent="flex-end">
            <Button 
              variant="outlined" 
              size="small"
              onClick={() => {
                setSelectedAlert(alert);
                setAlertDetailsDialogOpen(true);
              }}
            >
              View Details
            </Button>
          </Box>
        </CardContent>
      </Card>
    );
  };
  
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Deployment Monitoring</Typography>
        <Box display="flex" alignItems="center">
          <FormControl sx={{ minWidth: 150, mr: 2 }}>
            <InputLabel>Environment</InputLabel>
            <Select
              value={selectedEnvironment}
              label="Environment"
              onChange={(e) => setSelectedEnvironment(e.target.value)}
              size="small"
            >
              <MenuItem value="">All Environments</MenuItem>
              {environments.map(env => (
                <MenuItem key={env.id} value={env.id}>{env.name}</MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <FormControl sx={{ minWidth: 150, mr: 2 }}>
            <InputLabel>Deployment</InputLabel>
            <Select
              value={selectedDeployment}
              label="Deployment"
              onChange={(e) => setSelectedDeployment(e.target.value)}
              size="small"
            >
              <MenuItem value="">All Deployments</MenuItem>
              {deployments.map(dep => (
                <MenuItem key={dep.id} value={dep.id}>{dep.name}</MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <Button 
            variant="outlined" 
            startIcon={<RefreshIcon />}
            onClick={() => {
              fetchHealthChecks();
              fetchMetrics();
              fetchAlerts();
            }}
          >
            Refresh
          </Button>
        </Box>
      </Box>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Health Checks</Typography>
            <Chip 
              label={`${healthChecks.filter(h => h.status === 'healthy').length}/${healthChecks.length} Healthy`}
              size="small"
              color="success"
            />
          </Box>
          
          {loading ? (
            <Box display="flex" justifyContent="center" my={4}>
              <CircularProgress />
            </Box>
          ) : healthChecks.length > 0 ? (
            healthChecks.map(renderHealthCheckCard)
          ) : (
            <Typography variant="body1" color="text.secondary" align="center" my={4}>
              No health checks found.
            </Typography>
          )}
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Typography variant="h6" mb={2}>Metrics</Typography>
          {loading ? (
            <Box display="flex" justifyContent="center" my={4}>
              <CircularProgress />
            </Box>
          ) : metrics.length > 0 ? (
            metrics.map(renderMetricCard)
          ) : (
            <Typography variant="body1" color="text.secondary" align="center" my={4}>
              No metrics found.
            </Typography>
          )}
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Alerts</Typography>
            {alerts.length > 0 && (
              <Chip 
                label={`${alerts.length} Active`}
                size="small"
                color="error"
                icon={<AlertIcon />}
              />
            )}
          </Box>
          
          {loading ? (
            <Box display="flex" justifyContent="center" my={4}>
              <CircularProgress />
            </Box>
          ) : alerts.length > 0 ? (
            alerts.map(renderAlertCard)
          ) : (
            <Typography variant="body1" color="text.secondary" align="center" my={4}>
              No alerts found.
            </Typography>
          )}
        </Grid>
      </Grid>
      
      {/* Health Check Details Dialog */}
      <Dialog open={healthCheckDetailsDialogOpen} onClose={() => setHealthCheckDetailsDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Health Check Details</DialogTitle>
        <DialogContent>
          {selectedHealthCheck && (
            <Box mt={2}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">{getDeploymentName(selectedHealthCheck.deploymentId)}</Typography>
                <Chip 
                  label={selectedHealthCheck.status} 
                  color={getStatusColor(selectedHealthCheck.status)}
                />
              </Box>
              
              <Typography variant="body2" color="text.secondary" mb={3}>
                Environment: {getEnvironmentName(selectedHealthCheck.environmentId)} • Last Check: {formatDate(selectedHealthCheck.timestamp)}
              </Typography>
              
              <Typography variant="subtitle1" gutterBottom>
                Check Results
              </Typography>
              
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Check</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Message</TableCell>
                      <TableCell>Details</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {selectedHealthCheck.checks.map((check, index) => (
                      <TableRow key={index}>
                        <TableCell>{check.name}</TableCell>
                        <TableCell>
                          <Chip 
                            label={check.status} 
                            size="small" 
                            color={getStatusColor(check.status)}
                          />
                        </TableCell>
                        <TableCell>{check.message}</TableCell>
                        <TableCell>
                          <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                            {JSON.stringify(check.details, null, 2)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHealthCheckDetailsDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
      
      {/* Metric Details Dialog */}
      <Dialog open={metricDetailsDialogOpen} onClose={() => setMetricDetailsDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Metric Details</DialogTitle>
        <DialogContent>
          {selectedMetric && (
            <Box mt={2}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">{selectedMetric.name}</Typography>
                <Chip 
                  label={selectedMetric.type} 
                  size="small" 
                  color="primary"
                />
              </Box>
              
              <Typography variant="body2" color="text.secondary" mb={1}>
                {selectedMetric.description}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" mb={3}>
                Deployment: {getDeploymentName(selectedMetric.deploymentId)} • Environment: {getEnvironmentName(selectedMetric.environmentId)}
              </Typography>
              
              <Box height={300} mb={3}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={selectedMetric.values.map(v => ({
                    time: new Date(v.timestamp).toLocaleTimeString(),
                    value: v.value
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="value" 
                      name={`${selectedMetric.name} (${selectedMetric.unit})`} 
                      stroke={theme.palette.primary.main} 
                      activeDot={{ r: 8 }} 
                    />
                    {selectedMetric.baseline && (
                      <>
                        <Line 
                          type="monotone" 
                          dataKey={() => selectedMetric.baseline?.max} 
                          name="Max Threshold" 
                          stroke={theme.palette.error.main} 
                          strokeDasharray="5 5" 
                          dot={false}
                        />
                        <Line 
                          type="monotone" 
                          dataKey={() => selectedMetric.baseline?.min} 
                          name="Min Threshold" 
                          stroke={theme.palette.success.main} 
                          strokeDasharray="5 5" 
                          dot={false}
                        />
                      </>
                    )}
                  </LineChart>
                </ResponsiveContainer>
              </Box>
              
              {selectedMetric.baseline && (
                <Box mb={3}>
                  <Typography variant="subtitle1" gutterBottom>
                    Baseline Information
                  </Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell>Minimum</TableCell>
                          <TableCell>{formatMetricValue(selectedMetric.baseline.min, selectedMetric.unit)}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Maximum</TableCell>
                          <TableCell>{formatMetricValue(selectedMetric.baseline.max, selectedMetric.unit)}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Average</TableCell>
                          <TableCell>{formatMetricValue(selectedMetric.baseline.avg, selectedMetric.unit)}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>95th Percentile</TableCell>
                          <TableCell>{formatMetricValue(selectedMetric.baseline.p95, selectedMetric.unit)}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>99th Percentile</TableCell>
                          <TableCell>{formatMetricValue(selectedMetric.baseline.p99, selectedMetric.unit)}</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}
              
              <Typography variant="subtitle1" gutterBottom>
                Tags
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={1}>
                {Object.entries(selectedMetric.tags).map(([key, value]) => (
                  <Chip 
                    key={key} 
                    label={`${key}: ${value}`} 
                    size="small" 
                    color="default"
                  />
                ))}
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMetricDetailsDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
      
      {/* Alert Details Dialog */}
      <Dialog open={alertDetailsDialogOpen} onClose={() => setAlertDetailsDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Alert Details</DialogTitle>
        <DialogContent>
          {selectedAlert && (
            <Box mt={2}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">{selectedAlert.message}</Typography>
                <Chip 
                  label={selectedAlert.severity} 
                  color={getSeverityColor(selectedAlert.severity)}
                />
              </Box>
              
              <Typography variant="body2" color="text.secondary" mb={3}>
                Deployment: {getDeploymentName(selectedAlert.deploymentId)} • Environment: {getEnvironmentName(selectedAlert.environmentId)}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" mb={3}>
                Triggered: {formatDate(selectedAlert.timestamp)} • Status: {selectedAlert.status}
              </Typography>
              
              {selectedAlert.metric && (
                <Box mb={3}>
                  <Typography variant="subtitle1" gutterBottom>
                    Metric Information
                  </Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell>Metric</TableCell>
                          <TableCell>{selectedAlert.metric.name}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Current Value</TableCell>
                          <TableCell>{selectedAlert.metric.value}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Threshold</TableCell>
                          <TableCell>{selectedAlert.metric.threshold}</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}
              
              <Typography variant="subtitle1" gutterBottom>
                Additional Details
              </Typography>
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'background.default' }}>
                <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify(selectedAlert.details, null, 2)}
                </Typography>
              </Paper>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAlertDetailsDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DeploymentMonitor;
