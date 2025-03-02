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
  Avatar,
  Badge,
  FormControlLabel,
  Switch,
  Tooltip,
  Paper
} from '@mui/material';
import { 
  CheckCircle as ApproveIcon, 
  Cancel as RejectIcon, 
  Notifications as NotificationIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Person as PersonIcon,
  Group as GroupIcon,
  Security as SecurityIcon,
  Business as BusinessIcon,
  Comment as CommentIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { useWebSocketEvent } from '../../hooks/useWebSocket';

// Types
interface ApprovalRule {
  id: string;
  name: string;
  level: string;
  requiredApprovals: number;
  timeoutMinutes?: number;
  autoApproveCriteria?: any;
}

interface ApprovalWorkflow {
  id: string;
  name: string;
  description: string;
  rules: ApprovalRule[];
  environmentId: string;
  pipelineId: string;
  active: boolean;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
}

interface ApprovalRequest {
  id: string;
  workflowId: string;
  ruleId: string;
  deploymentId: string;
  environmentId: string;
  pipelineId: string;
  status: string;
  requestedBy: string;
  requestedAt: string;
  expiresAt?: string;
  approvals: any[];
  rejections: any[];
  comments: any[];
}

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  avatarUrl?: string;
}

// Mock data for development
const mockWorkflows: ApprovalWorkflow[] = [
  {
    id: '1',
    name: 'Production Approval Workflow',
    description: 'Approval workflow for production deployments',
    rules: [
      {
        id: '1',
        name: 'Team Lead Approval',
        level: 'team_lead',
        requiredApprovals: 1
      },
      {
        id: '2',
        name: 'Manager Approval',
        level: 'manager',
        requiredApprovals: 1
      }
    ],
    environmentId: '3', // production
    pipelineId: '1',
    active: true,
    createdAt: '2025-03-01T12:00:00Z',
    updatedAt: '2025-03-01T12:00:00Z',
    createdBy: 'user1'
  },
  {
    id: '2',
    name: 'Staging Approval Workflow',
    description: 'Approval workflow for staging deployments',
    rules: [
      {
        id: '1',
        name: 'Team Lead Approval',
        level: 'team_lead',
        requiredApprovals: 1
      }
    ],
    environmentId: '2', // staging
    pipelineId: '1',
    active: true,
    createdAt: '2025-03-01T12:00:00Z',
    updatedAt: '2025-03-01T12:00:00Z',
    createdBy: 'user1'
  }
];

const mockRequests: ApprovalRequest[] = [
  {
    id: '1',
    workflowId: '1',
    ruleId: '1',
    deploymentId: '1',
    environmentId: '3', // production
    pipelineId: '1',
    status: 'pending',
    requestedBy: 'user1',
    requestedAt: '2025-03-01T14:00:00Z',
    approvals: [],
    rejections: [],
    comments: []
  },
  {
    id: '2',
    workflowId: '1',
    ruleId: '1',
    deploymentId: '2',
    environmentId: '3', // production
    pipelineId: '1',
    status: 'approved',
    requestedBy: 'user1',
    requestedAt: '2025-03-01T13:00:00Z',
    approvals: [
      {
        userId: 'user2',
        timestamp: '2025-03-01T13:10:00Z',
        comment: 'Looks good!'
      }
    ],
    rejections: [],
    comments: [
      {
        userId: 'user2',
        comment: 'Looks good!',
        timestamp: '2025-03-01T13:10:00Z'
      }
    ]
  }
];

const mockUsers: User[] = [
  {
    id: 'user1',
    name: 'John Doe',
    email: 'john.doe@example.com',
    role: 'developer'
  },
  {
    id: 'user2',
    name: 'Jane Smith',
    email: 'jane.smith@example.com',
    role: 'team_lead'
  },
  {
    id: 'user3',
    name: 'Bob Johnson',
    email: 'bob.johnson@example.com',
    role: 'manager'
  }
];

