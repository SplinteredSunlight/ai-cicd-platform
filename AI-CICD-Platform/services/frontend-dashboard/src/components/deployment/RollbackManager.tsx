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
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Paper,
  Tooltip
} from '@mui/material';
import { 
  Restore as RestoreIcon, 
  History as HistoryIcon,
  PlayArrow as ExecuteIcon,
  Cancel as CancelIcon,
  Info as InfoIcon,
  Add as AddIcon,
  Camera as SnapshotIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { useWebSocketEvent } from '../../hooks/useWebSocket';

// Types
interface RollbackStep {
  id: string;
  name: string;
  order: number;
  status: string;
  startTime?: string;
  endTime?: string;
  logs?: string[];
}

interface Rollback {
  id: string;
  deploymentId: string;
  pipelineId: string;
  environmentId: string;
  status: string;
  reason: string;
  strategy: string;
  trigger: string;
  snapshotId?: string;
  steps: RollbackStep[];
  startTime?: string;
  endTime?: string;
  initiatedBy: string;
  createdAt: string;
  updatedAt: string;
}

interface Snapshot {
  id: string;
  deploymentId: string;
  environmentId: string;
  timestamp: string;
  status: string;
  size: string;
  metadata: any;
  createdBy: string;
}

interface RollbackTestResult {
  id: string;
  deploymentId: string;
  environmentId: string;
  timestamp: string;
  status: string;
  result: string;
  details: any;
}

// Mock data for development
const mockRollbacks: Rollback[] = [
  {
    id: '1',
    deploymentId: '1',
    pipelineId: '1',
    environmentId: '3', // production
    status: 'completed',
    reason: 'Failed deployment',
    strategy: 'full',
    trigger: 'manual',
    snapshotId: '1',
    steps: [
      {
        id: '1',
        name: 'Stop current deployment',
        order: 1,
        status: 'completed',
        startTime: '2025-03-01T14:00:00Z',
        endTime: '2025-03-01T14:05:00Z'
      },
      {
        id: '2',
        name: 'Restore previous version',
        order: 2,
        status: 'completed',
        startTime: '2025-03-01T14:05:00Z',
        endTime: '2025-03-01T14:15:00Z'
      },
      {
        id: '3',
        name: 'Verify rollback',
        order: 3,
        status: 'completed',
        startTime: '2025-03-01T14:15:00Z',
        endTime: '2025-03-01T14:20:00Z'
      }
    ],
    startTime: '2025-03-01T14:00:00Z',
    endTime: '2025-03-01T14:20:00Z',
    initiatedBy: 'user1',
    createdAt: '2025-03-01T14:00:00Z',
    updatedAt: '2025-03-01T14:20:00Z'
  },
  {
    id: '2',
    deploymentId: '2',
    pipelineId: '1',
    environmentId: '3', // production
    status: 'in-progress',
    reason: 'Performance degradation',
    strategy: 'full',
    trigger: 'automatic',
    snapshotId: '2',
    steps: [
      {
        id: '1',
        name: 'Stop current deployment',
        order: 1,
        status: 'completed',
        startTime: '2025-03-01T15:00:00Z',
        endTime: '2025-03-01T15:05:00Z'
      },
      {
        id: '2',
        name: 'Restore previous version',
        order: 2,
        status: 'in-progress',
        startTime: '2025-03-01T15:05:00Z'
      },
      {
        id: '3',
        name: 'Verify rollback',
        order: 3,
        status: 'pending'
      }
    ],
    startTime: '2025-03-01T15:00:00Z',
    initiatedBy: 'system',
    createdAt: '2025-03-01T15:00:00Z',
    updatedAt: '2025-03-01T15:05:00Z'
  }
];

const mockSnapshots: Snapshot[] = [
  {
    id: '1',
    deploymentId: '1',
    environmentId: '3', // production
    timestamp: '2025-03-01T13:00:00Z',
    status: 'completed',
    size: '10MB',
    metadata: {
      version: '1.0.0',
      commit: 'abc123'
    },
    createdBy: 'user1'
  },
  {
    id: '2',
    deploymentId: '2',
    environmentId: '3', // production
    timestamp: '2025-03-01T14:30:00Z',
    status: 'completed',
    size: '15MB',
    metadata: {
      version: '1.1.0',
      commit: 'def456'
    },
    createdBy: 'user1'
  }
];

const mockTestResults: RollbackTestResult[] = [
  {
    id: '1',
    deploymentId: '1',
    environmentId: '3', // production
    timestamp: '2025-03-01T13:30:00Z',
    status: 'completed',
    result: 'success',
    details: {
      message: 'Rollback test completed successfully',
      duration: '5s'
    }
  },
  {
    id: '2',
    deploymentId: '2',
    environmentId: '3', // production
    timestamp: '2025-03-01T14:45:00Z',
    status: 'completed',
    result: 'success',
    details: {
      message: 'Rollback test completed successfully',
      duration: '7s'
    }
  }
];

// Component
const RollbackManager: React.FC = () => {
  const theme = useTheme();
  const { data: lastMessage } = useWebSocketEvent('rollback_update');
  
  const [rollbacks, setRollbacks] = useState<Rollback[]>(mockRollbacks);
  const [snapshots, setSnapshots] = useState<Snapshot[]>(mockSnapshots);
  const [testResults, setTestResults] = useState<RollbackTestResult[]>(mockTestResults);
  const [selectedRollback, setSelectedRollback] = useState<Rollback | null>(null);
  const [selectedSnapshot, setSelectedSnapshot] = useState<Snapshot | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  
  // Dialog states
  const [createRollbackDialogOpen, setCreateRollbackDialogOpen] = useState<boolean>(false);
  const [rollbackDetailsDialogOpen, setRollbackDetailsDialogOpen] = useState<boolean>(false);
  const [createSnapshotDialogOpen, setCreateSnapshotDialogOpen] = useState<boolean>(false);
  const [testRollbackDialogOpen, setTestRollbackDialogOpen] = useState<boolean>(false);
  
  // Form states
  const [newRollback, setNewRollback] = useState<Partial<Rollback>>({
    reason: '',
    strategy: 'full',
    snapshotId: ''
  });
  
  const [newSnapshot, setNewSnapshot] = useState<Partial<Snapshot>>({
    deploymentId: '',
    environmentId: ''
  });
  
  const [testRollback, setTestRollback] = useState<{
    deploymentId: string;
    environmentId: string;
  }>({
    deploymentId: '',
    environmentId: ''
  });
  
  // Effect to handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      try {
        if (typeof lastMessage === 'object') {
          // Handle rollback updates
          if (lastMessage.type === 'rollback_update' && lastMessage.rollback) {
            setRollbacks(prevRollbacks => {
              const index = prevRollbacks.findIndex(r => r.id === lastMessage.rollback.id);
              if (index >= 0) {
                const updatedRollbacks = [...prevRollbacks];
                updatedRollbacks[index] = lastMessage.rollback;
                return updatedRollbacks;
              }
              return [...prevRollbacks, lastMessage.rollback];
            });
          } 
          // Handle snapshot updates
          else if (lastMessage.type === 'snapshot_update' && lastMessage.snapshot) {
            setSnapshots(prevSnapshots => {
              const index = prevSnapshots.findIndex(s => s.id === lastMessage.snapshot.id);
              if (index >= 0) {
                const updatedSnapshots = [...prevSnapshots];
                updatedSnapshots[index] = lastMessage.snapshot;
                return updatedSnapshots;
              }
              return [...prevSnapshots, lastMessage.snapshot];
            });
          }
          // Handle test result updates
          else if (lastMessage.type === 'test_result_update' && lastMessage.testResult) {
            setTestResults(prevTestResults => {
              const index = prevTestResults.findIndex(t => t.id === lastMessage.testResult.id);
              if (index >= 0) {
                const updatedTestResults = [...prevTestResults];
                updatedTestResults[index] = lastMessage.testResult;
                return updatedTestResults;
              }
              return [...prevTestResults, lastMessage.testResult];
            });
          }
        }
      } catch (error) {
        console.error('Error handling WebSocket message:', error);
      }
    }
  }, [lastMessage]);
  
  // Fetch rollbacks
  const fetchRollbacks = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would fetch from the API
      // const response = await fetch('/api/deployment-automation/rollbacks');
      // const data = await response.json();
      // setRollbacks(data);
      
      // For now, use mock data
      setRollbacks(mockRollbacks);
    } catch (error) {
      console.error('Error fetching rollbacks:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Fetch snapshots
  const fetchSnapshots = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would fetch from the API
      // const response = await fetch('/api/deployment-automation/snapshots');
      // const data = await response.json();
      // setSnapshots(data);
      
      // For now, use mock data
      setSnapshots(mockSnapshots);
    } catch (error) {
      console.error('Error fetching snapshots:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Create a new rollback
  const createRollback = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would send to the API
      // const response = await fetch('/api/deployment-automation/rollbacks', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(newRollback)
      // });
      // const data = await response.json();
      // setRollbacks([...rollbacks, data]);
      
      // For now, use mock data
      const newId = (rollbacks.length + 1).toString();
      const createdRollback: Rollback = {
        id: newId,
        deploymentId: newRollback.deploymentId || '1',
        pipelineId: newRollback.pipelineId || '1',
        environmentId: newRollback.environmentId || '3',
        status: 'pending',
        reason: newRollback.reason || 'Manual rollback',
        strategy: newRollback.strategy || 'full',
        trigger: 'manual',
        snapshotId: newRollback.snapshotId,
        steps: [
          {
            id: '1',
            name: 'Stop current deployment',
            order: 1,
            status: 'pending'
          },
          {
            id: '2',
            name: 'Restore previous version',
            order: 2,
            status: 'pending'
          },
          {
            id: '3',
            name: 'Verify rollback',
            order: 3,
            status: 'pending'
          }
        ],
        initiatedBy: 'user1',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      setRollbacks([...rollbacks, createdRollback]);
      
      // Reset form
      setNewRollback({
        reason: '',
        strategy: 'full',
        snapshotId: ''
      });
      
      // Close dialog
      setCreateRollbackDialogOpen(false);
    } catch (error) {
      console.error('Error creating rollback:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Create a new snapshot
  const createSnapshot = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would send to the API
      // const response = await fetch('/api/deployment-automation/snapshots', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(newSnapshot)
      // });
      // const data = await response.json();
      // setSnapshots([...snapshots, data]);
      
      // For now, use mock data
      const newId = (snapshots.length + 1).toString();
      const createdSnapshot: Snapshot = {
        id: newId,
        deploymentId: newSnapshot.deploymentId || '1',
        environmentId: newSnapshot.environmentId || '3',
        timestamp: new Date().toISOString(),
        status: 'completed',
        size: '12MB',
        metadata: {
          version: '1.2.0',
          commit: 'ghi789'
        },
        createdBy: 'user1'
      };
      setSnapshots([...snapshots, createdSnapshot]);
      
      // Reset form
      setNewSnapshot({
        deploymentId: '',
        environmentId: ''
      });
      
      // Close dialog
      setCreateSnapshotDialogOpen(false);
    } catch (error) {
      console.error('Error creating snapshot:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Test rollback
  const testRollbackFunc = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would send to the API
      // const response = await fetch('/api/deployment-automation/rollbacks/test', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(testRollback)
      // });
      // const data = await response.json();
      // setTestResults([...testResults, data]);
      
      // For now, use mock data
      const newId = (testResults.length + 1).toString();
      const createdTestResult: RollbackTestResult = {
        id: newId,
        deploymentId: testRollback.deploymentId || '1',
        environmentId: testRollback.environmentId || '3',
        timestamp: new Date().toISOString(),
        status: 'completed',
        result: 'success',
        details: {
          message: 'Rollback test completed successfully',
          duration: '6s'
        }
      };
      setTestResults([...testResults, createdTestResult]);
      
      // Reset form
      setTestRollback({
        deploymentId: '',
        environmentId: ''
      });
      
      // Close dialog
      setTestRollbackDialogOpen(false);
    } catch (error) {
      console.error('Error testing rollback:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Execute a rollback
  const executeRollback = async (rollbackId: string) => {
    setLoading(true);
    try {
      // In a real implementation, this would send to the API
      // const response = await fetch(`/api/deployment-automation/rollbacks/${rollbackId}/execute`, {
      //   method: 'POST'
      // });
      // const data = await response.json();
      // setRollbacks(prevRollbacks => {
      //   const index = prevRollbacks.findIndex(r => r.id === rollbackId);
      //   if (index >= 0) {
      //     const updatedRollbacks = [...prevRollbacks];
      //     updatedRollbacks[index] = data;
      //     return updatedRollbacks;
      //   }
      //   return prevRollbacks;
      // });
      
      // For now, use mock data
      setRollbacks(prevRollbacks => {
        const index = prevRollbacks.findIndex(r => r.id === rollbackId);
        if (index >= 0) {
          const updatedRollbacks = [...prevRollbacks];
          const rollback = { ...updatedRollbacks[index] };
          
          // Update status
          rollback.status = 'in-progress';
          rollback.startTime = new Date().toISOString();
          rollback.steps[0].status = 'in-progress';
          rollback.steps[0].startTime = new Date().toISOString();
          
          updatedRollbacks[index] = rollback;
          return updatedRollbacks;
        }
        return prevRollbacks;
      });
    } catch (error) {
      console.error('Error executing rollback:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Cancel a rollback
  const cancelRollback = async (rollbackId: string) => {
    setLoading(true);
    try {
      // In a real implementation, this would send to the API
      // const response = await fetch(`/api/deployment-automation/rollbacks/${rollbackId}/cancel`, {
      //   method: 'POST'
      // });
      // const data = await response.json();
      // setRollbacks(prevRollbacks => {
      //   const index = prevRollbacks.findIndex(r => r.id === rollbackId);
      //   if (index >= 0) {
      //     const updatedRollbacks = [...prevRollbacks];
      //     updatedRollbacks[index] = data;
      //     return updatedRollbacks;
      //   }
      //   return prevRollbacks;
      // });
      
      // For now, use mock data
      setRollbacks(prevRollbacks => {
        const index = prevRollbacks.findIndex(r => r.id === rollbackId);
        if (index >= 0) {
          const updatedRollbacks = [...prevRollbacks];
          const rollback = { ...updatedRollbacks[index] };
          
          // Update status
          rollback.status = 'cancelled';
          
          // Update pending steps
          rollback.steps = rollback.steps.map(step => {
            if (step.status === 'pending') {
              return { ...step, status: 'cancelled' };
            }
            return step;
          });
          
          updatedRollbacks[index] = rollback;
          return updatedRollbacks;
        }
        return prevRollbacks;
      });
    } catch (error) {
      console.error('Error cancelling rollback:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'in-progress':
        return 'info';
      case 'pending':
        return 'default';
      case 'failed':
        return 'error';
      case 'cancelled':
        return 'warning';
      default:
        return 'default';
    }
  };
  
  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <SuccessIcon />;
      case 'in-progress':
        return <CircularProgress size={20} />;
      case 'pending':
        return null;
      case 'failed':
        return <ErrorIcon />;
      case 'cancelled':
        return <WarningIcon />;
      default:
        return null;
    }
  };
  
  // Render rollback card
  const renderRollbackCard = (rollback: Rollback) => {
    const isSelected = selectedRollback?.id === rollback.id;
    
    return (
      <Card 
        key={rollback.id} 
        sx={{ 
          mb: 2, 
          cursor: 'pointer',
          border: isSelected ? `2px solid ${theme.palette.primary.main}` : 'none'
        }}
        onClick={() => setSelectedRollback(rollback)}
      >
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="h6">Rollback #{rollback.id}</Typography>
            <Chip 
              label={rollback.status} 
              size="small" 
              color={getStatusColor(rollback.status)}
            />
          </Box>
          
          <Typography variant="body2" color="text.secondary" mb={2}>
            Reason: {rollback.reason}
          </Typography>
          
          <Typography variant="body2" color="text.secondary" mb={2}>
            Strategy: {rollback.strategy} • Trigger: {rollback.trigger}
            {rollback.startTime && ` • Started: ${new Date(rollback.startTime).toLocaleString()}`}
            {rollback.endTime && ` • Completed: ${new Date(rollback.endTime).toLocaleString()}`}
          </Typography>
          
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Chip 
              label={`${rollback.steps.filter(s => s.status === 'completed').length}/${rollback.steps.length} Steps`}
              size="small"
              color="info"
            />
            
            <Box>
              {rollback.status === 'pending' && (
                <Tooltip title="Execute Rollback">
                  <IconButton 
                    color="primary"
                    onClick={(e) => {
                      e.stopPropagation();
                      executeRollback(rollback.id);
                    }}
                  >
                    <ExecuteIcon />
                  </IconButton>
                </Tooltip>
              )}
              
              {(rollback.status === 'pending' || rollback.status === 'in-progress') && (
                <Tooltip title="Cancel Rollback">
                  <IconButton 
                    color="error"
                    onClick={(e) => {
                      e.stopPropagation();
                      cancelRollback(rollback.id);
                    }}
                  >
                    <CancelIcon />
                  </IconButton>
                </Tooltip>
              )}
              
              <Tooltip title="View Details">
                <IconButton 
                  color="info"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedRollback(rollback);
                    setRollbackDetailsDialogOpen(true);
                  }}
                >
                  <InfoIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
        </CardContent>
      </Card>
    );
  };
  
  // Render snapshot card
  const renderSnapshotCard = (snapshot: Snapshot) => {
    const isSelected = selectedSnapshot?.id === snapshot.id;
    
    return (
      <Card 
        key={snapshot.id} 
        sx={{ 
          mb: 2, 
          cursor: 'pointer',
          border: isSelected ? `2px solid ${theme.palette.primary.main}` : 'none'
        }}
        onClick={() => setSelectedSnapshot(snapshot)}
      >
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="h6">Snapshot #{snapshot.id}</Typography>
            <Chip 
              label={snapshot.status} 
              size="small" 
              color={getStatusColor(snapshot.status)}
            />
          </Box>
          
          <Typography variant="body2" color="text.secondary" mb={2}>
            Created: {new Date(snapshot.timestamp).toLocaleString()} • Size: {snapshot.size}
          </Typography>
          
          <Typography variant="body2" color="text.secondary" mb={2}>
            Deployment: {snapshot.deploymentId} • Environment: {snapshot.environmentId}
          </Typography>
          
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Chip 
              label={`Version: ${snapshot.metadata.version}`}
              size="small"
              color="info"
            />
            
            <Button 
              variant="outlined" 
              size="small"
              startIcon={<RestoreIcon />}
              onClick={() => {
                setNewRollback({
                  ...newRollback,
                  deploymentId: snapshot.deploymentId,
                  environmentId: snapshot.environmentId,
                  snapshotId: snapshot.id
                });
                setCreateRollbackDialogOpen(true);
              }}
            >
              Rollback to this Snapshot
            </Button>
          </Box>
        </CardContent>
      </Card>
    );
  };
  
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Rollback & Recovery</Typography>
        <Box>
          <Button 
            variant="outlined" 
            startIcon={<SnapshotIcon />}
            onClick={() => setCreateSnapshotDialogOpen(true)}
            sx={{ mr: 2 }}
          >
            Create Snapshot
          </Button>
          <Button 
            variant="contained" 
            startIcon={<RestoreIcon />}
            onClick={() => setCreateRollbackDialogOpen(true)}
          >
            Create Rollback
          </Button>
        </Box>
      </Box>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Typography variant="h6" mb={2}>Recent Rollbacks</Typography>
          {loading ? (
            <Box display="flex" justifyContent="center" my={4}>
              <CircularProgress />
            </Box>
          ) : rollbacks.length > 0 ? (
            rollbacks.map(renderRollbackCard)
          ) : (
            <Typography variant="body1" color="text.secondary" align="center" my={4}>
              No rollbacks found.
            </Typography>
          )}
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Typography variant="h6" mb={2}>Available Snapshots</Typography>
          {loading ? (
            <Box display="flex" justifyContent="center" my={4}>
              <CircularProgress />
            </Box>
          ) : snapshots.length > 0 ? (
            snapshots.map(renderSnapshotCard)
          ) : (
            <Typography variant="body1" color="text.secondary" align="center" my={4}>
              No snapshots found.
            </Typography>
          )}
          
          <Box mt={4}>
            <Typography variant="h6" mb={2}>Rollback Testing</Typography>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="body2" color="text.secondary" mb={2}>
                Test rollback procedures without affecting production systems.
              </Typography>
              
              <Button 
                variant="outlined" 
                startIcon={<HistoryIcon />}
                fullWidth
                onClick={() => setTestRollbackDialogOpen(true)}
              >
                Test Rollback
              </Button>
              
              {testResults.length > 0 && (
                <Box mt={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    Recent Test Results:
                  </Typography>
                  
                  <List dense>
                    {testResults.slice(0, 3).map((result, index) => (
                      <React.Fragment key={result.id}>
                        <ListItem>
                          <ListItemText 
                            primary={`Test #${result.id} - ${result.result}`}
                            secondary={`${new Date(result.timestamp).toLocaleString()} - ${result.details.message}`}
                          />
                          <ListItemSecondaryAction>
                            <Chip 
                              label={result.result} 
                              size="small" 
                              color={result.result === 'success' ? 'success' : 'error'}
                            />
                          </ListItemSecondaryAction>
                        </ListItem>
                        {index < testResults.slice(0, 3).length - 1 && <Divider component="li" />}
                      </React.Fragment>
                    ))}
                  </List>
                </Box>
              )}
            </Paper>
          </Box>
        </Grid>
      </Grid>
      
      {/* Create Rollback Dialog */}
      <Dialog open={createRollbackDialogOpen} onClose={() => setCreateRollbackDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create Rollback</DialogTitle>
        <DialogContent>
          <Box mt={2}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Deployment</InputLabel>
              <Select
                value={newRollback.deploymentId || ''}
                label="Deployment"
                onChange={(e) => setNewRollback({...newRollback, deploymentId: e.target.value})}
              >
                <MenuItem value="1">Deployment #1</MenuItem>
                <MenuItem value="2">Deployment #2</MenuItem>
                <MenuItem value="3">Deployment #3</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Environment</InputLabel>
              <Select
                value={newRollback.environmentId || ''}
                label="Environment"
                onChange={(e) => setNewRollback({...newRollback, environmentId: e.target.value})}
              >
                <MenuItem value="1">Development</MenuItem>
                <MenuItem value="2">Staging</MenuItem>
                <MenuItem value="3">Production</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Strategy</InputLabel>
              <Select
                value={newRollback.strategy || 'full'}
                label="Strategy"
                onChange={(e) => setNewRollback({...newRollback, strategy: e.target.value})}
              >
                <MenuItem value="full">Full Rollback</MenuItem>
                <MenuItem value="partial">Partial Rollback</MenuItem>
                <MenuItem value="canary">Canary Rollback</MenuItem>
                <MenuItem value="custom">Custom Rollback</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Snapshot</InputLabel>
              <Select
                value={newRollback.snapshotId || ''}
                label="Snapshot"
                onChange={(e) => setNewRollback({...newRollback, snapshotId: e.target.value})}
              >
                <MenuItem value="">None</MenuItem>
                {snapshots.map(snapshot => (
                  <MenuItem key={snapshot.id} value={snapshot.id}>
                    Snapshot #{snapshot.id} - {new Date(snapshot.timestamp).toLocaleString()}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <TextField
              label="Reason"
              fullWidth
              margin="normal"
              multiline
              rows={3}
              value={newRollback.reason}
              onChange={(e) => setNewRollback({...newRollback, reason: e.target.value})}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateRollbackDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={createRollback}
            disabled={!newRollback.deploymentId || !newRollback.environmentId || !newRollback.reason}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Rollback Details Dialog */}
      <Dialog open={rollbackDetailsDialogOpen} onClose={() => setRollbackDetailsDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Rollback Details</DialogTitle>
        <DialogContent>
          {selectedRollback && (
            <Box mt={2}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Rollback #{selectedRollback.id}</Typography>
                <Chip 
                  label={selectedRollback.status} 
                  color={getStatusColor(selectedRollback.status)}
                />
              </Box>
              
              <Typography variant="body2" color="text.secondary" mb={2}>
                Reason: {selectedRollback.reason}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" mb={3}>
                Strategy: {selectedRollback.strategy} • Trigger: {selectedRollback.trigger}
                {selectedRollback.startTime && ` • Started: ${new Date(selectedRollback.startTime).toLocaleString()}`}
                {selectedRollback.endTime && ` • Completed: ${new Date(selectedRollback.endTime).toLocaleString()}`}
              </Typography>
              
              <Typography variant="subtitle1" gutterBottom>
                Rollback Steps
              </Typography>
              
              <Stepper orientation="vertical" sx={{ mt: 2 }}>
                {selectedRollback.steps.map((step) => (
                  <Step key={step.id} active={step.status === 'in-progress'} completed={step.status === 'completed'}>
                    <StepLabel
                      error={step.status === 'failed'}
                      icon={getStatusIcon(step.status)}
                    >
                      {step.name}
                    </StepLabel>
                    <StepContent>
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                          Status: {step.status}
                          {step.startTime && ` • Started: ${new Date(step.startTime).toLocaleString()}`}
                          {step.endTime && ` • Completed: ${new Date(step.endTime).toLocaleString()}`}
                        </Typography>
                        
                        {step.logs && step.logs.length > 0 && (
                          <Paper variant="outlined" sx={{ p: 1, mt: 1, bgcolor: 'background.default' }}>
                            <Typography variant="caption" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                              {step.logs.join('\n')}
                            </Typography>
                          </Paper>
                        )}
                      </Box>
                    </StepContent>
                  </Step>
                ))}
              </Stepper>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRollbackDetailsDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
      
      {/* Create Snapshot Dialog */}
      <Dialog open={createSnapshotDialogOpen} onClose={() => setCreateSnapshotDialogOpen(false)}>
        <DialogTitle>Create Snapshot</DialogTitle>
        <DialogContent>
          <Box mt={2}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Deployment</InputLabel>
              <Select
                value={newSnapshot.deploymentId || ''}
                label="Deployment"
                onChange={(e) => setNewSnapshot({...newSnapshot, deploymentId: e.target.value})}
              >
                <MenuItem value="1">Deployment #1</MenuItem>
                <MenuItem value="2">Deployment #2</MenuItem>
                <MenuItem value="3">Deployment #3</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Environment</InputLabel>
              <Select
                value={newSnapshot.environmentId || ''}
                label="Environment"
                onChange={(e) => setNewSnapshot({...newSnapshot, environmentId: e.target.value})}
              >
                <MenuItem value="1">Development</MenuItem>
                <MenuItem value="2">Staging</MenuItem>
                <MenuItem value="3">Production</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateSnapshotDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={createSnapshot}
            disabled={!newSnapshot.deploymentId || !newSnapshot.environmentId}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Test Rollback Dialog */}
      <Dialog open={testRollbackDialogOpen} onClose={() => setTestRollbackDialogOpen(false)}>
        <DialogTitle>Test Rollback</DialogTitle>
        <DialogContent>
          <Box mt={2}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Deployment</InputLabel>
              <Select
                value={testRollback.deploymentId || ''}
                label="Deployment"
                onChange={(e) => setTestRollback({...testRollback, deploymentId: e.target.value})}
              >
                <MenuItem value="1">Deployment #1</MenuItem>
                <MenuItem value="2">Deployment #2</MenuItem>
                <MenuItem value="3">Deployment #3</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Environment</InputLabel>
              <Select
                value={testRollback.environmentId || ''}
                label="Environment"
                onChange={(e) => setTestRollback({...testRollback, environmentId: e.target.value})}
              >
                <MenuItem value="1">Development</MenuItem>
                <MenuItem value="2">Staging</MenuItem>
                <MenuItem value="3">Production</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestRollbackDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={testRollbackFunc}
            disabled={!testRollback.deploymentId || !testRollback.environmentId}
          >
            Test
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RollbackManager;
