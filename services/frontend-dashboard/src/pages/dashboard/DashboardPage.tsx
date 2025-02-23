import { useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Timeline as TimelineIcon,
  Security as SecurityIcon,
  BugReport as BugIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';

import { usePipelineStore } from '../../stores/pipeline.store';
import { useSecurityStore } from '../../stores/security.store';
import { useDebugStore } from '../../stores/debug.store';
import { useMetricsStore } from '../../stores/metrics.store';

import StatusCard from './components/StatusCard';
import PipelineChart from './components/PipelineChart';
import SecuritySummary from './components/SecuritySummary';
import ServiceHealth from './components/ServiceHealth';

export default function DashboardPage() {
  // Store hooks
  const { fetchPipelines, pipelines, isLoading: pipelinesLoading, error: pipelinesError } = usePipelineStore();
  const { fetchVulnerabilities, vulnerabilities, isLoading: securityLoading, error: securityError } = useSecurityStore();
  const { fetchSessions, sessions, isLoading: debugLoading, error: debugError } = useDebugStore();
  const { fetchMetricsSummary, summary, isLoading: metricsLoading, error: metricsError } = useMetricsStore();

  // Load data on mount
  useEffect(() => {
    fetchPipelines();
    fetchVulnerabilities();
    fetchSessions();
    fetchMetricsSummary();
  }, [fetchPipelines, fetchVulnerabilities, fetchSessions, fetchMetricsSummary]);

  // Calculate stats
  const stats = {
    activePipelines: pipelines?.filter(p => p.status === 'running').length || 0,
    criticalVulnerabilities: vulnerabilities?.filter(v => v.severity === 'critical').length || 0,
    activeDebugSessions: sessions?.filter(s => s.status === 'active').length || 0,
    serviceHealth: summary?.service_health || {},
  };

  // Loading state
  const isLoading = pipelinesLoading || securityLoading || debugLoading || metricsLoading;

  // Error state
  const error = pipelinesError || securityError || debugError || metricsError;

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

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {/* Status Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatusCard
            title="Active Pipelines"
            value={stats.activePipelines}
            icon={<TimelineIcon />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatusCard
            title="Critical Vulnerabilities"
            value={stats.criticalVulnerabilities}
            icon={<SecurityIcon />}
            color="error"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatusCard
            title="Debug Sessions"
            value={stats.activeDebugSessions}
            icon={<BugIcon />}
            color="warning"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatusCard
            title="Service Health"
            value={Object.values(stats.serviceHealth).filter(s => s.status === 'healthy').length}
            icon={<SpeedIcon />}
            color="success"
          />
        </Grid>
      </Grid>

      {/* Charts and Summaries */}
      <Grid container spacing={3}>
        {/* Pipeline Activity */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Pipeline Activity
            </Typography>
            <PipelineChart pipelines={pipelines} />
          </Paper>
        </Grid>

        {/* Security Summary */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Security Overview
            </Typography>
            <SecuritySummary vulnerabilities={vulnerabilities} />
          </Paper>
        </Grid>

        {/* Service Health */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Service Health
            </Typography>
            <ServiceHealth services={stats.serviceHealth} />
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
