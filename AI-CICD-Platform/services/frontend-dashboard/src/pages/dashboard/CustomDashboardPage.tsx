import React, { useEffect, useState } from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  Card, 
  CardContent, 
  CardMedia, 
  Grid, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions,
  TextField,
  Divider,
  Chip,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Add as AddIcon,
  ContentCopy as DuplicateIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Download as ExportIcon,
  Upload as ImportIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import { useDashboardStore, DashboardConfig } from '../../stores/dashboard.store';

const CustomDashboardPage: React.FC = () => {
  const { 
    dashboards, 
    templates, 
    activeDashboardId, 
    setActiveDashboard,
    addDashboard,
    duplicateDashboard,
    deleteDashboard,
    createFromTemplate,
    importDashboard,
    exportDashboard,
    loadTemplatesFromServer
  } = useDashboardStore();
  
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [newDashboardName, setNewDashboardName] = useState('');
  const [newDashboardDescription, setNewDashboardDescription] = useState('');
  const [importJson, setImportJson] = useState('');
  const [importError, setImportError] = useState('');
  
  // Load templates on initial render
  useEffect(() => {
    loadTemplatesFromServer();
  }, [loadTemplatesFromServer]);
  
  const handleCreateDashboard = () => {
    if (newDashboardName.trim()) {
      const id = addDashboard({
        name: newDashboardName,
        description: newDashboardDescription,
        layout: {
          cols: 12,
          rowHeight: 50,
          containerPadding: [10, 10],
          margin: [10, 10],
        },
        widgets: [],
      });
      setActiveDashboard(id);
      setCreateDialogOpen(false);
      setNewDashboardName('');
      setNewDashboardDescription('');
    }
  };
  
  const handleCreateFromTemplate = (templateId: string) => {
    const id = createFromTemplate(templateId);
    if (id) {
      setActiveDashboard(id);
    }
  };
  
  const handleDuplicateDashboard = (dashboardId: string) => {
    const id = duplicateDashboard(dashboardId);
    setActiveDashboard(id);
  };
  
  const handleDeleteDashboard = (dashboardId: string) => {
    if (dashboards.length > 1) {
      deleteDashboard(dashboardId);
    }
  };
  
  const handleExportDashboard = (dashboardId: string) => {
    const dashboard = exportDashboard(dashboardId);
    if (dashboard) {
      // Create a downloadable JSON file
      const dataStr = JSON.stringify(dashboard, null, 2);
      const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
      
      const exportFileDefaultName = `dashboard-${dashboard.name.toLowerCase().replace(/\s+/g, '-')}.json`;
      
      const linkElement = document.createElement('a');
      linkElement.setAttribute('href', dataUri);
      linkElement.setAttribute('download', exportFileDefaultName);
      linkElement.click();
    }
  };
  
  const handleImportDashboard = () => {
    try {
      setImportError('');
      const dashboardData = JSON.parse(importJson);
      
      // Validate required fields
      if (!dashboardData.name || !dashboardData.layout || !Array.isArray(dashboardData.widgets)) {
        setImportError('Invalid dashboard format. Missing required fields.');
        return;
      }
      
      const id = importDashboard(dashboardData);
      setActiveDashboard(id);
      setImportDialogOpen(false);
      setImportJson('');
    } catch (error) {
      setImportError('Invalid JSON format. Please check your input.');
    }
  };
  
  return (
    <Box sx={{ p: 3, height: 'calc(100vh - 64px)' }}>
      {activeDashboardId ? (
        <DashboardLayout />
      ) : (
        <Typography variant="h5" sx={{ mb: 3 }}>
          No dashboard selected. Please select or create a dashboard.
        </Typography>
      )}
      
      {/* Dashboard Selection Section */}
      <Box sx={{ mt: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5">Your Dashboards</Typography>
          <Box>
            <Button 
              variant="outlined" 
              startIcon={<AddIcon />} 
              onClick={() => setCreateDialogOpen(true)}
              sx={{ mr: 1 }}
            >
              Create New
            </Button>
            <Button 
              variant="outlined" 
              startIcon={<ImportIcon />} 
              onClick={() => setImportDialogOpen(true)}
            >
              Import
            </Button>
          </Box>
        </Box>
        
        <Grid container spacing={2}>
          {dashboards.map((dashboard) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={dashboard.id}>
              <Card 
                sx={{ 
                  cursor: 'pointer',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  ...(dashboard.id === activeDashboardId && {
                    outline: '2px solid',
                    outlineColor: 'primary.main',
                  }),
                }}
                onClick={() => setActiveDashboard(dashboard.id)}
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Typography variant="h6" component="div">
                      {dashboard.name}
                    </Typography>
                    <Box>
                      {!dashboard.isDefault && (
                        <Tooltip title="Delete">
                          <IconButton 
                            size="small" 
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteDashboard(dashboard.id);
                            }}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                      <Tooltip title="Duplicate">
                        <IconButton 
                          size="small" 
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDuplicateDashboard(dashboard.id);
                          }}
                        >
                          <DuplicateIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Export">
                        <IconButton 
                          size="small" 
                          onClick={(e) => {
                            e.stopPropagation();
                            handleExportDashboard(dashboard.id);
                          }}
                        >
                          <ExportIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    {dashboard.description || 'No description'}
                  </Typography>
                  <Typography variant="caption" display="block" sx={{ mt: 2 }}>
                    {dashboard.widgets.length} widgets
                  </Typography>
                  <Box sx={{ mt: 1 }}>
                    {dashboard.isDefault && (
                      <Chip label="Default" size="small" color="primary" sx={{ mr: 0.5 }} />
                    )}
                    {dashboard.tags?.map((tag) => (
                      <Chip key={tag} label={tag} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
      
      {/* Templates Section */}
      <Box sx={{ mt: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5">Dashboard Templates</Typography>
          <Button 
            variant="text" 
            startIcon={<RefreshIcon />} 
            onClick={() => loadTemplatesFromServer()}
          >
            Refresh Templates
          </Button>
        </Box>
        
        <Grid container spacing={2}>
          {templates.map((template) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={template.id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" component="div">
                    {template.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    {template.description || 'No description'}
                  </Typography>
                  <Typography variant="caption" display="block" sx={{ mt: 2 }}>
                    {template.widgets.length} widgets
                  </Typography>
                  <Box sx={{ mt: 1 }}>
                    {template.category && (
                      <Chip 
                        label={template.category} 
                        size="small" 
                        color="secondary" 
                        sx={{ mr: 0.5 }} 
                      />
                    )}
                    {template.tags?.map((tag) => (
                      <Chip key={tag} label={tag} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                    ))}
                  </Box>
                </CardContent>
                <Divider />
                <Box sx={{ p: 1, display: 'flex', justifyContent: 'flex-end' }}>
                  <Button 
                    size="small" 
                    onClick={() => handleCreateFromTemplate(template.id)}
                  >
                    Use Template
                  </Button>
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
      
      {/* Create Dashboard Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Dashboard</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Dashboard Name"
            type="text"
            fullWidth
            value={newDashboardName}
            onChange={(e) => setNewDashboardName(e.target.value)}
          />
          <TextField
            margin="dense"
            label="Description (optional)"
            type="text"
            fullWidth
            multiline
            rows={3}
            value={newDashboardDescription}
            onChange={(e) => setNewDashboardDescription(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateDashboard} 
            variant="contained"
            disabled={!newDashboardName.trim()}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Import Dashboard Dialog */}
      <Dialog open={importDialogOpen} onClose={() => setImportDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Import Dashboard</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Paste the dashboard JSON configuration below:
          </Typography>
          <TextField
            autoFocus
            margin="dense"
            type="text"
            fullWidth
            multiline
            rows={10}
            value={importJson}
            onChange={(e) => setImportJson(e.target.value)}
            error={!!importError}
            helperText={importError}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImportDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleImportDashboard} 
            variant="contained"
            disabled={!importJson.trim()}
          >
            Import
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CustomDashboardPage;
