import React, { useState, useEffect } from 'react';
import { useWebSocketCategory } from '../../hooks/useWebSocket';
import { EventCategory, EventPriority } from '../../services/websocket.service';
import { 
  Box, 
  Card, 
  CardContent, 
  CardHeader, 
  Typography, 
  IconButton, 
  Tooltip, 
  List, 
  ListItem, 
  ListItemText, 
  ListItemIcon, 
  Divider, 
  Chip, 
  Badge,
  Collapse,
  Button,
  Avatar,
  LinearProgress
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import BugReportIcon from '@mui/icons-material/BugReport';
import CodeIcon from '@mui/icons-material/Code';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import BuildIcon from '@mui/icons-material/Build';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import NotificationsIcon from '@mui/icons-material/Notifications';
import NotificationsOffIcon from '@mui/icons-material/NotificationsOff';
import HistoryIcon from '@mui/icons-material/History';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import WarningIcon from '@mui/icons-material/Warning';

// Debug event types
export enum DebugEventType {
  ERROR_DETECTED = 'error_detected',
  PATCH_GENERATED = 'patch_generated',
  PATCH_APPLIED = 'patch_applied',
  PATCH_ROLLBACK = 'patch_rollback',
  ML_CLASSIFICATION = 'ml_classification',
  SESSION_CREATED = 'session_created',
  SESSION_UPDATED = 'session_updated'
}

// Debug event status
export enum DebugEventStatus {
  SUCCESS = 'success',
  FAILURE = 'failure',
  WARNING = 'warning',
  INFO = 'info',
  IN_PROGRESS = 'in_progress'
}

// Debug event interface
interface DebugEvent {
  eventId: string;
  sessionId: string;
  type: DebugEventType;
  status: DebugEventStatus;
  title: string;
  description: string;
  timestamp: string;
  details?: {
    errorId?: string;
    patchId?: string;
    errorMessage?: string;
    errorType?: string;
    patchDescription?: string;
    patchCode?: string;
    mlClassification?: {
      category: string;
      confidence: number;
      possibleCauses: string[];
    };
    affectedFiles?: string[];
  };
}

interface DebugActivityFeedProps {
  title?: string;
  maxItems?: number;
  height?: number | string;
  showDetails?: boolean;
  onEventClick?: (eventId: string, sessionId: string) => void;
}

const DebugActivityFeed: React.FC<DebugActivityFeedProps> = ({
  title = 'Debug Activity',
  maxItems = 10,
  height = 400,
  showDetails = true,
  onEventClick
}) => {
  // Subscribe to debug category events
  const { events: debugEvents, clearEvents } = useWebSocketCategory(EventCategory.DEBUG);
  
  // State for debug events
  const [events, setEvents] = useState<DebugEvent[]>([]);
  const [expandedEvent, setExpandedEvent] = useState<string | null>(null);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  
  // Process debug events
  useEffect(() => {
    if (debugEvents.length === 0 || !notificationsEnabled) return;
    
    // Map WebSocket events to debug events
    debugEvents.forEach(wsEvent => {
      let debugEvent: DebugEvent | null = null;
      
      if (wsEvent.event_type === 'debug_error_detected') {
        debugEvent = {
          eventId: `error-${wsEvent.data.errorId}`,
          sessionId: wsEvent.data.sessionId,
          type: DebugEventType.ERROR_DETECTED,
          status: DebugEventStatus.WARNING,
          title: 'Error Detected',
          description: wsEvent.data.error.message || 'An error was detected in the pipeline',
          timestamp: wsEvent.timestamp || new Date().toISOString(),
          details: {
            errorId: wsEvent.data.errorId,
            errorMessage: wsEvent.data.error.message,
            errorType: wsEvent.data.error.type,
            affectedFiles: wsEvent.data.error.affectedFiles
          }
        };
      } else if (wsEvent.event_type === 'debug_patch_generated') {
        debugEvent = {
          eventId: `patch-gen-${wsEvent.data.patchId}`,
          sessionId: wsEvent.data.sessionId,
          type: DebugEventType.PATCH_GENERATED,
          status: DebugEventStatus.INFO,
          title: 'Patch Generated',
          description: wsEvent.data.patch.description || 'A patch was generated',
          timestamp: wsEvent.timestamp || new Date().toISOString(),
          details: {
            patchId: wsEvent.data.patchId,
            patchDescription: wsEvent.data.patch.description,
            patchCode: wsEvent.data.patch.code,
            affectedFiles: wsEvent.data.patch.affectedFiles
          }
        };
      } else if (wsEvent.event_type === 'debug_patch_applied') {
        debugEvent = {
          eventId: `patch-apply-${wsEvent.data.patchId}`,
          sessionId: wsEvent.data.sessionId,
          type: DebugEventType.PATCH_APPLIED,
          status: wsEvent.data.result.success ? DebugEventStatus.SUCCESS : DebugEventStatus.FAILURE,
          title: wsEvent.data.result.success ? 'Patch Applied Successfully' : 'Patch Application Failed',
          description: wsEvent.data.result.message || (wsEvent.data.result.success ? 'Patch was applied successfully' : 'Failed to apply patch'),
          timestamp: wsEvent.timestamp || new Date().toISOString(),
          details: {
            patchId: wsEvent.data.patchId,
            errorMessage: wsEvent.data.result.success ? undefined : wsEvent.data.result.error
          }
        };
      } else if (wsEvent.event_type === 'debug_patch_rollback') {
        debugEvent = {
          eventId: `patch-rollback-${wsEvent.data.patchId}`,
          sessionId: wsEvent.data.sessionId,
          type: DebugEventType.PATCH_ROLLBACK,
          status: wsEvent.data.result.success ? DebugEventStatus.SUCCESS : DebugEventStatus.FAILURE,
          title: wsEvent.data.result.success ? 'Patch Rolled Back' : 'Patch Rollback Failed',
          description: wsEvent.data.result.message || (wsEvent.data.result.success ? 'Patch was rolled back successfully' : 'Failed to roll back patch'),
          timestamp: wsEvent.timestamp || new Date().toISOString(),
          details: {
            patchId: wsEvent.data.patchId,
            errorMessage: wsEvent.data.result.success ? undefined : wsEvent.data.result.error
          }
        };
      } else if (wsEvent.event_type === 'debug_ml_classification') {
        debugEvent = {
          eventId: `ml-class-${wsEvent.data.errorId}`,
          sessionId: wsEvent.data.sessionId || 'unknown',
          type: DebugEventType.ML_CLASSIFICATION,
          status: DebugEventStatus.INFO,
          title: 'ML Classification',
          description: `Error classified as ${wsEvent.data.classifications.category} with ${Math.round(wsEvent.data.classifications.confidence * 100)}% confidence`,
          timestamp: wsEvent.timestamp || new Date().toISOString(),
          details: {
            errorId: wsEvent.data.errorId,
            mlClassification: {
              category: wsEvent.data.classifications.category,
              confidence: wsEvent.data.classifications.confidence,
              possibleCauses: wsEvent.data.classifications.possibleCauses
            }
          }
        };
      } else if (wsEvent.event_type === 'debug_session_created') {
        debugEvent = {
          eventId: `session-created-${wsEvent.data.sessionId}`,
          sessionId: wsEvent.data.sessionId,
          type: DebugEventType.SESSION_CREATED,
          status: DebugEventStatus.INFO,
          title: 'Debug Session Created',
          description: wsEvent.data.session.description || 'A new debug session was created',
          timestamp: wsEvent.timestamp || new Date().toISOString(),
          details: {}
        };
      } else if (wsEvent.event_type === 'debug_session_updated') {
        debugEvent = {
          eventId: `session-updated-${wsEvent.data.sessionId}-${Date.now()}`,
          sessionId: wsEvent.data.sessionId,
          type: DebugEventType.SESSION_UPDATED,
          status: DebugEventStatus.INFO,
          title: 'Debug Session Updated',
          description: wsEvent.data.session.description || 'Debug session was updated',
          timestamp: wsEvent.timestamp || new Date().toISOString(),
          details: {}
        };
      }
      
      if (debugEvent) {
        setEvents(prev => {
          // Add new event or update existing one
          const exists = prev.some(e => e.eventId === debugEvent!.eventId);
          if (exists) {
            return prev.map(e => e.eventId === debugEvent!.eventId ? debugEvent! : e);
          } else {
            return [debugEvent!, ...prev].slice(0, maxItems);
          }
        });
      }
    });
  }, [debugEvents, maxItems, notificationsEnabled]);
  
  // Get status color
  const getStatusColor = (status: DebugEventStatus) => {
    switch (status) {
      case DebugEventStatus.SUCCESS:
        return 'success';
      case DebugEventStatus.FAILURE:
        return 'error';
      case DebugEventStatus.WARNING:
        return 'warning';
      case DebugEventStatus.INFO:
        return 'info';
      case DebugEventStatus.IN_PROGRESS:
        return 'primary';
      default:
        return 'default';
    }
  };
  
  // Get event icon
  const getEventIcon = (type: DebugEventType, status: DebugEventStatus) => {
    switch (type) {
      case DebugEventType.ERROR_DETECTED:
        return <ErrorIcon color="error" />;
      case DebugEventType.PATCH_GENERATED:
        return <CodeIcon color="info" />;
      case DebugEventType.PATCH_APPLIED:
        return status === DebugEventStatus.SUCCESS ? 
          <CheckCircleIcon color="success" /> : 
          <ErrorIcon color="error" />;
      case DebugEventType.PATCH_ROLLBACK:
        return <HistoryIcon color="warning" />;
      case DebugEventType.ML_CLASSIFICATION:
        return <AutoFixHighIcon color="primary" />;
      case DebugEventType.SESSION_CREATED:
      case DebugEventType.SESSION_UPDATED:
        return <BugReportIcon color="info" />;
      default:
        return <BugReportIcon />;
    }
  };
  
  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };
  
  // Handle refresh
  const handleRefresh = () => {
    // In a real implementation, this would fetch the latest debug events
    // For now, we'll just clear the events to simulate a refresh
    clearEvents();
  };
  
  // Toggle expanded event
  const toggleExpanded = (eventId: string) => {
    setExpandedEvent(prev => 
      prev === eventId ? null : eventId
    );
  };
  
  // Toggle notifications
  const toggleNotifications = () => {
    setNotificationsEnabled(prev => !prev);
  };
  
  return (
    <Card sx={{ height, display: 'flex', flexDirection: 'column' }}>
      <CardHeader
        title={
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <BugReportIcon sx={{ mr: 1 }} />
            <Typography variant="h6">{title}</Typography>
          </Box>
        }
        action={
          <Box>
            <Tooltip title={notificationsEnabled ? "Disable Notifications" : "Enable Notifications"}>
              <IconButton onClick={toggleNotifications}>
                {notificationsEnabled ? <NotificationsIcon /> : <NotificationsOffIcon />}
              </IconButton>
            </Tooltip>
            <Tooltip title="Refresh">
              <IconButton onClick={handleRefresh}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        }
      />
      <CardContent sx={{ flex: 1, overflow: 'auto', p: 0 }}>
        {events.length === 0 ? (
          <Box sx={{ p: 2, textAlign: 'center' }}>
            <Typography color="textSecondary">No debug activity yet</Typography>
          </Box>
        ) : (
          <List disablePadding>
            {events.map((event, index) => (
              <React.Fragment key={event.eventId}>
                <ListItem
                  alignItems="flex-start"
                  sx={{
                    p: 2,
                    cursor: 'pointer',
                    '&:hover': {
                      backgroundColor: theme => theme.palette.action.hover
                    }
                  }}
                  onClick={() => toggleExpanded(event.eventId)}
                >
                  <ListItemIcon>
                    {getEventIcon(event.type, event.status)}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                          {event.title}
                        </Typography>
                        <Chip
                          label={event.status}
                          color={getStatusColor(event.status)}
                          size="small"
                          sx={{ ml: 2 }}
                        />
                        <Box sx={{ flex: 1 }} />
                        {expandedEvent === event.eventId ? 
                          <ExpandLessIcon /> : <ExpandMoreIcon />}
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                          {event.description.length > 100 && expandedEvent !== event.eventId
                            ? `${event.description.substring(0, 100)}...`
                            : event.description}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {formatDate(event.timestamp)}
                        </Typography>
                        <Typography variant="caption" color="textSecondary" sx={{ ml: 2 }}>
                          Session: {event.sessionId.substring(0, 8)}
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
                
                <Collapse in={expandedEvent === event.eventId} timeout="auto" unmountOnExit>
                  <Box sx={{ p: 2, pl: 9, bgcolor: 'background.paper' }}>
                    {showDetails && event.details && (
                      <>
                        {event.type === DebugEventType.ERROR_DETECTED && event.details?.errorMessage && (
                          <Box sx={{ mb: 2 }}>
                            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                              Error Details
                            </Typography>
                            <Typography variant="body2" sx={{ mb: 1 }}>
                              {event.details.errorMessage}
                            </Typography>
                            {event.details.errorType && (
                              <Typography variant="body2" sx={{ mb: 1 }}>
                                Type: {event.details.errorType}
                              </Typography>
                            )}
                            {event.details.affectedFiles && event.details.affectedFiles.length > 0 && (
                              <Box sx={{ mt: 1 }}>
                                <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                                  Affected Files
                                </Typography>
                                <Box component="ul" sx={{ pl: 2, mt: 0 }}>
                                  {event.details.affectedFiles.map((file, fileIndex) => (
                                    <li key={fileIndex}>
                                      <Typography variant="body2">{file}</Typography>
                                    </li>
                                  ))}
                                </Box>
                              </Box>
                            )}
                          </Box>
                        )}
                        
                        {event.type === DebugEventType.PATCH_GENERATED && event.details && (
                          <Box sx={{ mb: 2 }}>
                            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                              Patch Details
                            </Typography>
                            {event.details.patchDescription && (
                              <Typography variant="body2" sx={{ mb: 1 }}>
                                {event.details.patchDescription}
                              </Typography>
                            )}
                            {event.details.affectedFiles && event.details.affectedFiles.length > 0 && (
                              <Box sx={{ mt: 1 }}>
                                <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                                  Files to Modify
                                </Typography>
                                <Box component="ul" sx={{ pl: 2, mt: 0 }}>
                                  {event.details.affectedFiles.map((file, fileIndex) => (
                                    <li key={fileIndex}>
                                      <Typography variant="body2">{file}</Typography>
                                    </li>
                                  ))}
                                </Box>
                              </Box>
                            )}
                            {event.details.patchCode && (
                              <Box sx={{ mt: 1 }}>
                                <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                                  Patch Code
                                </Typography>
                                <Box 
                                  sx={{ 
                                    p: 1, 
                                    bgcolor: 'background.default', 
                                    borderRadius: 1,
                                    maxHeight: 200,
                                    overflow: 'auto',
                                    fontFamily: 'monospace',
                                    fontSize: '0.875rem',
                                    whiteSpace: 'pre-wrap'
                                  }}
                                >
                                  {event.details.patchCode}
                                </Box>
                              </Box>
                            )}
                            <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                              <Button 
                                variant="contained" 
                                color="primary" 
                                size="small"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  // In a real implementation, this would apply the patch
                                  console.log(`Applying patch ${event.details?.patchId}`);
                                }}
                              >
                                Apply Patch
                              </Button>
                              <Button 
                                variant="outlined" 
                                color="primary" 
                                size="small"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  // In a real implementation, this would show the patch diff
                                  console.log(`Viewing diff for patch ${event.details?.patchId}`);
                                }}
                              >
                                View Diff
                              </Button>
                            </Box>
                          </Box>
                        )}
                        
                        {event.type === DebugEventType.ML_CLASSIFICATION && event.details?.mlClassification && (
                          <Box sx={{ mb: 2 }}>
                            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                              ML Classification
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                              <Typography variant="body2" sx={{ mr: 1 }}>
                                Category: {event.details.mlClassification.category}
                              </Typography>
                              <Chip 
                                label={`${Math.round(event.details.mlClassification.confidence * 100)}% confidence`}
                                size="small"
                                color={event.details.mlClassification.confidence > 0.8 ? 'success' : 'warning'}
                              />
                            </Box>
                            <Box sx={{ width: '100%', mb: 2 }}>
                              <LinearProgress 
                                variant="determinate" 
                                value={event.details.mlClassification.confidence * 100}
                                color={event.details.mlClassification.confidence > 0.8 ? 'success' : 'warning'}
                                sx={{ height: 8, borderRadius: 4 }}
                              />
                            </Box>
                            {event.details.mlClassification.possibleCauses && (
                              <Box sx={{ mt: 1 }}>
                                <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                                  Possible Causes
                                </Typography>
                                <Box component="ul" sx={{ pl: 2, mt: 0 }}>
                                  {event.details.mlClassification.possibleCauses.map((cause, causeIndex) => (
                                    <li key={causeIndex}>
                                      <Typography variant="body2">{cause}</Typography>
                                    </li>
                                  ))}
                                </Box>
                              </Box>
                            )}
                          </Box>
                        )}
                      </>
                    )}
                    
                    {onEventClick && (
                      <Button 
                        variant="outlined" 
                        color="primary" 
                        size="small" 
                        sx={{ mt: 2 }}
                        onClick={(e) => {
                          e.stopPropagation();
                          onEventClick(event.eventId, event.sessionId);
                        }}
                      >
                        View Details
                      </Button>
                    )}
                  </Box>
                </Collapse>
                
                {index < events.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  );
};

export default DebugActivityFeed;
