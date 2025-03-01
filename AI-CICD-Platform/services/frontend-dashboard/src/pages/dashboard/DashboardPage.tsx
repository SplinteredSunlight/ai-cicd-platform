import React from 'react';
import { Box, Typography } from '@mui/material';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import { useDashboardStore } from '../../stores/dashboard.store';

const DashboardPage: React.FC = () => {
  // Initialize dashboard store
  const { dashboards } = useDashboardStore();

  return (
    <Box sx={{ p: 3, height: 'calc(100vh - 64px)' }}>
      <DashboardLayout />
    </Box>
  );
};

export default DashboardPage;
