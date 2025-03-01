import React, { useState, useEffect } from 'react';
import { useWebSocketEvent, useWebSocketCategory } from '../../hooks/useWebSocket';
import { EventCategory, EventPriority } from '../../services/websocket.service';
import { Box, Card, CardContent, CardHeader, Typography, Chip, LinearProgress, Badge, IconButton, Tooltip, List, ListItem, ListItemText, Divider, Alert } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import PendingIcon from '@mui/icons-material/Pending';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';

// Pipeline status types
export enum PipelineStatus {
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  PENDING = 'pending',
  CANCELLED = 'cancelled'
}

// Pipeline execution data interface
interface PipelineExecution {
  executionId: string;
  pipelineId: string;
  status: PipelineStatus;
  startTime: string;
  endTime?: string;
  progress?: number;
  stages?: {
    name: string;
    status: PipelineStatus;
    startTime: string;
    endTime?: string;
  }[];
  error?: {
    message: string;
    stage?: string;
    details?: string;
  };
}

interface LivePipelineStatusProps {
  title?: string;
  maxItems?: number;
  showDetails?: boolean;
  height?: number | string;
  onPipelineClick?: (pipelineId: string, executionId: string) => void;
}

const LivePipelineStatus: React.FC<LivePipelineStatusProps> = ({
  title = 'Pipeline Status',
  maxItems = 5,
  showDetails = true,
  height = 400,
  onPipelineClick
}) => {
  // Subscribe to pipeline category events
  const { events: pipelineEvents, clearEvents } = useWebSocketCategory(EventCategory.PIPELINE);
  
  // State for pipeline executions
  const [executions, setExecutions] = useState<PipelineExecution[]>([]);
  
  // Process pipeline events to update executions
  useEffect(() => {
    if (pipelineEvents.length === 0) return;
    
    // Process events to update executions
    pipelineEvents.forEach(event => {
      if (event.event_type === 'pipeline_execution_started') {
        const execution = event.data.execution as PipelineExecution;
        setExecutions(prev => {
          // Add new execution or update existing one
          const exists = prev.some(e => e.executionId === execution.executionId);
          if (exists) {
            return prev.map(e => e.executionId === execution.executionId ? execution : e);
          } else {
            return [execution, ...prev].slice(0, maxItems);
          }
        });
      } else if (event.event_type === 'pipeline_execution_updated') {
        const execution = event.data.execution as PipelineExecution;
        setExecutions(prev => 
          prev.map(e => e.executionId === execution.executionId ? execution : e)
        );
      } else if (event.event_type === 'pipeline_execution_completed') {
        const execution = event.data.execution as PipelineExecution;
        setExecutions(prev => 
          prev.map(e => e.executionId === execution.executionId ? execution : e)
        );
      }
    });
  }, [pipelineEvents, maxItems]);
  
  // Get status color
  const getStatusColor = (status: PipelineStatus) => {
    switch (status) {
      case PipelineStatus.RUNNING:
        return 'primary';
      case PipelineStatus.COMPLETED:
        return 'success';
      case PipelineStatus.FAILED:
        return 'error';
      case PipelineStatus.PENDING:
        return 'warning';
      case PipelineStatus.CANCELLED:
        return 'default';
      default:
        return 'default';
    }
  };
  
  // Get status icon
  const getStatusIcon = (status: PipelineStatus) => {
    switch (status) {
      case PipelineStatus.RUNNING:
        return <PlayArrowIcon />;
      case PipelineStatus.COMPLETED:
        return <CheckCircleIcon color="success" />;
      case PipelineStatus.FAILED:
        return <ErrorIcon color="error" />;
      case PipelineStatus.PENDING:
        return <PendingIcon color="warning" />;
      case PipelineStatus.CANCELLED:
        return <MoreVertIcon color="disabled" />;
      default:
        return null;
    }
  };
  
  // Format time difference
  const formatTimeDiff = (startTime: string, endTime?: string) => {
    const start = new Date(startTime).getTime();
    const end = endTime ? new Date(endTime).getTime() : Date.now();
    const diff = end - start;
    
    // Format as mm:ss
    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };
  
  // Handle refresh
  const handleRefresh = () => {
    // In a real implementation, this would fetch the latest pipeline executions
    // For now, we'll just clear the events to simulate a refresh
    clearEvents();
  };
  
  return (
    <Card sx={{ height, display: 'flex', flexDirection: 'column' }}>
      <CardHeader
        title={title}
        action={
          <Tooltip title="Refresh">
            <IconButton onClick={handleRefresh}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        }
      />
      <CardContent sx={{ flex: 1, overflow: 'auto', p: 0 }}>
        {executions.length === 0 ? (
          <Box sx={{ p: 2, textAlign: 'center' }}>
            <Typography color="textSecondary">No pipeline executions yet</Typography>
          </Box>
        ) : (
          <List disablePadding>
            {executions.map((execution, index) => (
              <React.Fragment key={execution.executionId}>
                <ListItem
                  onClick={() => onPipelineClick?.(execution.pipelineId, execution.executionId)}
                  sx={{
                    p: 2,
                    cursor: onPipelineClick ? 'pointer' : 'default',
                    '&:hover': {
                      backgroundColor: theme => theme.palette.action.hover
                    }
                  }}
                >
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        {getStatusIcon(execution.status)}
                        <Typography variant="subtitle1" sx={{ ml: 1, fontWeight: 'bold' }}>
                          Pipeline {execution.pipelineId.substring(0, 8)}
                        </Typography>
                        {(() => {
                          const icon = getStatusIcon(execution.status);
                          return (
                            <Chip
                              label={execution.status}
                              color={getStatusColor(execution.status)}
                              size="small"
                              icon={icon || undefined}
                              sx={{ ml: 2 }}
                            />
                          );
                        })()}
                        <Box sx={{ flex: 1 }} />
                        <Typography variant="caption" color="textSecondary">
                          {formatTimeDiff(execution.startTime, execution.endTime)}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      <Box>
                        {execution.status === PipelineStatus.RUNNING && execution.progress !== undefined && (
                          <LinearProgress
                            variant="determinate"
                            value={execution.progress}
                            sx={{ mb: 1, height: 6, borderRadius: 3 }}
                          />
                        )}
                        
                        {execution.error && (
                          <Alert severity="error" sx={{ mt: 1, mb: 1 }}>
                            {execution.error.message}
                          </Alert>
                        )}
                        
                        {showDetails && execution.stages && (
                          <Box sx={{ mt: 1 }}>
                            {execution.stages.map((stage, stageIndex) => {
                              const icon = getStatusIcon(stage.status);
                              return (
                                <Chip
                                  key={stageIndex}
                                  label={stage.name}
                                  size="small"
                                  icon={icon || undefined}
                                  color={getStatusColor(stage.status)}
                                  sx={{ mr: 1, mb: 1 }}
                                />
                              );
                            })}
                          </Box>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
                {index < executions.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  );
};

export default LivePipelineStatus;
