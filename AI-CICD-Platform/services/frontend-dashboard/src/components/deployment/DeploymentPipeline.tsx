import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Button, 
  Card, 
  CardContent, 
  Typography, 
  Stepper, 
  Step, 
  StepLabel, 
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
  CircularProgress
} from '@mui/material';
import { 
  PlayArrow as PlayIcon, 
  Pause as PauseIcon, 
  Refresh as RefreshIcon, 
  History as HistoryIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { useWebSocketEvent } from '../../hooks/useWebSocket';

// Types
interface Environment {
  id: string;
  name: string;
  type: string;
  targetType: string;
  targetId: string;
  order: number;
}

interface DeploymentPipeline {
  id: string;
  name: string;
  description: string;
  environments: Environment[];
  strategy: string;
  status: string;
  createdAt: string;
  updatedAt: string;
}

interface DeploymentExecution {
  id: string;
  pipelineId: string;
  status: string;
  startTime: string;
  endTime?: string;
  stages: {
    id: string;
    name: string;
    environmentId: string;
    status: string;
    startTime?: string;
    endTime?: string;
  }[];
}

// Mock data for development
const mockPipelines: DeploymentPipeline[] = [
  {
    id: '1',
    name: 'Production Deployment Pipeline',
    description: 'Pipeline for deploying to production environment',
    environments: [
      { id: '1', name: 'Development', type: 'development', targetType: 'kubernetes', targetId: '1', order: 1 },
      { id: '2', name: 'Staging', type: 'staging', targetType: 'kubernetes', targetId: '2', order: 2 },
      { id: '3', name: 'Production', type: 'production', targetType: 'kubernetes', targetId: '3', order: 3 }
    ],
    strategy: 'blue-green',
    status: 'active',
    createdAt: '2025-03-01T12:00:00Z',
    updatedAt: '2025-03-01T12:00:00Z'
  },
  {
    id: '2',
    name: 'Microservices Deployment Pipeline',
    description: 'Pipeline for deploying microservices',
    environments: [
      { id: '1', name: 'Development', type: 'development', targetType: 'kubernetes', targetId: '1', order: 1 },
      { id: '2', name: 'Staging', type: 'staging', targetType: 'kubernetes', targetId: '2', order: 2 }
    ],
    strategy: 'canary',
    status: 'active',
    createdAt: '2025-03-01T12:00:00Z',
    updatedAt: '2025-03-01T12:00:00Z'
  }
];

const mockExecutions: DeploymentExecution[] = [
  {
    id: '1',
    pipelineId: '1',
    status: 'completed',
    startTime: '2025-03-01T14:00:00Z',
    endTime: '2025-03-01T14:30:00Z',
    stages: [
      { id: '1', name: 'Deploy to Development', environmentId: '1', status: 'completed', startTime: '2025-03-01T14:00:00Z', endTime: '2025-03-01T14:10:00Z' },
      { id: '2', name: 'Deploy to Staging', environmentId: '2', status: 'completed', startTime: '2025-03-01T14:10:00Z', endTime: '2025-03-01T14:20:00Z' },
      { id: '3', name: 'Deploy to Production', environmentId: '3', status: 'completed', startTime: '2025-03-01T14:20:00Z', endTime: '2025-03-01T14:30:00Z' }
    ]
  },
  {
    id: '2',
    pipelineId: '1',
    status: 'in-progress',
    startTime: '2025-03-01T15:00:00Z',
    stages: [
      { id: '1', name: 'Deploy to Development', environmentId: '1', status: 'completed', startTime: '2025-03-01T15:00:00Z', endTime: '2025-03-01T15:10:00Z' },
      { id: '2', name: 'Deploy to Staging', environmentId: '2', status: 'in-progress', startTime: '2025-03-01T15:10:00Z' },
      { id: '3', name: 'Deploy to Production', environmentId: '3', status: 'pending' }
    ]
  }
];

// Component
const DeploymentPipeline: React.FC = () => {
  const theme = useTheme();
  const { data: lastMessage } = useWebSocketEvent('deployment_update');
  
  const [pipelines, setPipelines] = useState<DeploymentPipeline[]>(mockPipelines);
  const [executions, setExecutions] = useState<DeploymentExecution[]>(mockExecutions);
  const [selectedPipeline, setSelectedPipeline] = useState<DeploymentPipeline | null>(null);
  const [selectedExecution, setSelectedExecution] = useState<DeploymentExecution | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  
  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState<boolean>(false);
  const [executeDialogOpen, setExecuteDialogOpen] = useState<boolean>(false);
  const [historyDialogOpen, setHistoryDialogOpen] = useState<boolean>(false);
  
  // Form states
  const [newPipeline, setNewPipeline] = useState<Partial<DeploymentPipeline>>({
    name: '',
    description: '',
    strategy: 'blue-green',
    environments: []
  });
  
  // Effect to handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      try {
        if (typeof lastMessage === 'object') {
          // Handle pipeline updates
          if (lastMessage.type === 'pipeline_update' && lastMessage.pipeline) {
            setPipelines(prevPipelines => {
              const index = prevPipelines.findIndex(p => p.id === lastMessage.pipeline.id);
              if (index >= 0) {
                const updatedPipelines = [...prevPipelines];
                updatedPipelines[index] = lastMessage.pipeline;
                return updatedPipelines;
              }
              return [...prevPipelines, lastMessage.pipeline];
            });
          } 
          // Handle execution updates
          else if (lastMessage.type === 'execution_update' && lastMessage.execution) {
            setExecutions(prevExecutions => {
              const index = prevExecutions.findIndex(e => e.id === lastMessage.execution.id);
              if (index >= 0) {
                const updatedExecutions = [...prevExecutions];
                updatedExecutions[index] = lastMessage.execution;
                return updatedExecutions;
              }
              return [...prevExecutions, lastMessage.execution];
            });
          }
        }
      } catch (error) {
        console.error('Error handling WebSocket message:', error);
      }
    }
  }, [lastMessage]);
  
  // Fetch pipelines
  const fetchPipelines = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would fetch from the API
      // const response = await fetch('/api/deployment-automation/pipelines');
      // const data = await response.json();
      // setPipelines(data);
      
      // For now, use mock data
      setPipelines(mockPipelines);
    } catch (error) {
      console.error('Error fetching pipelines:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Fetch executions for a pipeline
  const fetchExecutions = async (pipelineId: string) => {
    setLoading(true);
    try {
      // In a real implementation, this would fetch from the API
      // const response = await fetch(`/api/deployment-automation/pipelines/${pipelineId}/executions`);
      // const data = await response.json();
      // setExecutions(data);
      
      // For now, use mock data
      setExecutions(mockExecutions.filter(e => e.pipelineId === pipelineId));
    } catch (error) {
      console.error('Error fetching executions:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Create a new pipeline
  const createPipeline = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would send to the API
      // const response = await fetch('/api/deployment-automation/pipelines', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(newPipeline)
      // });
      // const data = await response.json();
      // setPipelines([...pipelines, data]);
      
      // For now, use mock data
      const newId = (pipelines.length + 1).toString();
      const createdPipeline: DeploymentPipeline = {
        id: newId,
        name: newPipeline.name || 'New Pipeline',
        description: newPipeline.description || '',
        environments: newPipeline.environments || [],
        strategy: newPipeline.strategy || 'blue-green',
        status: 'active',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      setPipelines([...pipelines, createdPipeline]);
      
      // Reset form
      setNewPipeline({
        name: '',
        description: '',
        strategy: 'blue-green',
        environments: []
      });
      
      // Close dialog
      setCreateDialogOpen(false);
    } catch (error) {
      console.error('Error creating pipeline:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Execute a pipeline
  const executePipeline = async (pipelineId: string) => {
    setLoading(true);
    try {
      // In a real implementation, this would send to the API
      // const response = await fetch(`/api/deployment-automation/pipelines/${pipelineId}/execute`, {
      //   method: 'POST'
      // });
      // const data = await response.json();
      // setExecutions([...executions, data]);
      
      // For now, use mock data
      const newId = (executions.length + 1).toString();
      const newExecution: DeploymentExecution = {
        id: newId,
        pipelineId,
        status: 'pending',
        startTime: new Date().toISOString(),
        stages: []
      };
      
      // Get pipeline to create stages
      const pipeline = pipelines.find(p => p.id === pipelineId);
      if (pipeline) {
        newExecution.stages = pipeline.environments.map((env, index) => ({
          id: (index + 1).toString(),
          name: `Deploy to ${env.name}`,
          environmentId: env.id,
          status: index === 0 ? 'pending' : 'pending'
        }));
      }
      
      setExecutions([...executions, newExecution]);
      
      // Close dialog
      setExecuteDialogOpen(false);
    } catch (error) {
      console.error('Error executing pipeline:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Handle pipeline selection
  const handlePipelineSelect = (pipeline: DeploymentPipeline) => {
    setSelectedPipeline(pipeline);
    fetchExecutions(pipeline.id);
  };
  
  // Render pipeline card
  const renderPipelineCard = (pipeline: DeploymentPipeline) => {
    const isSelected = selectedPipeline?.id === pipeline.id;
    
    return (
      <Card 
        key={pipeline.id} 
        sx={{ 
          mb: 2, 
          cursor: 'pointer',
          border: isSelected ? `2px solid ${theme.palette.primary.main}` : 'none'
        }}
        onClick={() => handlePipelineSelect(pipeline)}
      >
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="h6">{pipeline.name}</Typography>
            <Chip 
              label={pipeline.strategy} 
              size="small" 
              color={
                pipeline.strategy === 'blue-green' ? 'primary' : 
                pipeline.strategy === 'canary' ? 'secondary' : 
                'default'
              }
            />
          </Box>
          
          <Typography variant="body2" color="text.secondary" mb={2}>
            {pipeline.description}
          </Typography>
          
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Stepper alternativeLabel sx={{ flexGrow: 1 }}>
              {pipeline.environments.map((env) => (
                <Step key={env.id} completed={true}>
                  <StepLabel>{env.name}</StepLabel>
                </Step>
              ))}
            </Stepper>
            
            <Box>
              <IconButton 
                size="small" 
                color="primary"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedPipeline(pipeline);
                  setExecuteDialogOpen(true);
                }}
              >
                <PlayIcon />
              </IconButton>
              <IconButton 
                size="small" 
                color="info"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedPipeline(pipeline);
                  setHistoryDialogOpen(true);
                }}
              >
                <HistoryIcon />
              </IconButton>
              <IconButton 
                size="small" 
                color="error"
                onClick={(e) => {
                  e.stopPropagation();
                  // Delete pipeline
                }}
              >
                <DeleteIcon />
              </IconButton>
            </Box>
          </Box>
        </CardContent>
      </Card>
    );
  };
  
  // Render execution card
  const renderExecutionCard = (execution: DeploymentExecution) => {
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
        default:
          return 'default';
      }
    };
    
    return (
      <Card key={execution.id} sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="h6">Execution #{execution.id}</Typography>
            <Chip 
              label={execution.status} 
              size="small" 
              color={getStatusColor(execution.status)}
            />
          </Box>
          
          <Typography variant="body2" color="text.secondary" mb={2}>
            Started: {new Date(execution.startTime).toLocaleString()}
            {execution.endTime && ` • Completed: ${new Date(execution.endTime).toLocaleString()}`}
          </Typography>
          
          <Stepper alternativeLabel>
            {execution.stages.map((stage) => (
              <Step key={stage.id} completed={stage.status === 'completed'} active={stage.status === 'in-progress'}>
                <StepLabel error={stage.status === 'failed'}>
                  {stage.name}
                  <br />
                  <Chip 
                    label={stage.status} 
                    size="small" 
                    color={getStatusColor(stage.status)}
                    sx={{ mt: 1 }}
                  />
                </StepLabel>
              </Step>
            ))}
          </Stepper>
        </CardContent>
      </Card>
    );
  };
  
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Deployment Pipelines</Typography>
        <Button 
          variant="contained" 
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Create Pipeline
        </Button>
      </Box>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Typography variant="h6" mb={2}>Pipelines</Typography>
          {loading ? (
            <Box display="flex" justifyContent="center" my={4}>
              <CircularProgress />
            </Box>
          ) : (
            pipelines.map(renderPipelineCard)
          )}
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Typography variant="h6" mb={2}>Recent Executions</Typography>
          {selectedPipeline ? (
            loading ? (
              <Box display="flex" justifyContent="center" my={4}>
                <CircularProgress />
              </Box>
            ) : executions.length > 0 ? (
              executions.map(renderExecutionCard)
            ) : (
              <Typography variant="body1" color="text.secondary" align="center" my={4}>
                No executions found for this pipeline.
              </Typography>
            )
          ) : (
            <Typography variant="body1" color="text.secondary" align="center" my={4}>
              Select a pipeline to view its executions.
            </Typography>
          )}
        </Grid>
      </Grid>
      
      {/* Create Pipeline Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create Deployment Pipeline</DialogTitle>
        <DialogContent>
          <Box mt={2}>
            <TextField
              label="Pipeline Name"
              fullWidth
              margin="normal"
              value={newPipeline.name}
              onChange={(e) => setNewPipeline({...newPipeline, name: e.target.value})}
            />
            
            <TextField
              label="Description"
              fullWidth
              margin="normal"
              multiline
              rows={3}
              value={newPipeline.description}
              onChange={(e) => setNewPipeline({...newPipeline, description: e.target.value})}
            />
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Deployment Strategy</InputLabel>
              <Select
                value={newPipeline.strategy}
                label="Deployment Strategy"
                onChange={(e) => setNewPipeline({...newPipeline, strategy: e.target.value})}
              >
                <MenuItem value="blue-green">Blue-Green Deployment</MenuItem>
                <MenuItem value="canary">Canary Deployment</MenuItem>
                <MenuItem value="rolling">Rolling Deployment</MenuItem>
                <MenuItem value="recreate">Recreate Deployment</MenuItem>
              </Select>
            </FormControl>
            
            {/* Environment configuration would go here */}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={createPipeline}
            disabled={!newPipeline.name}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Execute Pipeline Dialog */}
      <Dialog open={executeDialogOpen} onClose={() => setExecuteDialogOpen(false)}>
        <DialogTitle>Execute Pipeline</DialogTitle>
        <DialogContent>
          <Typography variant="body1" mt={2}>
            Are you sure you want to execute the pipeline "{selectedPipeline?.name}"?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExecuteDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            color="primary"
            onClick={() => selectedPipeline && executePipeline(selectedPipeline.id)}
          >
            Execute
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* History Dialog */}
      <Dialog open={historyDialogOpen} onClose={() => setHistoryDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Deployment History</DialogTitle>
        <DialogContent>
          <Typography variant="h6" mt={2} mb={2}>
            {selectedPipeline?.name}
          </Typography>
          
          {executions.length > 0 ? (
            executions.map(renderExecutionCard)
          ) : (
            <Typography variant="body1" color="text.secondary" align="center" my={4}>
              No execution history found.
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHistoryDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DeploymentPipeline;
