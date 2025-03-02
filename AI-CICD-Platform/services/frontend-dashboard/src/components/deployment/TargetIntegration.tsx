import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Button, 
  Card, 
  CardContent, 
  Typography, 
  Chip, 
  Grid, 
  IconButton, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Paper,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Switch,
  FormControlLabel
} from '@mui/material';
import { 
  Add as AddIcon, 
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  CloudUpload as CloudUploadIcon,
  Storage as DatabaseIcon,
  Cloud as CloudIcon,
  Code as CodeIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { useWebSocketEvent } from '../../hooks/useWebSocket';

// Types
interface DeploymentTarget {
  id: string;
  name: string;
  type: string;
  provider: string;
  config: any;
  status: string;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
}

interface TargetCredential {
  id: string;
  name: string;
  type: string;
  provider: string;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
}

// Mock data for development
const mockTargets: DeploymentTarget[] = [
  {
    id: '1',
    name: 'Production Kubernetes Cluster',
    type: 'kubernetes',
    provider: 'aws',
    config: {
      cluster: 'prod-cluster',
      namespace: 'default',
      region: 'us-west-2'
    },
    status: 'active',
    createdAt: '2025-03-01T12:00:00Z',
    updatedAt: '2025-03-01T12:00:00Z',
    createdBy: 'user1'
  },
  {
    id: '2',
    name: 'Staging Kubernetes Cluster',
    type: 'kubernetes',
    provider: 'aws',
    config: {
      cluster: 'staging-cluster',
      namespace: 'default',
      region: 'us-west-2'
    },
    status: 'active',
    createdAt: '2025-03-01T12:00:00Z',
    updatedAt: '2025-03-01T12:00:00Z',
    createdBy: 'user1'
  },
  {
    id: '3',
    name: 'Development Kubernetes Cluster',
    type: 'kubernetes',
    provider: 'aws',
    config: {
      cluster: 'dev-cluster',
      namespace: 'default',
      region: 'us-west-2'
    },
    status: 'active',
    createdAt: '2025-03-01T12:00:00Z',
    updatedAt: '2025-03-01T12:00:00Z',
    createdBy: 'user1'
  },
  {
    id: '4',
    name: 'Production Azure App Service',
    type: 'app_service',
    provider: 'azure',
    config: {
      resource_group: 'prod-rg',
      app_name: 'prod-app',
      region: 'eastus'
    },
    status: 'active',
    createdAt: '2025-03-01T12:00:00Z',
    updatedAt: '2025-03-01T12:00:00Z',
    createdBy: 'user1'
  },
  {
    id: '5',
    name: 'Production GCP App Engine',
    type: 'app_engine',
    provider: 'gcp',
    config: {
      project: 'prod-project',
      service: 'default',
      region: 'us-central1'
    },
    status: 'active',
    createdAt: '2025-03-01T12:00:00Z',
    updatedAt: '2025-03-01T12:00:00Z',
    createdBy: 'user1'
  }
];

const mockCredentials: TargetCredential[] = [
  {
    id: '1',
    name: 'AWS Production Credentials',
    type: 'aws',
    provider: 'aws',
    createdAt: '2025-03-01T12:00:00Z',
    updatedAt: '2025-03-01T12:00:00Z',
    createdBy: 'user1'
  },
  {
    id: '2',
    name: 'Azure Production Credentials',
    type: 'azure',
    provider: 'azure',
    createdAt: '2025-03-01T12:00:00Z',
    updatedAt: '2025-03-01T12:00:00Z',
    createdBy: 'user1'
  },
  {
    id: '3',
    name: 'GCP Production Credentials',
    type: 'gcp',
    provider: 'gcp',
    createdAt: '2025-03-01T12:00:00Z',
    updatedAt: '2025-03-01T12:00:00Z',
    createdBy: 'user1'
  }
];

// Component
const TargetIntegration: React.FC = () => {
  const theme = useTheme();
  const { data: lastMessage } = useWebSocketEvent('target_update');
  
  const [targets, setTargets] = useState<DeploymentTarget[]>(mockTargets);
  const [credentials, setCredentials] = useState<TargetCredential[]>(mockCredentials);
  const [selectedTarget, setSelectedTarget] = useState<DeploymentTarget | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [filterProvider, setFilterProvider] = useState<string>('');
  const [filterType, setFilterType] = useState<string>('');
  
  // Dialog states
  const [createTargetDialogOpen, setCreateTargetDialogOpen] = useState<boolean>(false);
  const [editTargetDialogOpen, setEditTargetDialogOpen] = useState<boolean>(false);
  const [deleteTargetDialogOpen, setDeleteTargetDialogOpen] = useState<boolean>(false);
  const [createCredentialDialogOpen, setCreateCredentialDialogOpen] = useState<boolean>(false);
  
  // Form states
  const [newTarget, setNewTarget] = useState<Partial<DeploymentTarget>>({
    name: '',
    type: '',
    provider: '',
    config: {}
  });
  
  const [newCredential, setNewCredential] = useState<Partial<TargetCredential>>({
    name: '',
    type: '',
    provider: ''
  });
  
  // Effect to handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      try {
        if (typeof lastMessage === 'object') {
          // Handle target updates
          if (lastMessage.type === 'target_update' && lastMessage.target) {
            setTargets(prevTargets => {
              const index = prevTargets.findIndex(t => t.id === lastMessage.target.id);
              if (index >= 0) {
                const updatedTargets = [...prevTargets];
                updatedTargets[index] = lastMessage.target;
                return updatedTargets;
              }
              return [...prevTargets, lastMessage.target];
            });
          } 
          // Handle credential updates
          else if (lastMessage.type === 'credential_update' && lastMessage.credential) {
            setCredentials(prevCredentials => {
              const index = prevCredentials.findIndex(c => c.id === lastMessage.credential.id);
              if (index >= 0) {
                const updatedCredentials = [...prevCredentials];
                updatedCredentials[index] = lastMessage.credential;
                return updatedCredentials;
              }
              return [...prevCredentials, lastMessage.credential];
            });
          }
        }
      } catch (error) {
        console.error('Error handling WebSocket message:', error);
      }
    }
  }, [lastMessage]);
  
  // Fetch targets
  const fetchTargets = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would fetch from the API
      // const response = await fetch('/api/deployment-automation/targets');
      // const data = await response.json();
      // setTargets(data);
      
      // For now, filter mock data
      const filteredTargets = mockTargets.filter(t => 
        (filterProvider ? t.provider === filterProvider : true) &&
        (filterType ? t.type === filterType : true)
      );
      setTargets(filteredTargets);
    } catch (error) {
      console.error('Error fetching targets:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Fetch credentials
  const fetchCredentials = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would fetch from the API
      // const response = await fetch('/api/deployment-automation/credentials');
      // const data = await response.json();
      // setCredentials(data);
      
      // For now, use mock data
      setCredentials(mockCredentials);
    } catch (error) {
      console.error('Error fetching credentials:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Effect to fetch data when filters change
  useEffect(() => {
    fetchTargets();
  }, [filterProvider, filterType]);
  
  // Create a new target
  const createTarget = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would send to the API
      // const response = await fetch('/api/deployment-automation/targets', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(newTarget)
      // });
      // const data = await response.json();
      // setTargets([...targets, data]);
      
      // For now, use mock data
      const newId = (targets.length + 1).toString();
      const createdTarget: DeploymentTarget = {
        id: newId,
        name: newTarget.name || 'New Target',
        type: newTarget.type || 'kubernetes',
        provider: newTarget.provider || 'aws',
        config: newTarget.config || {},
        status: 'active',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        createdBy: 'user1'
      };
      setTargets([...targets, createdTarget]);
      
      // Reset form
      setNewTarget({
        name: '',
        type: '',
        provider: '',
        config: {}
      });
      
      // Close dialog
      setCreateTargetDialogOpen(false);
    } catch (error) {
      console.error('Error creating target:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Update a target
  const updateTarget = async () => {
    if (!selectedTarget) return;
    
    setLoading(true);
    try {
      // In a real implementation, this would send to the API
      // const response = await fetch(`/api/deployment-automation/targets/${selectedTarget.id}`, {
      //   method: 'PUT',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(selectedTarget)
      // });
      // const data = await response.json();
      // setTargets(prevTargets => {
      //   const index = prevTargets.findIndex(t => t.id === selectedTarget.id);
      //   if (index >= 0) {
      //     const updatedTargets = [...prevTargets];
      //     updatedTargets[index] = data;
      //     return updatedTargets;
      //   }
      //   return prevTargets;
      // });
      
      // For now, use mock data
      setTargets(prevTargets => {
        const index = prevTargets.findIndex(t => t.id === selectedTarget.id);
        if (index >= 0) {
          const updatedTargets = [...prevTargets];
          updatedTargets[index] = {
            ...selectedTarget,
            updatedAt: new Date().toISOString()
          };
          return updatedTargets;
        }
        return prevTargets;
      });
      
      // Close dialog
      setEditTargetDialogOpen(false);
    } catch (error) {
      console.error('Error updating target:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Delete a target
  const deleteTarget = async () => {
    if (!selectedTarget) return;
    
    setLoading(true);
    try {
      // In a real implementation, this would send to the API
      // const response = await fetch(`/api/deployment-automation/targets/${selectedTarget.id}`, {
      //   method: 'DELETE'
      // });
      
      // For now, use mock data
      setTargets(prevTargets => prevTargets.filter(t => t.id !== selectedTarget.id));
      
      // Close dialog
      setDeleteTargetDialogOpen(false);
    } catch (error) {
      console.error('Error deleting target:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Create a new credential
  const createCredential = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would send to the API
      // const response = await fetch('/api/deployment-automation/credentials', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(newCredential)
      // });
      // const data = await response.json();
      // setCredentials([...credentials, data]);
      
      // For now, use mock data
      const newId = (credentials.length + 1).toString();
      const createdCredential: TargetCredential = {
        id: newId,
        name: newCredential.name || 'New Credential',
        type: newCredential.type || 'aws',
        provider: newCredential.provider || 'aws',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        createdBy: 'user1'
      };
      setCredentials([...credentials, createdCredential]);
      
      // Reset form
      setNewCredential({
        name: '',
        type: '',
        provider: ''
      });
      
      // Close dialog
      setCreateCredentialDialogOpen(false);
    } catch (error) {
      console.error('Error creating credential:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Get provider icon
  const getProviderIcon = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'aws':
        return <CloudIcon sx={{ color: '#FF9900' }} />;
      case 'azure':
        return <CloudIcon sx={{ color: '#0078D4' }} />;
      case 'gcp':
        return <CloudIcon sx={{ color: '#4285F4' }} />;
      case 'kubernetes':
        return <CloudIcon sx={{ color: '#326CE5' }} />;
      default:
        return <CloudIcon />;
    }
  };
  
  // Get type icon
  const getTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'kubernetes':
        return <CloudIcon />;
      case 'app_service':
        return <CloudUploadIcon />;
      case 'app_engine':
        return <CloudUploadIcon />;
      case 'database':
        return <DatabaseIcon />;
      case 'serverless':
        return <CodeIcon />;
      default:
        return <SettingsIcon />;
    }
  };
  
  // Format date
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString();
  };
  
  // Render target card
  const renderTargetCard = (target: DeploymentTarget) => {
    const isSelected = selectedTarget?.id === target.id;
    
    return (
      <Card 
        key={target.id} 
        sx={{ 
          mb: 2, 
          cursor: 'pointer',
          border: isSelected ? `2px solid ${theme.palette.primary.main}` : 'none'
        }}
        onClick={() => setSelectedTarget(target)}
      >
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Box display="flex" alignItems="center">
              {getTypeIcon(target.type)}
              <Typography variant="h6" sx={{ ml: 1 }}>{target.name}</Typography>
            </Box>
            <Chip 
              icon={getProviderIcon(target.provider)}
              label={target.provider.toUpperCase()} 
              size="small" 
              color="primary"
            />
          </Box>
          
          <Typography variant="body2" color="text.secondary" mb={2}>
            Type: {target.type.replace('_', ' ')} • Status: {target.status}
          </Typography>
          
          <Box display="flex" justifyContent="flex-end">
            <IconButton 
              size="small" 
              color="primary"
              onClick={(e) => {
                e.stopPropagation();
                setSelectedTarget(target);
                setEditTargetDialogOpen(true);
              }}
            >
              <EditIcon />
            </IconButton>
            <IconButton 
              size="small" 
              color="error"
              onClick={(e) => {
                e.stopPropagation();
                setSelectedTarget(target);
                setDeleteTargetDialogOpen(true);
              }}
            >
              <DeleteIcon />
            </IconButton>
          </Box>
        </CardContent>
      </Card>
    );
  };
  
  // Render credential card
  const renderCredentialCard = (credential: TargetCredential) => {
    return (
      <Card key={credential.id} sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="h6">{credential.name}</Typography>
            <Chip 
              icon={getProviderIcon(credential.provider)}
              label={credential.provider.toUpperCase()} 
              size="small" 
              color="primary"
            />
          </Box>
          
          <Typography variant="body2" color="text.secondary" mb={2}>
            Type: {credential.type} • Created: {formatDate(credential.createdAt)}
          </Typography>
        </CardContent>
      </Card>
    );
  };
  
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Deployment Targets</Typography>
        <Box>
          <Button 
            variant="outlined" 
            startIcon={<AddIcon />}
            onClick={() => setCreateCredentialDialogOpen(true)}
            sx={{ mr: 2 }}
          >
            Add Credential
          </Button>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
            onClick={() => setCreateTargetDialogOpen(true)}
          >
            Add Target
          </Button>
        </Box>
      </Box>
      
      <Box display="flex" justifyContent="flex-start" alignItems="center" mb={3}>
        <FormControl sx={{ minWidth: 150, mr: 2 }}>
          <InputLabel>Provider</InputLabel>
          <Select
            value={filterProvider}
            label="Provider"
            onChange={(e) => setFilterProvider(e.target.value)}
            size="small"
          >
            <MenuItem value="">All Providers</MenuItem>
            <MenuItem value="aws">AWS</MenuItem>
            <MenuItem value="azure">Azure</MenuItem>
            <MenuItem value="gcp">GCP</MenuItem>
          </Select>
        </FormControl>
        
        <FormControl sx={{ minWidth: 150, mr: 2 }}>
          <InputLabel>Type</InputLabel>
          <Select
            value={filterType}
            label="Type"
            onChange={(e) => setFilterType(e.target.value)}
            size="small"
          >
            <MenuItem value="">All Types</MenuItem>
            <MenuItem value="kubernetes">Kubernetes</MenuItem>
            <MenuItem value="app_service">App Service</MenuItem>
            <MenuItem value="app_engine">App Engine</MenuItem>
          </Select>
        </FormControl>
        
        <Button 
          variant="outlined" 
          startIcon={<RefreshIcon />}
          onClick={() => {
            fetchTargets();
            fetchCredentials();
          }}
        >
          Refresh
        </Button>
      </Box>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Typography variant="h6" mb={2}>Deployment Targets</Typography>
          {loading ? (
            <Box display="flex" justifyContent="center" my={4}>
              <CircularProgress />
            </Box>
          ) : targets.length > 0 ? (
            targets.map(renderTargetCard)
          ) : (
            <Typography variant="body1" color="text.secondary" align="center" my={4}>
              No deployment targets found.
            </Typography>
          )}
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Typography variant="h6" mb={2}>Credentials</Typography>
          {loading ? (
            <Box display="flex" justifyContent="center" my={4}>
              <CircularProgress />
            </Box>
          ) : credentials.length > 0 ? (
            credentials.map(renderCredentialCard)
          ) : (
            <Typography variant="body1" color="text.secondary" align="center" my={4}>
              No credentials found.
            </Typography>
          )}
        </Grid>
      </Grid>
      
      {/* Create Target Dialog */}
      <Dialog open={createTargetDialogOpen} onClose={() => setCreateTargetDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add Deployment Target</DialogTitle>
        <DialogContent>
          <Box mt={2}>
            <TextField
              label="Target Name"
              fullWidth
              margin="normal"
              value={newTarget.name}
              onChange={(e) => setNewTarget({...newTarget, name: e.target.value})}
            />
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Provider</InputLabel>
              <Select
                value={newTarget.provider || ''}
                label="Provider"
                onChange={(e) => setNewTarget({...newTarget, provider: e.target.value})}
              >
                <MenuItem value="aws">AWS</MenuItem>
                <MenuItem value="azure">Azure</MenuItem>
                <MenuItem value="gcp">GCP</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Type</InputLabel>
              <Select
                value={newTarget.type || ''}
                label="Type"
                onChange={(e) => setNewTarget({...newTarget, type: e.target.value})}
              >
                <MenuItem value="kubernetes">Kubernetes</MenuItem>
                <MenuItem value="app_service">App Service</MenuItem>
                <MenuItem value="app_engine">App Engine</MenuItem>
              </Select>
            </FormControl>
            
            <Typography variant="subtitle1" mt={3} mb={1}>
              Configuration
            </Typography>
            
            {newTarget.type === 'kubernetes' && (
              <>
                <TextField
                  label="Cluster Name"
                  fullWidth
                  margin="normal"
                  value={newTarget.config?.cluster || ''}
                  onChange={(e) => setNewTarget({
                    ...newTarget, 
                    config: {...newTarget.config, cluster: e.target.value}
                  })}
                />
                
                <TextField
                  label="Namespace"
                  fullWidth
                  margin="normal"
                  value={newTarget.config?.namespace || ''}
                  onChange={(e) => setNewTarget({
                    ...newTarget, 
                    config: {...newTarget.config, namespace: e.target.value}
                  })}
                />
                
                <TextField
                  label="Region"
                  fullWidth
                  margin="normal"
                  value={newTarget.config?.region || ''}
                  onChange={(e) => setNewTarget({
                    ...newTarget, 
                    config: {...newTarget.config, region: e.target.value}
                  })}
                />
              </>
            )}
            
            {newTarget.type === 'app_service' && (
              <>
                <TextField
                  label="Resource Group"
                  fullWidth
                  margin="normal"
                  value={newTarget.config?.resource_group || ''}
                  onChange={(e) => setNewTarget({
                    ...newTarget, 
                    config: {...newTarget.config, resource_group: e.target.value}
                  })}
                />
                
                <TextField
                  label="App Name"
                  fullWidth
                  margin="normal"
                  value={newTarget.config?.app_name || ''}
                  onChange={(e) => setNewTarget({
                    ...newTarget, 
                    config: {...newTarget.config, app_name: e.target.value}
                  })}
                />
                
                <TextField
                  label="Region"
                  fullWidth
                  margin="normal"
                  value={newTarget.config?.region || ''}
                  onChange={(e) => setNewTarget({
                    ...newTarget, 
                    config: {...newTarget.config, region: e.target.value}
                  })}
                />
              </>
            )}
            
            {newTarget.type === 'app_engine' && (
              <>
                <TextField
                  label="Project"
                  fullWidth
                  margin="normal"
                  value={newTarget.config?.project || ''}
                  onChange={(e) => setNewTarget({
                    ...newTarget, 
                    config: {...newTarget.config, project: e.target.value}
                  })}
                />
                
                <TextField
                  label="Service"
                  fullWidth
                  margin="normal"
                  value={newTarget.config?.service || ''}
                  onChange={(e) => setNewTarget({
                    ...newTarget, 
                    config: {...newTarget.config, service: e.target.value}
                  })}
                />
                
                <TextField
                  label="Region"
                  fullWidth
                  margin="normal"
                  value={newTarget.config?.region || ''}
                  onChange={(e) => setNewTarget({
                    ...newTarget, 
                    config: {...newTarget.config, region: e.target.value}
                  })}
                />
              </>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateTargetDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={createTarget}
            disabled={!newTarget.name || !newTarget.type || !newTarget.provider}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Edit Target Dialog */}
      <Dialog open={editTargetDialogOpen} onClose={() => setEditTargetDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Deployment Target</DialogTitle>
        <DialogContent>
          {selectedTarget && (
            <Box mt={2}>
              <TextField
                label="Target Name"
                fullWidth
                margin="normal"
                value={selectedTarget.name}
                onChange={(e) => setSelectedTarget({...selectedTarget, name: e.target.value})}
              />
              
              <FormControl fullWidth margin="normal">
                <InputLabel>Status</InputLabel>
                <Select
                  value={selectedTarget.status}
                  label="Status"
                  onChange={(e) => setSelectedTarget({...selectedTarget, status: e.target.value})}
                >
                  <MenuItem value="active">Active</MenuItem>
                  <MenuItem value="inactive">Inactive</MenuItem>
                </Select>
              </FormControl>
              
              <Typography variant="subtitle1" mt={3} mb={1}>
                Configuration
              </Typography>
              
              {selectedTarget.type === 'kubernetes' && (
                <>
                  <TextField
                    label="Cluster Name"
                    fullWidth
                    margin="normal"
                    value={selectedTarget.config?.cluster || ''}
                    onChange={(e) => setSelectedTarget({
                      ...selectedTarget, 
                      config: {...selectedTarget.config, cluster: e.target.value}
                    })}
                  />
                  
                  <TextField
                    label="Namespace"
                    fullWidth
                    margin="normal"
                    value={selectedTarget.config?.namespace || ''}
                    onChange={(e) => setSelectedTarget({
                      ...selectedTarget, 
                      config: {...selectedTarget.config, namespace: e.target.value}
                    })}
                  />
                  
                  <TextField
                    label="Region"
                    fullWidth
                    margin="normal"
                    value={selectedTarget.config?.region || ''}
                    onChange={(e) => setSelectedTarget({
                      ...selectedTarget, 
                      config: {...selectedTarget.config, region: e.target.value}
                    })}
                  />
                </>
              )}
              
              {selectedTarget.type === 'app_service' && (
                <>
                  <TextField
                    label="Resource Group"
                    fullWidth
                    margin="normal"
                    value={selectedTarget.config?.resource_group || ''}
                    onChange={(e) => setSelectedTarget({
                      ...selectedTarget, 
                      config: {...selectedTarget.config, resource_group: e.target.value}
                    })}
                  />
                  
                  <TextField
                    label="App Name"
                    fullWidth
                    margin="normal"
                    value={selectedTarget.config?.app_name || ''}
                    onChange={(e) => setSelectedTarget({
                      ...selectedTarget, 
                      config: {...selectedTarget.config, app_name: e.target.value}
                    })}
                  />
                  
                  <TextField
                    label="Region"
                    fullWidth
                    margin="normal"
                    value={selectedTarget.config?.region || ''}
                    onChange={(e) => setSelectedTarget({
                      ...selectedTarget, 
                      config: {...selectedTarget.config, region: e.target.value}
                    })}
                  />
                </>
              )}
              
              {selectedTarget.type === 'app_engine' && (
                <>
                  <TextField
                    label="Project"
                    fullWidth
                    margin="normal"
                    value={selectedTarget.config?.project || ''}
                    onChange={(e) => setSelectedTarget({
                      ...selectedTarget, 
                      config: {...selectedTarget.config, project: e.target.value}
                    })}
                  />
                  
                  <TextField
                    label="Service"
                    fullWidth
                    margin="normal"
                    value={selectedTarget.config?.service || ''}
                    onChange={(e) => setSelectedTarget({
                      ...selectedTarget, 
                      config: {...selectedTarget.config, service: e.target.value}
                    })}
                  />
                  
                  <TextField
                    label="Region"
                    fullWidth
                    margin="normal"
                    value={selectedTarget.config?.region || ''}
                    onChange={(e) => setSelectedTarget({
                      ...selectedTarget, 
                      config: {...selectedTarget.config, region: e.target.value}
                    })}
                  />
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditTargetDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={updateTarget}
            disabled={!selectedTarget?.name}
          >
            Update
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Delete Target Dialog */}
      <Dialog open={deleteTargetDialogOpen} onClose={() => setDeleteTargetDialogOpen(false)}>
        <DialogTitle>Delete Deployment Target</DialogTitle>
        <DialogContent>
          <Box mt={2}>
            <Typography variant="body1">
              Are you sure you want to delete the target "{selectedTarget?.name}"?
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTargetDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            color="error"
            onClick={deleteTarget}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Create Credential Dialog */}
      <Dialog open={createCredentialDialogOpen} onClose={() => setCreateCredentialDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add Credential</DialogTitle>
        <DialogContent>
          <Box mt={2}>
            <TextField
              label="Credential Name"
              fullWidth
              margin="normal"
              value={newCredential.name}
              onChange={(e) => setNewCredential({...newCredential, name: e.target.value})}
            />
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Provider</InputLabel>
              <Select
                value={newCredential.provider || ''}
                label="Provider"
                onChange={(e) => setNewCredential({...newCredential, provider: e.target.value})}
              >
                <MenuItem value="aws">AWS</MenuItem>
                <MenuItem value="azure">Azure</MenuItem>
                <MenuItem value="gcp">GCP</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Type</InputLabel>
              <Select
                value={newCredential.type || ''}
                label="Type"
                onChange={(e) => setNewCredential({...newCredential, type: e.target.value})}
              >
                <MenuItem value="aws">AWS Credentials</MenuItem>
                <MenuItem value="azure">Azure Service Principal</MenuItem>
                <MenuItem value="gcp">GCP Service Account</MenuItem>
              </Select>
            </FormControl>
            
            <Typography variant="subtitle1" mt={3} mb={1}>
              Credentials
            </Typography>
            
            {newCredential.type === 'aws' && (
              <>
                <TextField
                  label="Access Key ID"
                  fullWidth
                  margin="normal"
                  type="password"
                />
                
                <TextField
                  label="Secret Access Key"
                  fullWidth
                  margin="normal"
                  type="password"
                />
                
                <TextField
                  label="Region"
                  fullWidth
                  margin="normal"
                />
              </>
            )}
            
            {newCredential.type === 'azure' && (
              <>
                <TextField
                  label="Tenant ID"
                  fullWidth
                  margin="normal"
                />
                
                <TextField
                  label="Client ID"
                  fullWidth
                  margin="normal"
                />
                
                <TextField
                  label="Client Secret"
                  fullWidth
                  margin="normal"
                  type="password"
                />
                
                <TextField
                  label="Subscription ID"
                  fullWidth
                  margin="normal"
                />
              </>
            )}
            
            {newCredential.type === 'gcp' && (
              <>
                <TextField
                  label="Project ID"
                  fullWidth
                  margin="normal"
                />
                
                <TextField
                  label="Service Account Key"
                  fullWidth
                  margin="normal"
                  multiline
                  rows={4}
                  type="password"
                />
              </>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateCredentialDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={createCredential}
            disabled={!newCredential.name || !newCredential.type || !newCredential.provider}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TargetIntegration;
