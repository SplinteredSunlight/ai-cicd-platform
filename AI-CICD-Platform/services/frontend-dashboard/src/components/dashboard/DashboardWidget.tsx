import React, { useState, useEffect, lazy, Suspense } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  IconButton,
  Menu,
  MenuItem,
  Typography,
  Box,
  CircularProgress,
  Divider,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  MoreVert as MoreIcon,
  Refresh as RefreshIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ContentCopy as DuplicateIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { WidgetConfig } from '../../stores/dashboard.store';

interface DashboardWidgetProps {
  widget: WidgetConfig;
  dashboardId?: string;
  isEditMode?: boolean;
  onRefresh?: (widgetId: string) => void;
  onEdit?: (widgetId: string) => void;
  onDelete?: (widgetId: string) => void;
  onDuplicate?: (widgetId: string) => void;
  onSettings?: (widgetId: string) => void;
  data?: any;
  isLoading?: boolean;
  children?: React.ReactNode;
}

const DashboardWidget: React.FC<DashboardWidgetProps> = ({
  widget,
  dashboardId,
  isEditMode = false,
  onRefresh,
  onEdit,
  onDelete,
  onDuplicate,
  onSettings,
  data,
  isLoading = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [widgetContent, setWidgetContent] = useState<React.ReactNode>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleRefresh = () => {
    handleMenuClose();
    if (onRefresh) {
      onRefresh(widget.id);
    }
  };

  const handleEdit = () => {
    handleMenuClose();
    if (onEdit) {
      onEdit(widget.id);
    }
  };

  const handleDelete = () => {
    handleMenuClose();
    if (onDelete) {
      onDelete(widget.id);
    }
  };

  const handleDuplicate = () => {
    handleMenuClose();
    if (onDuplicate) {
      onDuplicate(widget.id);
    }
  };

  const handleSettings = () => {
    handleMenuClose();
    if (onSettings) {
      onSettings(widget.id);
    }
  };

  // Render widget content based on widget type
  useEffect(() => {
    if (isLoading) {
      setWidgetContent(
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '100%',
            minHeight: isMobile ? '100px' : '150px',
          }}
        >
          <CircularProgress size={isMobile ? 30 : 40} />
        </Box>
      );
      return;
    }

    if (!data) {
      setWidgetContent(
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '100%',
            minHeight: isMobile ? '100px' : '150px',
          }}
        >
          <Typography color="text.secondary" variant={isMobile ? "body2" : "body1"}>
            No data available
          </Typography>
        </Box>
      );
      return;
    }

    // Render different content based on widget type
    switch (widget.type) {
      case 'metrics-summary':
        setWidgetContent(
          <Box>
            <Typography variant={isMobile ? "body2" : "body1"}>System Metrics Summary</Typography>
            <Box sx={{ mt: isMobile ? 1 : 2 }}>
              {data && typeof data === 'object' && Object.entries(data).map(([key, value]) => (
                <Box key={key} sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant={isMobile ? "caption" : "body2"}>{key}:</Typography>
                  <Typography variant={isMobile ? "caption" : "body2"} fontWeight="bold">
                    {String(value)}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Box>
        );
        break;

      case 'pipeline-status':
        setWidgetContent(
          <Box>
            <Typography variant={isMobile ? "body2" : "body1"}>Pipeline Status</Typography>
            <Box sx={{ mt: isMobile ? 1 : 2 }}>
              {Array.isArray(data) && data.map((pipeline, index) => (
                <Box key={index} sx={{ mb: isMobile ? 1 : 2 }}>
                  <Box sx={{ 
                    display: 'flex', 
                    justifyContent: 'space-between',
                    flexDirection: isMobile && pipeline.name?.length > 15 ? 'column' : 'row'
                  }}>
                    <Typography 
                      variant={isMobile ? "caption" : "body2"} 
                      fontWeight="bold"
                      sx={{ mr: 1 }}
                    >
                      {pipeline.name || `Pipeline ${index + 1}`}
                    </Typography>
                    <Typography
                      variant={isMobile ? "caption" : "body2"}
                      sx={{
                        color:
                          pipeline.status === 'success'
                            ? 'success.main'
                            : pipeline.status === 'running'
                            ? 'info.main'
                            : pipeline.status === 'failed'
                            ? 'error.main'
                            : 'text.secondary',
                      }}
                    >
                      {pipeline.status}
                    </Typography>
                  </Box>
                  {index < data.length - 1 && <Divider sx={{ my: isMobile ? 0.5 : 1 }} />}
                </Box>
              ))}
            </Box>
          </Box>
        );
        break;

      case 'error-classification':
        setWidgetContent(
          <Box>
            <Typography variant={isMobile ? "body2" : "body1"}>Error Classification</Typography>
            <Box sx={{ mt: isMobile ? 1 : 2 }}>
              {Array.isArray(data) && data.map((category, index) => (
                <Box key={index} sx={{ mb: isMobile ? 0.5 : 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant={isMobile ? "caption" : "body2"}>
                      {category.name || `Category ${index + 1}`}:
                    </Typography>
                    <Typography variant={isMobile ? "caption" : "body2"} fontWeight="bold">
                      {category.count || 0}
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      mt: 0.5,
                      height: isMobile ? 6 : 8,
                      width: '100%',
                      bgcolor: 'grey.200',
                      borderRadius: 1,
                      overflow: 'hidden',
                    }}
                  >
                    <Box
                      sx={{
                        height: '100%',
                        width: `${category.percentage || 0}%`,
                        bgcolor: category.color || 'primary.main',
                      }}
                    />
                  </Box>
                </Box>
              ))}
            </Box>
          </Box>
        );
        break;

      case 'ml-classification':
        setWidgetContent(
          <Box>
            <Typography variant={isMobile ? "body2" : "body1"}>ML Error Classification</Typography>
            <Box sx={{ mt: isMobile ? 1 : 2 }}>
              {data && typeof data === 'object' && (
                <>
                  <Box sx={{ mb: isMobile ? 1 : 2 }}>
                    <Typography variant={isMobile ? "caption" : "body2"} fontWeight="bold">
                      Classification Summary
                    </Typography>
                    <Typography variant={isMobile ? "caption" : "body2"}>
                      Total errors analyzed: {data.totalErrors || 0}
                    </Typography>
                    <Typography variant={isMobile ? "caption" : "body2"}>
                      Classification accuracy: {data.accuracy || 0}%
                    </Typography>
                  </Box>
                  {Array.isArray(data.categories) && data.categories.map((category: any, index: number) => (
                    <Box key={index} sx={{ mb: isMobile ? 0.5 : 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant={isMobile ? "caption" : "body2"}>
                          {category.name || `Category ${index + 1}`}:
                        </Typography>
                        <Typography variant={isMobile ? "caption" : "body2"} fontWeight="bold">
                          {category.count || 0}
                        </Typography>
                      </Box>
                    </Box>
                  ))}
                </>
              )}
            </Box>
          </Box>
        );
        break;
        
      case 'architecture-diagram':
        // Lazy load the ArchitectureDiagram component
        const ArchitectureDiagram = lazy(() => import('../visualizations/ArchitectureDiagram'));
        
        setWidgetContent(
          <Suspense fallback={
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
              <CircularProgress size={isMobile ? 30 : 40} />
            </Box>
          }>
            <ArchitectureDiagram 
              data={data || { diagrams: [] }}
              isLoading={false}
              height="100%"
              width="100%"
            />
          </Suspense>
        );
        break;

      case 'security-vulnerabilities':
        setWidgetContent(
          <Box>
            <Typography variant={isMobile ? "body2" : "body1"}>Security Vulnerabilities</Typography>
            <Box sx={{ mt: isMobile ? 1 : 2 }}>
              {Array.isArray(data) && data.map((vuln, index) => (
                <Box key={index} sx={{ mb: isMobile ? 1 : 2 }}>
                  <Typography 
                    variant={isMobile ? "caption" : "body2"} 
                    fontWeight="bold" 
                    color="error"
                    sx={{ 
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      maxWidth: '100%'
                    }}
                  >
                    {vuln.name || `Vulnerability ${index + 1}`}
                  </Typography>
                  <Typography variant={isMobile ? "caption" : "body2"}>
                    Severity: {vuln.severity || 'Unknown'}
                  </Typography>
                  <Typography 
                    variant={isMobile ? "caption" : "body2"} 
                    noWrap
                    sx={{ 
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      maxWidth: '100%'
                    }}
                  >
                    {vuln.description || 'No description available'}
                  </Typography>
                  {index < data.length - 1 && <Divider sx={{ my: isMobile ? 0.5 : 1 }} />}
                </Box>
              ))}
            </Box>
          </Box>
        );
        break;

      default:
        setWidgetContent(
          <Box sx={{ p: isMobile ? 1 : 2 }}>
            <Typography variant={isMobile ? "body2" : "body1"}>
              Widget type "{widget.type}" not implemented yet
            </Typography>
          </Box>
        );
    }
  }, [widget.type, data, isLoading, isMobile]);

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        ...(isEditMode && {
          outline: '1px dashed',
          outlineColor: 'grey.400',
        }),
      }}
    >
      <CardHeader
        title={widget.title}
        titleTypographyProps={{ 
          variant: isMobile ? 'subtitle1' : 'h6',
          noWrap: true,
          sx: { 
            overflow: 'hidden', 
            textOverflow: 'ellipsis',
            width: isMobile ? '80%' : '100%'
          }
        }}
        action={
          <>
            <IconButton
              aria-label="widget menu"
              aria-controls="widget-menu"
              aria-haspopup="true"
              onClick={handleMenuOpen}
              size="small"
            >
              <MoreIcon />
            </IconButton>
            <Menu
              id="widget-menu"
              anchorEl={anchorEl}
              keepMounted
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
              PaperProps={{
                sx: {
                  maxHeight: isMobile ? '70vh' : 'auto',
                  width: isMobile ? '200px' : 'auto',
                }
              }}
            >
              <MenuItem onClick={handleRefresh}>
                <RefreshIcon fontSize="small" sx={{ mr: 1 }} />
                Refresh
              </MenuItem>
              {isEditMode && (
                <>
                  <MenuItem onClick={handleEdit}>
                    <EditIcon fontSize="small" sx={{ mr: 1 }} />
                    Edit
                  </MenuItem>
                  <MenuItem onClick={handleSettings}>
                    <SettingsIcon fontSize="small" sx={{ mr: 1 }} />
                    Settings
                  </MenuItem>
                  <MenuItem onClick={handleDuplicate}>
                    <DuplicateIcon fontSize="small" sx={{ mr: 1 }} />
                    Duplicate
                  </MenuItem>
                  <MenuItem onClick={handleDelete}>
                    <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
                    Delete
                  </MenuItem>
                </>
              )}
            </Menu>
          </>
        }
        sx={{
          p: isMobile ? 1.5 : 2,
        }}
      />
      <CardContent 
        sx={{ 
          flexGrow: 1, 
          overflow: 'auto',
          p: isMobile ? 1.5 : 2,
          '&:last-child': {
            pb: isMobile ? 1.5 : 2,
          }
        }}
      >
        {widgetContent}
      </CardContent>
    </Card>
  );
};

export default DashboardWidget;