// Component
const ApprovalWorkflow: React.FC = () => {
  const theme = useTheme();
  const { data: lastMessage } = useWebSocketEvent('approval_update');
  
  const [workflows, setWorkflows] = useState<ApprovalWorkflow[]>(mockWorkflows);
  const [requests, setRequests] = useState<ApprovalRequest[]>(mockRequests);
  const [selectedWorkflow, setSelectedWorkflow] = useState<ApprovalWorkflow | null>(null);
  const [selectedRequest, setSelectedRequest] = useState<ApprovalRequest | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  
  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState<boolean>(false);
  const [requestDetailsDialogOpen, setRequestDetailsDialogOpen] = useState<boolean>(false);
  const [commentDialogOpen, setCommentDialogOpen] = useState<boolean>(false);
  
  // Form states
  const [newWorkflow, setNewWorkflow] = useState<Partial<ApprovalWorkflow>>({
    name: '',
    description: '',
    rules: [],
    active: true
  });
  
  const [comment, setComment] = useState<string>('');
  
  // Effect to handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      try {
        if (typeof lastMessage === 'object') {
          // Handle workflow updates
          if (lastMessage.type === 'workflow_update' && lastMessage.workflow) {
            setWorkflows(prevWorkflows => {
              const index = prevWorkflows.findIndex(w => w.id === lastMessage.workflow.id);
              if (index >= 0) {
                const updatedWorkflows = [...prevWorkflows];
                updatedWorkflows[index] = lastMessage.workflow;
                return updatedWorkflows;
              }
              return [...prevWorkflows, lastMessage.workflow];
            });
          } 
          // Handle request updates
          else if (lastMessage.type === 'request_update' && lastMessage.request) {
            setRequests(prevRequests => {
              const index = prevRequests.findIndex(r => r.id === lastMessage.request.id);
              if (index >= 0) {
                const updatedRequests = [...prevRequests];
                updatedRequests[index] = lastMessage.request;
                return updatedRequests;
              }
              return [...prevRequests, lastMessage.request];
            });
          }
        }
      } catch (error) {
        console.error('Error handling WebSocket message:', error);
      }
    }
  }, [lastMessage]);
  
  // Fetch workflows
  const fetchWorkflows = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would fetch from the API
      // const response = await fetch('/api/deployment-automation/approval-workflows');
      // const data = await response.json();
      // setWorkflows(data);
      
      // For now, use mock data
      setWorkflows(mockWorkflows);
    } catch (error) {
      console.error('Error fetching workflows:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Fetch requests for a workflow
  const fetchRequests = async (workflowId: string) => {
    setLoading(true);
    try {
      // In a real implementation, this would fetch from the API
      // const response = await fetch(`/api/deployment-automation/approval-workflows/${workflowId}/requests`);
      // const data = await response.json();
      // setRequests(data);
      
      // For now, use mock data
      setRequests(mockRequests.filter(r => r.workflowId === workflowId));
    } catch (error) {
      console.error('Error fetching requests:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Create a new workflow
  const createWorkflow = async () => {
    setLoading(true);
    try {
      // In a real implementation, this would send to the API
      // const response = await fetch('/api/deployment-automation/approval-workflows', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(newWorkflow)
      // });
      // const data = await response.json();
      // setWorkflows([...workflows, data]);
      
      // For now, use mock data
      const newId = (workflows.length + 1).toString();
      const createdWorkflow: ApprovalWorkflow = {
        id: newId,
        name: newWorkflow.name || 'New Workflow',
        description: newWorkflow.description || '',
        rules: newWorkflow.rules || [],
        environmentId: newWorkflow.environmentId || '1',
        pipelineId: newWorkflow.pipelineId || '1',
        active: newWorkflow.active !== undefined ? newWorkflow.active : true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        createdBy: 'user1'
      };
      setWorkflows([...workflows, createdWorkflow]);
      
      // Reset form
      setNewWorkflow({
        name: '',
        description: '',
        rules: [],
        active: true
      });
      
      // Close dialog
      setCreateDialogOpen(false);
    } catch (error) {
      console.error('Error creating workflow:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Approve a request
  const approveRequest = async (requestId: string, comment: string = '') => {
    setLoading(true);
    try {
      // In a real implementation, this would send to the API
      // const response = await fetch(`/api/deployment-automation/approval-requests/${requestId}/approve`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ comment })
      // });
      // const data = await response.json();
      // setRequests(prevRequests => {
      //   const index = prevRequests.findIndex(r => r.id === requestId);
      //   if (index >= 0) {
      //     const updatedRequests = [...prevRequests];
      //     updatedRequests[index] = data;
      //     return updatedRequests;
      //   }
      //   return prevRequests;
      // });
      
      // For now, use mock data
      setRequests(prevRequests => {
        const index = prevRequests.findIndex(r => r.id === requestId);
        if (index >= 0) {
          const updatedRequests = [...prevRequests];
          const request = { ...updatedRequests[index] };
          
          // Add approval
          request.approvals.push({
            userId: 'user2',
            timestamp: new Date().toISOString(),
            comment
          });
          
          // Add comment if provided
          if (comment) {
            request.comments.push({
              userId: 'user2',
              comment,
              timestamp: new Date().toISOString()
            });
          }
          
          // Update status
          request.status = 'approved';
          
          updatedRequests[index] = request;
          return updatedRequests;
        }
        return prevRequests;
      });
      
      // Close dialog
      setCommentDialogOpen(false);
      setComment('');
    } catch (error) {
      console.error('Error approving request:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Reject a request
  const rejectRequest = async (requestId: string, comment: string = '') => {
    setLoading(true);
    try {
      // In a real implementation, this would send to the API
      // const response = await fetch(`/api/deployment-automation/approval-requests/${requestId}/reject`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ comment })
      // });
      // const data = await response.json();
      // setRequests(prevRequests => {
      //   const index = prevRequests.findIndex(r => r.id === requestId);
      //   if (index >= 0) {
      //     const updatedRequests = [...prevRequests];
      //     updatedRequests[index] = data;
      //     return updatedRequests;
      //   }
      //   return prevRequests;
      // });
      
      // For now, use mock data
      setRequests(prevRequests => {
        const index = prevRequests.findIndex(r => r.id === requestId);
        if (index >= 0) {
          const updatedRequests = [...prevRequests];
          const request = { ...updatedRequests[index] };
          
          // Add rejection
          request.rejections.push({
            userId: 'user2',
            timestamp: new Date().toISOString(),
            comment
          });
          
          // Add comment if provided
          if (comment) {
            request.comments.push({
              userId: 'user2',
              comment,
              timestamp: new Date().toISOString()
            });
          }
          
          // Update status
          request.status = 'rejected';
          
          updatedRequests[index] = request;
          return updatedRequests;
        }
        return prevRequests;
      });
      
      // Close dialog
      setCommentDialogOpen(false);
      setComment('');
    } catch (error) {
      console.error('Error rejecting request:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Add a comment to a request
  const addComment = async (requestId: string, comment: string) => {
    setLoading(true);
    try {
      // In a real implementation, this would send to the API
      // const response = await fetch(`/api/deployment-automation/approval-requests/${requestId}/comments`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ comment })
      // });
      // const data = await response.json();
      // setRequests(prevRequests => {
      //   const index = prevRequests.findIndex(r => r.id === requestId);
      //   if (index >= 0) {
      //     const updatedRequests = [...prevRequests];
      //     updatedRequests[index] = data;
      //     return updatedRequests;
      //   }
      //   return prevRequests;
      // });
      
      // For now, use mock data
      setRequests(prevRequests => {
        const index = prevRequests.findIndex(r => r.id === requestId);
        if (index >= 0) {
          const updatedRequests = [...prevRequests];
          const request = { ...updatedRequests[index] };
          
          // Add comment
          request.comments.push({
            userId: 'user2',
            comment,
            timestamp: new Date().toISOString()
          });
          
          updatedRequests[index] = request;
          return updatedRequests;
        }
        return prevRequests;
      });
      
      // Close dialog
      setCommentDialogOpen(false);
      setComment('');
    } catch (error) {
      console.error('Error adding comment:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Handle workflow selection
  const handleWorkflowSelect = (workflow: ApprovalWorkflow) => {
    setSelectedWorkflow(workflow);
    fetchRequests(workflow.id);
  };
  
  // Get user by ID
  const getUserById = (userId: string): User => {
    return mockUsers.find(u => u.id === userId) || {
      id: userId,
      name: 'Unknown User',
      email: 'unknown@example.com',
      role: 'unknown'
    };
  };
  
  // Get approval level icon
  const getApprovalLevelIcon = (level: string) => {
    switch (level) {
      case 'team_lead':
        return <PersonIcon />;
      case 'manager':
        return <GroupIcon />;
      case 'director':
        return <BusinessIcon />;
      case 'security':
        return <SecurityIcon />;
      default:
        return <PersonIcon />;
    }
  };
  
  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'success';
      case 'rejected':
        return 'error';
      case 'pending':
        return 'warning';
      case 'cancelled':
        return 'default';
      default:
        return 'default';
    }
  };
  
  // Render workflow card
  const renderWorkflowCard = (workflow: ApprovalWorkflow) => {
    const isSelected = selectedWorkflow?.id === workflow.id;
    
    return (
      <Card 
        key={workflow.id} 
        sx={{ 
          mb: 2, 
          cursor: 'pointer',
          border: isSelected ? `2px solid ${theme.palette.primary.main}` : 'none'
        }}
        onClick={() => handleWorkflowSelect(workflow)}
      >
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="h6">{workflow.name}</Typography>
            <Chip 
              label={workflow.active ? 'Active' : 'Inactive'} 
              size="small" 
              color={workflow.active ? 'success' : 'default'}
            />
          </Box>
          
          <Typography variant="body2" color="text.secondary" mb={2}>
            {workflow.description}
          </Typography>
          
          <Typography variant="subtitle2" gutterBottom>
            Approval Rules:
          </Typography>
          
          <List dense>
            {workflow.rules.map((rule, index) => (
              <React.Fragment key={rule.id}>
                <ListItem>
                  <ListItemText 
                    primary={rule.name}
                    secondary={`${rule.requiredApprovals} approval(s) required`}
                  />
                  <ListItemSecondaryAction>
                    <Avatar sx={{ bgcolor: theme.palette.primary.main, width: 24, height: 24 }}>
                      {getApprovalLevelIcon(rule.level)}
                    </Avatar>
                  </ListItemSecondaryAction>
                </ListItem>
                {index < workflow.rules.length - 1 && <Divider component="li" />}
              </React.Fragment>
            ))}
          </List>
        </CardContent>
      </Card>
    );
  };
  
  // Render request card
  const renderRequestCard = (request: ApprovalRequest) => {
    const user = getUserById(request.requestedBy);
    
    return (
      <Card key={request.id} sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="h6">Approval Request #{request.id}</Typography>
            <Chip 
              label={request.status} 
              size="small" 
              color={getStatusColor(request.status)}
            />
          </Box>
          
          <Typography variant="body2" color="text.secondary" mb={2}>
            Requested by: {user.name} • {new Date(request.requestedAt).toLocaleString()}
            {request.expiresAt && ` • Expires: ${new Date(request.expiresAt).toLocaleString()}`}
          </Typography>
          
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Box>
              <Chip 
                label={`${request.approvals.length} Approval(s)`}
                size="small"
                color="success"
                sx={{ mr: 1 }}
              />
              <Chip 
                label={`${request.rejections.length} Rejection(s)`}
                size="small"
                color="error"
                sx={{ mr: 1 }}
              />
              <Chip 
                label={`${request.comments.length} Comment(s)`}
                size="small"
                color="info"
              />
            </Box>
            
            <Box>
              {request.status === 'pending' && (
                <>
                  <Tooltip title="Approve">
                    <IconButton 
                      color="success"
                      onClick={() => {
                        setSelectedRequest(request);
                        setCommentDialogOpen(true);
                      }}
                    >
                      <ApproveIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Reject">
                    <IconButton 
                      color="error"
                      onClick={() => {
                        setSelectedRequest(request);
                        setCommentDialogOpen(true);
                      }}
                    >
                      <RejectIcon />
                    </IconButton>
                  </Tooltip>
                </>
              )}
              <Tooltip title="View Details">
                <IconButton 
                  color="primary"
                  onClick={() => {
                    setSelectedRequest(request);
                    setRequestDetailsDialogOpen(true);
                  }}
                >
                  <CommentIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
        </CardContent>
      </Card>
    );
  };
  
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Approval Workflows</Typography>
        <Button 
          variant="contained" 
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Create Workflow
        </Button>
      </Box>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Typography variant="h6" mb={2}>Workflows</Typography>
          {loading ? (
            <Box display="flex" justifyContent="center" my={4}>
              <CircularProgress />
            </Box>
          ) : (
            workflows.map(renderWorkflowCard)
          )}
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Typography variant="h6" mb={2}>Pending Approvals</Typography>
          {selectedWorkflow ? (
            loading ? (
              <Box display="flex" justifyContent="center" my={4}>
                <CircularProgress />
              </Box>
            ) : requests.length > 0 ? (
              requests.map(renderRequestCard)
            ) : (
              <Typography variant="body1" color="text.secondary" align="center" my={4}>
                No approval requests found for this workflow.
              </Typography>
            )
          ) : (
            <Typography variant="body1" color="text.secondary" align="center" my={4}>
              Select a workflow to view its approval requests.
            </Typography>
          )}
        </Grid>
      </Grid>
      
      {/* Create Workflow Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create Approval Workflow</DialogTitle>
        <DialogContent>
          <Box mt={2}>
            <TextField
              label="Workflow Name"
              fullWidth
              margin="normal"
              value={newWorkflow.name}
              onChange={(e) => setNewWorkflow({...newWorkflow, name: e.target.value})}
            />
            
            <TextField
              label="Description"
              fullWidth
              margin="normal"
              multiline
              rows={3}
              value={newWorkflow.description}
              onChange={(e) => setNewWorkflow({...newWorkflow, description: e.target.value})}
            />
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Environment</InputLabel>
              <Select
                value={newWorkflow.environmentId || ''}
                label="Environment"
                onChange={(e) => setNewWorkflow({...newWorkflow, environmentId: e.target.value})}
              >
                <MenuItem value="1">Development</MenuItem>
                <MenuItem value="2">Staging</MenuItem>
                <MenuItem value="3">Production</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Pipeline</InputLabel>
              <Select
                value={newWorkflow.pipelineId || ''}
                label="Pipeline"
                onChange={(e) => setNewWorkflow({...newWorkflow, pipelineId: e.target.value})}
              >
                <MenuItem value="1">Production Deployment Pipeline</MenuItem>
                <MenuItem value="2">Microservices Deployment Pipeline</MenuItem>
              </Select>
            </FormControl>
            
            <FormControlLabel
              control={
                <Switch
                  checked={newWorkflow.active !== undefined ? newWorkflow.active : true}
                  onChange={(e) => setNewWorkflow({...newWorkflow, active: e.target.checked})}
                />
              }
              label="Active"
              sx={{ mt: 2 }}
            />
            
            {/* Approval rules configuration would go here */}
            <Typography variant="subtitle1" mt={2} mb={1}>
              Approval Rules
            </Typography>
            
            <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
              <Typography variant="body2" color="text.secondary" mb={2}>
                Add approval rules to define who needs to approve deployments and in what order.
              </Typography>
              
              <Button 
                variant="outlined" 
                startIcon={<AddIcon />}
                fullWidth
              >
                Add Approval Rule
              </Button>
            </Paper>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={createWorkflow}
            disabled={!newWorkflow.name}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Request Details Dialog */}
      <Dialog open={requestDetailsDialogOpen} onClose={() => setRequestDetailsDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Approval Request Details</DialogTitle>
        <DialogContent>
          {selectedRequest && (
            <Box mt={2}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Request #{selectedRequest.id}</Typography>
                <Chip 
                  label={selectedRequest.status} 
                  color={getStatusColor(selectedRequest.status)}
                />
              </Box>
              
              <Typography variant="body2" color="text.secondary" mb={3}>
                Requested by: {getUserById(selectedRequest.requestedBy).name} • {new Date(selectedRequest.requestedAt).toLocaleString()}
                {selectedRequest.expiresAt && ` • Expires: ${new Date(selectedRequest.expiresAt).toLocaleString()}`}
              </Typography>
              
              <Typography variant="subtitle1" gutterBottom>
                Comments
              </Typography>
              
              <List>
                {selectedRequest.comments.length > 0 ? (
                  selectedRequest.comments.map((comment, index) => (
                    <React.Fragment key={index}>
                      <ListItem alignItems="flex-start">
                        <ListItemText
                          primary={getUserById(comment.userId).name}
                          secondary={
                            <>
                              <Typography component="span" variant="body2" color="text.primary">
                                {comment.comment}
                              </Typography>
                              <br />
                              <Typography component="span" variant="caption" color="text.secondary">
                                {new Date(comment.timestamp).toLocaleString()}
                              </Typography>
                            </>
                          }
                        />
                      </ListItem>
                      {index < selectedRequest.comments.length - 1 && <Divider component="li" />}
                    </React.Fragment>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary" align="center" my={2}>
                    No comments yet.
                  </Typography>
                )}
              </List>
              
              <Box mt={3}>
                <TextField
                  label="Add a comment"
                  fullWidth
                  multiline
                  rows={3}
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                />
                <Box display="flex" justifyContent="flex-end" mt={2}>
                  <Button 
                    variant="contained" 
                    onClick={() => addComment(selectedRequest.id, comment)}
                    disabled={!comment}
                  >
                    Add Comment
                  </Button>
                </Box>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRequestDetailsDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
      
      {/* Comment Dialog */}
      <Dialog open={commentDialogOpen} onClose={() => setCommentDialogOpen(false)}>
        <DialogTitle>Add Comment</DialogTitle>
        <DialogContent>
          <Box mt={2}>
            <TextField
              label="Comment"
              fullWidth
              multiline
              rows={3}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCommentDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            color="success"
            onClick={() => selectedRequest && approveRequest(selectedRequest.id, comment)}
          >
            Approve
          </Button>
          <Button 
            variant="contained" 
            color="error"
            onClick={() => selectedRequest && rejectRequest(selectedRequest.id, comment)}
          >
            Reject
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ApprovalWorkflow;
