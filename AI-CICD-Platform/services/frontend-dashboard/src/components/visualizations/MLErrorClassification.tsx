import React, { useState, useEffect } from 'react';
import { ResponsiveRadar } from '@nivo/radar';
import { ResponsiveHeatMap, HeatMapDatum } from '@nivo/heatmap';
import { ResponsiveSankey } from '@nivo/sankey';
import { Box, Typography, Paper, Grid, Tabs, Tab, useTheme, useMediaQuery } from '@mui/material';
import { PipelineError } from '../../config/api';
import ErrorClassificationChart from './ErrorClassificationChart';

interface MLErrorClassificationProps {
  errors: PipelineError[];
  mlClassifications?: Record<string, any>[];
  isRealTime?: boolean;
}

const MLErrorClassification: React.FC<MLErrorClassificationProps> = ({
  errors,
  mlClassifications = [],
  isRealTime = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // Process error data for visualizations
  const processErrorsByCategory = () => {
    const categories: Record<string, number> = {};
    
    errors.forEach(error => {
      if (!categories[error.category]) {
        categories[error.category] = 0;
      }
      categories[error.category]++;
    });
    
    return Object.entries(categories).map(([category, count]) => ({
      id: category,
      label: category,
      value: count,
    }));
  };

  const processErrorsBySeverity = () => {
    const severities: Record<string, number> = {};
    
    errors.forEach(error => {
      if (!severities[error.severity]) {
        severities[error.severity] = 0;
      }
      severities[error.severity]++;
    });
    
    return Object.entries(severities).map(([severity, count]) => ({
      id: severity,
      label: severity,
      value: count,
    }));
  };

  // Generate radar data for ML confidence scores
  const generateRadarData = () => {
    if (!mlClassifications || mlClassifications.length === 0) {
      return [];
    }

    // Extract unique error categories and create radar data
    const categories = new Set<string>();
    mlClassifications.forEach(classification => {
      if (classification.classifications?.category?.prediction) {
        categories.add(classification.classifications.category.prediction);
      }
    });

    return Array.from(categories).map(category => {
      const dataPoint: Record<string, any> = { category };
      
      // Add confidence scores for different models
      mlClassifications.forEach((classification, index) => {
        if (classification.classifications?.category?.prediction === category) {
          dataPoint[`model${index + 1}`] = classification.classifications.category.confidence * 100;
        }
      });
      
      return dataPoint;
    });
  };

  // Generate heatmap data for error correlations
  const generateHeatmapData = () => {
    if (errors.length === 0) {
      return { data: [], xKeys: [], yKeys: [] };
    }

    // Extract categories and severities
    const categories = Array.from(new Set(errors.map(e => e.category)));
    const severities = Array.from(new Set(errors.map(e => e.severity)));
    
    // Format data for HeatMap component
    const data = categories.map(category => {
      const heatmapData = severities.map(severity => {
        const count = errors.filter(e => e.category === category && e.severity === severity).length;
        return { x: severity, y: count };
      });
      
      return {
        id: category,
        data: heatmapData
      };
    });
    
    return { data, xKeys: severities, yKeys: categories };
  };

  // Generate Sankey diagram data for error flows
  const generateSankeyData = () => {
    if (errors.length === 0) {
      return { nodes: [], links: [] };
    }

    // Create nodes for categories and severities
    const categories = Array.from(new Set(errors.map(e => e.category)));
    const severities = Array.from(new Set(errors.map(e => e.severity)));
    
    const nodes = [
      ...categories.map(category => ({ id: category })),
      ...severities.map(severity => ({ id: severity })),
    ];
    
    // Create links between categories and severities
    const links: Array<{ source: string; target: string; value: number }> = [];
    
    categories.forEach(category => {
      severities.forEach(severity => {
        const count = errors.filter(e => e.category === category && e.severity === severity).length;
        if (count > 0) {
          links.push({
            source: category,
            target: severity,
            value: count,
          });
        }
      });
    });
    
    return { nodes, links };
  };

  // Prepare data for visualizations
  const categoryData = processErrorsByCategory();
  const severityData = processErrorsBySeverity();
  const radarData = generateRadarData();
  const heatmapData = generateHeatmapData();
  const sankeyData = generateSankeyData();

  return (
    <Box sx={{ width: '100%' }}>
      <Typography 
        variant={isMobile ? "subtitle1" : "h5"} 
        gutterBottom
        sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          flexWrap: 'wrap',
          mb: isMobile ? 1 : 2
        }}
      >
        ML-Based Error Classification
        {isRealTime && (
          <Typography 
            component="span" 
            color="primary" 
            sx={{ 
              ml: 1, 
              fontSize: isMobile ? '0.7rem' : '0.8rem',
              whiteSpace: 'nowrap'
            }}
          >
            (Real-time)
          </Typography>
        )}
      </Typography>

      <Tabs 
        value={activeTab} 
        onChange={handleTabChange} 
        sx={{ 
          mb: isMobile ? 1 : 2,
          '.MuiTab-root': {
            minWidth: isMobile ? 'auto' : 90,
            padding: isMobile ? '6px 12px' : '12px 16px',
            fontSize: isMobile ? '0.75rem' : 'inherit'
          }
        }}
        variant={isMobile ? "scrollable" : "standard"}
        scrollButtons={isMobile ? "auto" : undefined}
      >
        <Tab label="Overview" />
        <Tab label="Advanced Analysis" />
        <Tab label="Error Flows" />
      </Tabs>

      {/* Overview Tab */}
      {activeTab === 0 && (
        <Grid container spacing={isMobile ? 1 : 2}>
          <Grid item xs={12} md={6}>
            <ErrorClassificationChart
              title="Errors by Category"
              data={categoryData}
              type="pie"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <ErrorClassificationChart
              title="Errors by Severity"
              data={severityData}
              type="bar"
            />
          </Grid>
        </Grid>
      )}

      {/* Advanced Analysis Tab */}
      {activeTab === 1 && (
        <Grid container spacing={isMobile ? 1 : 2}>
          <Grid item xs={12}>
            <Paper sx={{ p: isMobile ? 1 : 2, height: 'auto', mb: isMobile ? 1 : 2 }}>
              <Typography variant={isMobile ? "subtitle2" : "h6"} gutterBottom>
                ML Classification Confidence
              </Typography>
              <Box sx={{ height: isMobile ? 300 : 400 }}>
                {radarData.length > 0 ? (
                  <ResponsiveRadar
                    data={radarData}
                    keys={['model1', 'model2', 'model3'].filter(
                      key => radarData.some(d => d[key] !== undefined)
                    )}
                    indexBy="category"
                    maxValue={100}
                    margin={{ 
                      top: isMobile ? 50 : 70, 
                      right: isMobile ? 50 : 80, 
                      bottom: isMobile ? 30 : 40, 
                      left: isMobile ? 50 : 80 
                    }}
                    borderColor={{ from: 'color' }}
                    gridLabelOffset={isMobile ? 24 : 36}
                    dotSize={isMobile ? 6 : 10}
                    dotColor={{ theme: 'background' }}
                    dotBorderWidth={2}
                    colors={{ scheme: 'category10' }}
                    blendMode="multiply"
                    motionConfig="wobbly"
                    legends={isMobile ? [] : [
                      {
                        anchor: 'top-left',
                        direction: 'column',
                        translateX: -50,
                        translateY: -40,
                        itemWidth: 80,
                        itemHeight: 20,
                        itemTextColor: theme.palette.text.primary,
                        symbolSize: 12,
                        symbolShape: 'circle',
                        effects: [
                          {
                            on: 'hover',
                            style: {
                              itemTextColor: theme.palette.primary.main,
                            },
                          },
                        ],
                      },
                    ]}
                  />
                ) : (
                  <Typography 
                    color="text.secondary" 
                    sx={{ 
                      textAlign: 'center', 
                      pt: isMobile ? 5 : 10,
                      fontSize: isMobile ? '0.875rem' : 'inherit'
                    }}
                  >
                    No ML classification data available
                  </Typography>
                )}
              </Box>
            </Paper>
          </Grid>
          <Grid item xs={12}>
            <Paper sx={{ p: isMobile ? 1 : 2, height: 'auto', mb: isMobile ? 1 : 2 }}>
              <Typography variant={isMobile ? "subtitle2" : "h6"} gutterBottom>
                Error Correlation Heatmap
              </Typography>
              <Box sx={{ height: isMobile ? 300 : 400 }}>
                {heatmapData.data.length > 0 ? (
                  <ResponsiveHeatMap
                    data={heatmapData.data}
                    margin={{ 
                      top: isMobile ? 30 : 60, 
                      right: isMobile ? 50 : 90, 
                      bottom: isMobile ? 30 : 60, 
                      left: isMobile ? 50 : 90 
                    }}
                    forceSquare={true}
                    axisTop={{
                      tickSize: 5,
                      tickPadding: 5,
                      tickRotation: -45,
                      legend: 'Severity',
                      legendOffset: isMobile ? -25 : -40,
                      legendPosition: 'middle',
                      format: (value) => isMobile && value.length > 8 ? `${value.substring(0, 6)}...` : value
                    }}
                    axisRight={null}
                    axisBottom={null}
                    axisLeft={{
                      tickSize: 5,
                      tickPadding: 5,
                      tickRotation: 0,
                      legend: 'Category',
                      legendPosition: 'middle',
                      legendOffset: isMobile ? -40 : -72,
                      format: (value) => isMobile && value.length > 8 ? `${value.substring(0, 6)}...` : value
                    }}
                    colors={{
                      type: 'sequential',
                      scheme: 'blues',
                    }}
                    emptyColor="#eeeeee"
                    borderWidth={1}
                    borderColor={{ from: 'color', modifiers: [['darker', 0.4]] }}
                    legends={isMobile ? [] : [
                      {
                        anchor: 'bottom',
                        translateX: 0,
                        translateY: 30,
                        length: 400,
                        thickness: 8,
                        direction: 'row',
                        tickPosition: 'after',
                        tickSize: 3,
                        tickSpacing: 4,
                        tickOverlap: false,
                        tickFormat: '>-.2s',
                        title: 'Count',
                        titleAlign: 'start',
                        titleOffset: 4,
                      },
                    ]}
                    animate={true}
                    motionConfig="gentle"
                  />
                ) : (
                  <Typography 
                    color="text.secondary" 
                    sx={{ 
                      textAlign: 'center', 
                      pt: isMobile ? 5 : 10,
                      fontSize: isMobile ? '0.875rem' : 'inherit'
                    }}
                  >
                    No error correlation data available
                  </Typography>
                )}
              </Box>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Error Flows Tab */}
      {activeTab === 2 && (
        <Grid container spacing={isMobile ? 1 : 2}>
          <Grid item xs={12}>
            <Paper sx={{ p: isMobile ? 1 : 2, height: 'auto', mb: isMobile ? 1 : 2 }}>
              <Typography variant={isMobile ? "subtitle2" : "h6"} gutterBottom>
                Error Flow Diagram
              </Typography>
              <Box sx={{ height: isMobile ? 350 : 500 }}>
                {sankeyData.nodes.length > 0 ? (
                  <ResponsiveSankey
                    data={sankeyData}
                    margin={{ 
                      top: isMobile ? 20 : 40, 
                      right: isMobile ? 20 : 160, 
                      bottom: isMobile ? 20 : 40, 
                      left: isMobile ? 20 : 50 
                    }}
                    align="justify"
                    colors={{ scheme: 'category10' }}
                    nodeOpacity={1}
                    nodeHoverOthersOpacity={0.35}
                    nodeThickness={isMobile ? 12 : 18}
                    nodeSpacing={isMobile ? 12 : 24}
                    nodeBorderWidth={0}
                    nodeBorderColor={{
                      from: 'color',
                      modifiers: [['darker', 0.8]],
                    }}
                    linkOpacity={0.5}
                    linkHoverOthersOpacity={0.1}
                    linkContract={isMobile ? 1 : 3}
                    enableLinkGradient={true}
                    labelPosition="outside"
                    labelOrientation="vertical"
                    labelPadding={isMobile ? 8 : 16}
                    labelTextColor={{
                      from: 'color',
                      modifiers: [['darker', 1]],
                    }}
                    legends={isMobile ? [] : [
                      {
                        anchor: 'bottom-right',
                        direction: 'column',
                        translateX: 130,
                        itemWidth: 100,
                        itemHeight: 14,
                        itemDirection: 'right-to-left',
                        itemsSpacing: 2,
                        itemTextColor: theme.palette.text.primary,
                        symbolSize: 14,
                        effects: [
                          {
                            on: 'hover',
                            style: {
                              itemTextColor: theme.palette.primary.main,
                            },
                          },
                        ],
                      },
                    ]}
                  />
                ) : (
                  <Typography 
                    color="text.secondary" 
                    sx={{ 
                      textAlign: 'center', 
                      pt: isMobile ? 5 : 10,
                      fontSize: isMobile ? '0.875rem' : 'inherit'
                    }}
                  >
                    No error flow data available
                  </Typography>
                )}
              </Box>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default MLErrorClassification;
