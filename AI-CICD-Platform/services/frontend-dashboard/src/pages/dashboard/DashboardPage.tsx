import { useEffect } from 'react';
import { Box, Grid, Typography } from '@mui/material';
import { useMetricsStore } from '../../stores/metrics.store';
import { usePipelineStore } from '../../stores/pipeline.store';
import { useSecurityStore } from '../../stores/security.store';
import { Pipeline, Vulnerability } from '../../config/api';
import StatusCard from './components/StatusCard';
import PipelineChart from './components/PipelineChart';
import SecuritySummary from './components/SecuritySummary';
import ServiceHealth from './components/ServiceHealth';

export default function DashboardPage() {
  const { summary, isLoading: metricsLoading, error: metricsError, fetchSummary } = useMetricsStore();
  const { pipelines, fetchPipelines } = usePipelineStore() as { pipelines: Pipeline[]; fetchPipelines: () => Promise<void> };
  const { vulnerabilities, fetchVulnerabilities } = useSecurityStore() as { vulnerabilities: Vulnerability[]; fetchVulnerabilities: () => Promise<void> };

  useEffect(() => {
    fetchSummary();
    fetchPipelines();
    fetchVulnerabilities();
    const interval = setInterval(() => {
      fetchSummary();
      fetchPipelines();
      fetchVulnerabilities();
    }, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [fetchSummary, fetchPipelines, fetchVulnerabilities]);

  if (metricsError) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography color="error">{metricsError}</Typography>
      </Box>
    );
  }

  if (!summary && metricsLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography>Loading dashboard data...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Summary Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <StatusCard
            title="Total Pipelines"
            value={summary?.total_pipelines || 0}
            change={10}
            subtitle="Last 30 days"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatusCard
            title="Active Pipelines"
            value={summary?.active_pipelines || 0}
            change={5}
            subtitle="Currently running"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatusCard
            title="Success Rate"
            value={summary?.success_rate || 0}
            change={-2}
            unit="%"
            subtitle="Last 7 days"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatusCard
            title="Avg Duration"
            value={Math.round((summary?.avg_duration || 0) / 60)}
            change={-15}
            unit="min"
            subtitle="Last 24 hours"
          />
        </Grid>

        {/* Pipeline Activity Chart */}
        <Grid item xs={12} md={8}>
          <PipelineChart pipelines={pipelines} />
        </Grid>

        {/* Security Summary */}
        <Grid item xs={12} md={4}>
          <SecuritySummary vulnerabilities={vulnerabilities} />
        </Grid>

        {/* Service Health */}
        <Grid item xs={12}>
          <ServiceHealth services={summary?.service_health || {}} />
        </Grid>
      </Grid>
    </Box>
  );
}
