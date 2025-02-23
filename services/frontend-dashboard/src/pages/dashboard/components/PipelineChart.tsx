import { useMemo } from 'react';
import { ResponsiveLine } from '@nivo/line';
import { Box, useTheme } from '@mui/material';
import { Pipeline } from '../../../config/api';
import { format, subDays } from 'date-fns';
import { eachDayOfInterval } from 'date-fns/eachDayOfInterval';

interface PipelineChartProps {
  pipelines: Pipeline[];
}

interface DailyCount {
  date: string;
  successful: number;
  failed: number;
  running: number;
}

interface ChartData {
  id: string;
  color: string;
  data: Array<{
    x: string;
    y: number;
  }>;
}

export default function PipelineChart({ pipelines }: PipelineChartProps) {
  const theme = useTheme();

  const data: ChartData[] = useMemo(() => {
    // Get date range for last 7 days
    const endDate = new Date();
    const startDate = subDays(endDate, 6);
    
    // Generate array of dates
    const dates = eachDayOfInterval({ start: startDate, end: endDate });
    
    // Count pipelines by status for each date
    const statusCounts: DailyCount[] = dates.map((date: Date) => {
      const dayPipelines = pipelines.filter(pipeline => {
        const pipelineDate = new Date(pipeline.created_at);
        return format(pipelineDate, 'yyyy-MM-dd') === format(date, 'yyyy-MM-dd');
      });

      return {
        date: format(date, 'MM/dd'),
        successful: dayPipelines.filter(p => p.status === 'completed').length,
        failed: dayPipelines.filter(p => p.status === 'failed').length,
        running: dayPipelines.filter(p => p.status === 'running').length,
      };
    });

    // Format data for Nivo Line chart
    return [
      {
        id: 'Successful',
        color: theme.palette.success.main,
        data: statusCounts.map(count => ({
          x: count.date,
          y: count.successful,
        })),
      },
      {
        id: 'Failed',
        color: theme.palette.error.main,
        data: statusCounts.map(count => ({
          x: count.date,
          y: count.failed,
        })),
      },
      {
        id: 'Running',
        color: theme.palette.info.main,
        data: statusCounts.map(count => ({
          x: count.date,
          y: count.running,
        })),
      },
    ];
  }, [pipelines, theme.palette]);

  return (
    <Box sx={{ height: 300 }}>
      <ResponsiveLine
        data={data}
        margin={{ top: 20, right: 20, bottom: 50, left: 50 }}
        xScale={{
          type: 'point',
        }}
        yScale={{
          type: 'linear',
          min: 0,
          max: 'auto',
        }}
        curve="monotoneX"
        axisTop={null}
        axisRight={null}
        axisBottom={{
          tickSize: 5,
          tickPadding: 5,
          tickRotation: 0,
        }}
        axisLeft={{
          tickSize: 5,
          tickPadding: 5,
          tickRotation: 0,
        }}
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
            symbolSize: 12,
            symbolShape: 'circle',
          },
        ]}
        theme={{
          axis: {
            ticks: {
              text: {
                fill: theme.palette.text.secondary,
              },
            },
          },
          grid: {
            line: {
              stroke: theme.palette.divider,
              strokeWidth: 1,
            },
          },
          legends: {
            text: {
              fill: theme.palette.text.primary,
            },
          },
        }}
      />
    </Box>
  );
}
