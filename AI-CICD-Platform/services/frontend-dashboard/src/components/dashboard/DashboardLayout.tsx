import React, { useState, useEffect } from 'react';
import { Box, Button, Typography, Paper, Grid, Tooltip, useMediaQuery, useTheme } from '@mui/material';
import {
  Edit as EditIcon,
  Save as SaveIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  Menu as MenuIcon,
  Architecture as ArchitectureIcon,
} from '@mui/icons-material';
import { useDashboardStore, WidgetConfig } from '../../stores/dashboard.store';
import DashboardWidget from './DashboardWidget';
import { useDashboardWebSocket } from '../../stores/dashboard.store';

// Widget selection dialog
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  IconButton,
  Drawer,
  SwipeableDrawer,
} from '@mui/material';

// Widget type icons
import {
  BarChart as ChartIcon,
  Timeline as MetricsIcon,
  BugReport as ErrorIcon,
  Security as SecurityIcon,
  Speed as PerformanceIcon,
  History as HistoryIcon,
  Code as CodeIcon,
  ViewQuilt as CustomIcon,
} from '@mui/icons-material';

const DashboardLayout: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  const {
    dashboards,
    activeDashboardId,
    isEditMode,
    widgetData,
    setEditMode,
    updateWidget,
    deleteWidget,
    duplicateWidget,
    addWidget,
    refreshWidget,
    refreshAllWidgets,
  } = useDashboardStore();

  // Initialize WebSocket connection for real-time updates
  useDashboardWebSocket();

  const [addWidgetDialogOpen, setAddWidgetDialogOpen] = useState(false);
  const [editWidgetDialogOpen, setEditWidgetDialogOpen] = useState(false);
  const [currentWidgetId, setCurrentWidgetId] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const activeDashboard = dashboards.find((d) => d.id === activeDashboardId);

  // Handle edit mode toggle
  const handleToggleEditMode = () => {
    setEditMode(!isEditMode);
  };

  // Handle widget refresh
  const handleRefreshWidget = (widgetId: string) => {
    if (activeDashboardId) {
      refreshWidget(activeDashboardId, widgetId);
    }
  };

  // Handle refresh all widgets
  const handleRefreshAll = () => {
    if (activeDashboardId) {
      refreshAllWidgets(activeDashboardId);
    }
  };

  // Handle widget edit
  const handleEditWidget = (widgetId: string) => {
    setCurrentWidgetId(widgetId);
    setEditWidgetDialogOpen(true);
  };

  // Handle widget settings
  const handleWidgetSettings = (widgetId: string) => {
    // For now, just use the same edit dialog
    handleEditWidget(widgetId);
  };

  // Handle widget delete
  const handleDeleteWidget = (widgetId: string) => {
    if (activeDashboardId) {
      deleteWidget(activeDashboardId, widgetId);
    }
  };

  // Handle widget duplicate
  const handleDuplicateWidget = (widgetId: string) => {
    if (activeDashboardId) {
      duplicateWidget(activeDashboardId, widgetId);
    }
  };

  // Handle add widget
  const handleAddWidget = (type: string) => {
    if (activeDashboardId) {
      // Create a new widget with default settings based on type
      const newWidget: Omit<WidgetConfig, 'id'> = {
        type: type as any,
        title: getWidgetTitle(type),
        size: getWidgetDefaultSize(type),
        position: { x: 0, y: 0 }, // Will be adjusted by the grid layout
        settings: {},
        realtime: true,
      };
      
      addWidget(activeDashboardId, newWidget);
      setAddWidgetDialogOpen(false);
    }
  };

  // Get default widget title based on type
  const getWidgetTitle = (type: string): string => {
    switch (type) {
      case 'metrics-summary':
        return 'System Metrics';
      case 'pipeline-status':
        return 'Pipeline Status';
      case 'error-classification':
        return 'Error Classification';
      case 'security-vulnerabilities':
        return 'Security Vulnerabilities';
      case 'service-health':
        return 'Service Health';
      case 'recent-errors':
        return 'Recent Errors';
      case 'ml-classification':
        return 'ML Error Classification';
      case 'architecture-diagram':
        return 'Architecture Diagrams';
      case 'custom-chart':
        return 'Custom Chart';
      case 'performance-metrics':
        return 'Performance Metrics';
      case 'deployment-history':
        return 'Deployment History';
      case 'code-quality':
        return 'Code Quality';
      default:
        return 'New Widget';
    }
  };

  // Get default widget size based on type
  const getWidgetDefaultSize = (type: string): WidgetConfig['size'] => {
    switch (type) {
      case 'metrics-summary':
        return { w: 12, h: 4, minW: 6, minH: 3 };
      case 'pipeline-status':
      case 'error-classification':
      case 'service-health':
      case 'recent-errors':
      case 'custom-chart':
      case 'performance-metrics':
      case 'deployment-history':
      case 'code-quality':
        return { w: 6, h: 6, minW: 4, minH: 4 };
      case 'security-vulnerabilities':
        return { w: 12, h: 5, minW: 6, minH: 4 };
      case 'ml-classification':
        return { w: 12, h: 8, minW: 8, minH: 6 };
      case 'architecture-diagram':
        return { w: 12, h: 8, minW: 8, minH: 6 };
      default:
        return { w: 6, h: 6, minW: 4, minH: 4 };
    }
  };

  // Get widget icon based on type
  const getWidgetIcon = (type: string): React.ReactNode => {
    switch (type) {
      case 'metrics-summary':
        return <MetricsIcon />;
      case 'pipeline-status':
        return <HistoryIcon />;
      case 'error-classification':
        return <ErrorIcon />;
      case 'security-vulnerabilities':
        return <SecurityIcon />;
      case 'service-health':
        return <PerformanceIcon />;
      case 'recent-errors':
        return <ErrorIcon />;
      case 'ml-classification':
        return <ChartIcon />;
      case 'architecture-diagram':
        return <ArchitectureIcon />;
      case 'custom-chart':
        return <CustomIcon />;
      case 'performance-metrics':
        return <PerformanceIcon />;
      case 'deployment-history':
        return <HistoryIcon />;
      case 'code-quality':
        return <CodeIcon />;
      default:
        return <CustomIcon />;
    }
  };

  // Available widget types for add dialog
  const availableWidgetTypes = [
    { type: 'metrics-summary', name: 'System Metrics' },
    { type: 'pipeline-status', name: 'Pipeline Status' },
    { type: 'error-classification', name: 'Error Classification' },
    { type: 'security-vulnerabilities', name: 'Security Vulnerabilities' },
    { type: 'service-health', name: 'Service Health' },
    { type: 'recent-errors', name: 'Recent Errors' },
    { type: 'ml-classification', name: 'ML Error Classification' },
    { type: 'architecture-diagram', name: 'Architecture Diagrams' },
    { type: 'custom-chart', name: 'Custom Chart' },
    { type: 'performance-metrics', name: 'Performance Metrics' },
    { type: 'deployment-history', name: 'Deployment History' },
    { type: 'code-quality', name: 'Code Quality' },
  ];

  if (!activeDashboard) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h5">No dashboard selected</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%' }}>
      {/* Dashboard header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 2,
          flexDirection: isMobile ? 'column' : 'row',
        }}
      >
        <Box sx={{ width: isMobile ? '100%' : 'auto', mb: isMobile ? 2 : 0 }}>
          <Typography variant="h5">{activeDashboard.name}</Typography>
          {activeDashboard.description && (
            <Typography variant="body2" color="text.secondary">
              {activeDashboard.description}
            </Typography>
          )}
        </Box>
        
        {isMobile ? (
          // Mobile view - show menu button
          <Box sx={{ width: '100%', display: 'flex', justifyContent: 'space-between' }}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={handleRefreshAll}
              size="small"
            >
              Refresh
            </Button>
            <IconButton 
              color="primary" 
              onClick={() => setMobileMenuOpen(true)}
              edge="end"
            >
              <MenuIcon />
            </IconButton>
            
            {/* Mobile menu drawer */}
            <SwipeableDrawer
              anchor="bottom"
              open={mobileMenuOpen}
              onClose={() => setMobileMenuOpen(false)}
              onOpen={() => setMobileMenuOpen(true)}
            >
              <Box sx={{ p: 2 }}>
                <Typography variant="h6" sx={{ mb: 2 }}>Dashboard Actions</Typography>
                <List>
                  <ListItem button onClick={handleRefreshAll}>
                    <ListItemIcon><RefreshIcon /></ListItemIcon>
                    <ListItemText primary="Refresh All Widgets" />
                  </ListItem>
                  
                  {isEditMode ? (
                    <>
                      <ListItem button onClick={() => setAddWidgetDialogOpen(true)}>
                        <ListItemIcon><AddIcon /></ListItemIcon>
                        <ListItemText primary="Add Widget" />
                      </ListItem>
                      <ListItem button onClick={handleToggleEditMode}>
                        <ListItemIcon><SaveIcon /></ListItemIcon>
                        <ListItemText primary="Save Layout" />
                      </ListItem>
                    </>
                  ) : (
                    <ListItem button onClick={handleToggleEditMode}>
                      <ListItemIcon><EditIcon /></ListItemIcon>
                      <ListItemText primary="Edit Layout" />
                    </ListItem>
                  )}
                </List>
              </Box>
            </SwipeableDrawer>
          </Box>
        ) : (
          // Desktop view - show buttons
          <Box>
            <Tooltip title="Refresh All Widgets">
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={handleRefreshAll}
                sx={{ mr: 1 }}
                size={isTablet ? "small" : "medium"}
              >
                Refresh All
              </Button>
            </Tooltip>
            {isEditMode ? (
              <>
                <Button
                  variant="outlined"
                  startIcon={<AddIcon />}
                  onClick={() => setAddWidgetDialogOpen(true)}
                  sx={{ mr: 1 }}
                  size={isTablet ? "small" : "medium"}
                >
                  Add Widget
                </Button>
                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={handleToggleEditMode}
                  size={isTablet ? "small" : "medium"}
                >
                  Save Layout
                </Button>
              </>
            ) : (
              <Button
                variant="outlined"
                startIcon={<EditIcon />}
                onClick={handleToggleEditMode}
                size={isTablet ? "small" : "medium"}
              >
                Edit Layout
              </Button>
            )}
          </Box>
        )}
      </Box>

      {/* Dashboard grid */}
      <Box sx={{ mt: 2 }}>
        <Grid container spacing={2}>
          {activeDashboard.widgets.map((widget) => (
            <Grid
              item
              xs={12}
              sm={widget.size.w <= 6 ? 6 : 12}
              md={widget.size.w <= 4 ? 4 : widget.size.w <= 8 ? 8 : 12}
              lg={widget.size.w <= 3 ? 3 : widget.size.w <= 6 ? 6 : widget.size.w <= 9 ? 9 : 12}
              key={widget.id}
              sx={{
                height: isMobile 
                  ? 'auto' 
                  : `${widget.size.h * activeDashboard.layout.rowHeight}px`,
                minHeight: isMobile 
                  ? '250px' 
                  : `${widget.size.minH ? widget.size.minH * activeDashboard.layout.rowHeight : 200}px`,
              }}
            >
              <DashboardWidget
                widget={widget}
                dashboardId={activeDashboard.id}
                data={widgetData[widget.id]?.data}
                isEditMode={isEditMode}
                onEdit={handleEditWidget}
                onDelete={handleDeleteWidget}
                onSettings={handleWidgetSettings}
                onDuplicate={handleDuplicateWidget}
                onRefresh={handleRefreshWidget}
                isLoading={false}
              />
            </Grid>
          ))}

          {/* Empty state when no widgets */}
          {activeDashboard.widgets.length === 0 && (
            <Grid item xs={12}>
              <Paper
                sx={{
                  p: 4,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '300px',
                  textAlign: 'center',
                }}
              >
                <Typography variant="h6" gutterBottom>
                  This dashboard is empty
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Add widgets to start monitoring your system
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => setAddWidgetDialogOpen(true)}
                >
                  Add Widget
                </Button>
              </Paper>
            </Grid>
          )}
        </Grid>
      </Box>

      {/* Add Widget Dialog */}
      <Dialog
        open={addWidgetDialogOpen}
        onClose={() => setAddWidgetDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        fullScreen={isMobile}
      >
        <DialogTitle>Add Widget</DialogTitle>
        <DialogContent>
          <List>
            {availableWidgetTypes.map((widgetType, index) => (
              <React.Fragment key={widgetType.type}>
                <ListItem
                  button
                  onClick={() => handleAddWidget(widgetType.type)}
                >
                  <ListItemIcon>{getWidgetIcon(widgetType.type)}</ListItemIcon>
                  <ListItemText
                    primary={widgetType.name}
                    secondary={`Add a ${widgetType.name.toLowerCase()} widget to your dashboard`}
                  />
                </ListItem>
                {index < availableWidgetTypes.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddWidgetDialogOpen(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Widget Dialog - simplified for now */}
      <Dialog
        open={editWidgetDialogOpen}
        onClose={() => setEditWidgetDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        fullScreen={isMobile}
      >
        <DialogTitle>Edit Widget</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary">
            Widget editing functionality will be implemented in a future update.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditWidgetDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DashboardLayout;
