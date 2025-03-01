import React from 'react';
import { ResponsivePie } from '@nivo/pie';
import { ResponsiveBar } from '@nivo/bar';
import { Box, Typography, Paper, useTheme, useMediaQuery } from '@mui/material';
import { BarDatum } from '@nivo/bar';

interface ErrorClassificationData {
  id: string;
  label: string;
  value: number;
  color?: string;
  [key: string]: any; // Add index signature for BarDatum compatibility
}

interface ErrorClassificationChartProps {
  title: string;
  data: ErrorClassificationData[];
  type: 'pie' | 'bar';
  height?: number;
}

const ErrorClassificationChart: React.FC<ErrorClassificationChartProps> = ({
  title,
  data,
  type = 'pie',
  height = 300,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  
  // Adjust height for mobile
  const chartHeight = isMobile ? 250 : height;

  return (
    <Paper sx={{ p: isMobile ? 1 : 2, height: 'auto', mb: isMobile ? 1 : 2 }}>
      <Typography variant={isMobile ? "subtitle2" : "h6"} gutterBottom>
        {title}
      </Typography>
      <Box sx={{ height: chartHeight }}>
        {type === 'pie' ? (
          <ResponsivePie
            data={data}
            margin={{ 
              top: isMobile ? 20 : 40, 
              right: isMobile ? 20 : 80, 
              bottom: isMobile ? 50 : 80, 
              left: isMobile ? 20 : 80 
            }}
            innerRadius={0.5}
            padAngle={0.7}
            cornerRadius={3}
            activeOuterRadiusOffset={8}
            borderWidth={1}
            borderColor={{
              from: 'color',
              modifiers: [['darker', 0.2]],
            }}
            arcLinkLabelsSkipAngle={isMobile ? 15 : 10}
            arcLinkLabelsTextColor={theme.palette.text.primary}
            arcLinkLabelsThickness={2}
            arcLinkLabelsColor={{ from: 'color' }}
            arcLabelsSkipAngle={isMobile ? 15 : 10}
            arcLabelsTextColor={{
              from: 'color',
              modifiers: [['darker', 2]],
            }}
            enableArcLabels={!isMobile}
            // Remove the problematic arcLinkLabel property
            legends={isMobile ? [] : [
              {
                anchor: 'bottom',
                direction: 'row',
                justify: false,
                translateX: 0,
                translateY: 56,
                itemsSpacing: 0,
                itemWidth: 100,
                itemHeight: 18,
                itemTextColor: theme.palette.text.primary,
                itemDirection: 'left-to-right',
                itemOpacity: 1,
                symbolSize: 18,
                symbolShape: 'circle',
              },
            ]}
          />
        ) : (
          <ResponsiveBar
            data={data}
            keys={['value']}
            indexBy="label"
            margin={{ 
              top: isMobile ? 30 : 50, 
              right: isMobile ? 20 : 50, 
              bottom: isMobile ? 40 : 50, 
              left: isMobile ? 40 : 60 
            }}
            padding={0.3}
            valueScale={{ type: 'linear' }}
            indexScale={{ type: 'band', round: true }}
            colors={{ scheme: 'nivo' }}
            borderColor={{
              from: 'color',
              modifiers: [['darker', 1.6]],
            }}
            axisTop={null}
            axisRight={null}
            axisBottom={{
              tickSize: 5,
              tickPadding: 5,
              tickRotation: isMobile ? -45 : 0,
              legend: isMobile ? undefined : 'Category',
              legendPosition: 'middle',
              legendOffset: 32,
              format: (value) => typeof value === 'string' && isMobile && value.length > 8 ? `${value.substring(0, 6)}...` : value
            }}
            axisLeft={{
              tickSize: 5,
              tickPadding: 5,
              tickRotation: 0,
              legend: isMobile ? undefined : 'Count',
              legendPosition: 'middle',
              legendOffset: -40,
            }}
            labelSkipWidth={isMobile ? 20 : 12}
            labelSkipHeight={isMobile ? 20 : 12}
            labelTextColor={{
              from: 'color',
              modifiers: [['darker', 1.6]],
            }}
            enableLabel={!isMobile}
            legends={isMobile ? [] : [
              {
                dataFrom: 'keys',
                anchor: 'bottom-right',
                direction: 'column',
                justify: false,
                translateX: 120,
                translateY: 0,
                itemsSpacing: 2,
                itemWidth: 100,
                itemHeight: 20,
                itemDirection: 'left-to-right',
                itemOpacity: 0.85,
                symbolSize: 20,
                effects: [
                  {
                    on: 'hover',
                    style: {
                      itemOpacity: 1,
                    },
                  },
                ],
              },
            ]}
            role="application"
            ariaLabel="Error classification chart"
          />
        )}
      </Box>
    </Paper>
  );
};

export default ErrorClassificationChart;
