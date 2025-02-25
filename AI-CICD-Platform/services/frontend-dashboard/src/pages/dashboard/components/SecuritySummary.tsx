import { useMemo } from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { ResponsivePie } from '@nivo/pie';
import { Vulnerability } from '../../../config/api';

interface SecuritySummaryProps {
  vulnerabilities: Vulnerability[];
}

export default function SecuritySummary({ vulnerabilities }: SecuritySummaryProps) {

  const chartData = useMemo(() => {
    // Group vulnerabilities by severity
    const severityCounts = vulnerabilities.reduce((acc, vuln) => {
      acc[vuln.severity] = (acc[vuln.severity] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    // Convert to Nivo pie chart format
    return Object.entries(severityCounts).map(([severity, count]) => ({
      id: severity,
      label: severity,
      value: count,
      color: getColorBySeverity(severity),
    }));
  }, [vulnerabilities]);

  const getColorBySeverity = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return '#d32f2f';
      case 'high':
        return '#f44336';
      case 'medium':
        return '#ff9800';
      case 'low':
        return '#2196f3';
      default:
        return '#9e9e9e';
    }
  };

  return (
    <Paper sx={{ p: 2, height: 400 }}>
      <Typography variant="h6" gutterBottom>
        Security Overview
      </Typography>
      <Box sx={{ height: 350 }}>
        <ResponsivePie
          data={chartData}
          margin={{ top: 40, right: 80, bottom: 80, left: 80 }}
          innerRadius={0.5}
          padAngle={0.7}
          cornerRadius={3}
          activeOuterRadiusOffset={8}
          borderWidth={1}
          borderColor={{
            from: 'color',
            modifiers: [['darker', 0.2]],
          }}
          arcLinkLabelsSkipAngle={10}
          arcLinkLabelsTextColor="#333333"
          arcLinkLabelsThickness={2}
          arcLinkLabelsColor={{ from: 'color' }}
          arcLabelsSkipAngle={10}
          arcLabelsTextColor={{
            from: 'color',
            modifiers: [['darker', 2]],
          }}
          legends={[
            {
              anchor: 'bottom',
              direction: 'row',
              justify: false,
              translateX: 0,
              translateY: 56,
              itemsSpacing: 0,
              itemWidth: 100,
              itemHeight: 18,
              itemTextColor: '#999',
              itemDirection: 'left-to-right',
              itemOpacity: 1,
              symbolSize: 18,
              symbolShape: 'circle',
              effects: [
                {
                  on: 'hover',
                  style: {
                    itemTextColor: '#000',
                  },
                },
              ],
            },
          ]}
        />
      </Box>
    </Paper>
  );
}
