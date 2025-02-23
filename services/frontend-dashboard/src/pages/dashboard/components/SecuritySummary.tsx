import { useMemo } from 'react';
import { Box, Typography, LinearProgress } from '@mui/material';
import { ResponsivePie } from '@nivo/pie';
import { Vulnerability } from '../../../config/api';

interface SecuritySummaryProps {
  vulnerabilities: Vulnerability[];
}

interface SeverityCount {
  id: string;
  label: string;
  value: number;
  color: string;
}

export default function SecuritySummary({ vulnerabilities }: SecuritySummaryProps) {
  const stats = useMemo(() => {
    const counts = vulnerabilities.reduce(
      (acc, vuln) => {
        acc[vuln.severity] = (acc[vuln.severity] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>
    );

    const total = vulnerabilities.length;

    return {
      critical: counts.critical || 0,
      high: counts.high || 0,
      medium: counts.medium || 0,
      low: counts.low || 0,
      total,
    };
  }, [vulnerabilities]);

  const pieData: SeverityCount[] = [
    {
      id: 'Critical',
      label: 'Critical',
      value: stats.critical,
      color: '#d32f2f', // error.main
    },
    {
      id: 'High',
      label: 'High',
      value: stats.high,
      color: '#f57c00', // warning.dark
    },
    {
      id: 'Medium',
      label: 'Medium',
      value: stats.medium,
      color: '#ffa726', // warning.light
    },
    {
      id: 'Low',
      label: 'Low',
      value: stats.low,
      color: '#66bb6a', // success.light
    },
  ];

  const getPercentage = (value: number) => 
    stats.total ? Math.round((value / stats.total) * 100) : 0;

  return (
    <Box>
      {/* Pie Chart */}
      <Box sx={{ height: 200 }}>
        <ResponsivePie
          data={pieData}
          margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
          innerRadius={0.6}
          padAngle={0.7}
          cornerRadius={3}
          colors={{ datum: 'color' }}
          borderWidth={1}
          borderColor={{ from: 'color', modifiers: [['darker', 0.2]] }}
          enableArcLinkLabels={false}
          arcLabelsSkipAngle={10}
          arcLabelsTextColor="#ffffff"
        />
      </Box>

      {/* Stats Bars */}
      <Box sx={{ mt: 2 }}>
        {pieData.map(({ id, value, color }) => (
          <Box key={id} sx={{ mb: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="body2" color="text.secondary">
                {id}
              </Typography>
              <Typography variant="body2" color="text.primary">
                {value} ({getPercentage(value)}%)
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={getPercentage(value)}
              sx={{
                height: 8,
                borderRadius: 1,
                backgroundColor: 'action.hover',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: color,
                },
              }}
            />
          </Box>
        ))}
      </Box>

      {/* Total */}
      <Box sx={{ mt: 2, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Total Vulnerabilities
        </Typography>
        <Typography variant="h4" color="text.primary">
          {stats.total}
        </Typography>
      </Box>
    </Box>
  );
}
