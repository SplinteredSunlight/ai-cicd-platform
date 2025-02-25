import { useMemo } from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { ResponsiveLine } from '@nivo/line';
import { Pipeline } from '../../../config/api';

interface DataPoint {
  x: string;
  y: number;
}

interface ChartData {
  id: string;
  data: DataPoint[];
}

interface PipelineChartProps {
  pipelines: Pipeline[];
}

export default function PipelineChart({ pipelines }: PipelineChartProps) {

  const chartData = useMemo(() => {
    // Group pipelines by date and status
    const statusCounts = pipelines.reduce<Record<string, Record<'completed' | 'failed' | 'running', number>>>((acc, pipeline) => {
      const date = new Date(pipeline.created_at).toLocaleDateString();
      acc[date] = acc[date] || { completed: 0, failed: 0, running: 0 };
      acc[date][pipeline.status as 'completed' | 'failed' | 'running']++;
      return acc;
    }, {});

    // Convert to Nivo line chart format
    const data: ChartData[] = [
      {
        id: 'Completed',
        data: Object.entries(statusCounts).map(([date, counts]) => ({
          x: date,
          y: counts.completed,
        })),
      },
      {
        id: 'Failed',
        data: Object.entries(statusCounts).map(([date, counts]) => ({
          x: date,
          y: counts.failed,
        })),
      },
      {
        id: 'Running',
        data: Object.entries(statusCounts).map(([date, counts]) => ({
          x: date,
          y: counts.running,
        })),
      },
    ];

    return data;
  }, [pipelines]);

  return (
    <Paper sx={{ p: 2, height: 400 }}>
      <Typography variant="h6" gutterBottom>
        Pipeline Activity
      </Typography>
      <Box sx={{ height: 350 }}>
        <ResponsiveLine
          data={chartData}
          margin={{ top: 20, right: 20, bottom: 50, left: 50 }}
          xScale={{ type: 'point' }}
          yScale={{
            type: 'linear',
            min: 'auto',
            max: 'auto',
            stacked: false,
          }}
          curve="monotoneX"
          axisTop={null}
          axisRight={null}
          axisBottom={{
            tickSize: 5,
            tickPadding: 5,
            tickRotation: -45,
            legend: 'Date',
            legendOffset: 40,
            legendPosition: 'middle',
          }}
          axisLeft={{
            tickSize: 5,
            tickPadding: 5,
            tickRotation: 0,
            legend: 'Count',
            legendOffset: -40,
            legendPosition: 'middle',
          }}
          colors={{ scheme: 'category10' }}
          pointSize={8}
          pointColor={{ theme: 'background' }}
          pointBorderWidth={2}
          pointBorderColor={{ from: 'serieColor' }}
          pointLabelYOffset={-12}
          useMesh={true}
          legends={[
            {
              anchor: 'top',
              direction: 'row',
              justify: false,
              translateX: 0,
              translateY: -20,
              itemsSpacing: 0,
              itemDirection: 'left-to-right',
              itemWidth: 80,
              itemHeight: 20,
              itemOpacity: 0.75,
              symbolSize: 12,
              symbolShape: 'circle',
              symbolBorderColor: 'rgba(0, 0, 0, .5)',
              effects: [
                {
                  on: 'hover',
                  style: {
                    itemBackground: 'rgba(0, 0, 0, .03)',
                    itemOpacity: 1,
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
