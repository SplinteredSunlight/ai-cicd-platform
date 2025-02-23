import { useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Button,
  List,
  ListItem,
  ListItemText,
  Chip,
  IconButton,
  Tooltip,
  Divider,
} from '@mui/material';
import {
  PlayArrow as ApplyIcon,
  Undo as RollbackIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { useDebugStore } from '../../stores/debug.store';

export default function DebuggerPage() {
  const {
    sessions,
    activeSession,
    isLoading,
    error,
    fetchSessions,
    setActiveSession,
    applyPatch,
    rollbackPatch,
  } = useDebugStore();

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  const stats = useDebugStore.getState().getErrorStats();
  const patchingStats = useDebugStore.getState().getPatchingStats();

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Debug Sessions
      </Typography>

      {/* Stats Overview */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Errors
              </Typography>
              <Typography variant="h4">{stats.total}</Typography>
              <Box sx={{ mt: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  {stats.resolved} resolved • {stats.pending} pending
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Success Rate
              </Typography>
              <Typography variant="h4">
                {Math.round(patchingStats.success_rate * 100)}%
              </Typography>
              <Box sx={{ mt: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  {patchingStats.successful_patches} successful patches
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Active Session */}
      {activeSession && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Active Debug Session
          </Typography>
          <Typography color="text.secondary" gutterBottom>
            Pipeline: {activeSession.pipeline_id}
          </Typography>

          <Typography variant="subtitle1" sx={{ mt: 3, mb: 2 }}>
            Errors
          </Typography>
          <List>
            {activeSession.errors.map((error) => (
              <ListItem
                key={error.id}
                sx={{
                  borderBottom: '1px solid',
                  borderColor: 'divider',
                  '&:last-child': { borderBottom: 'none' },
                }}
              >
                <ListItemText
                  primary={error.message}
                  secondary={
                    <>
                      <Typography variant="body2" color="text.secondary">
                        {error.category}
                      </Typography>
                      <Chip
                        size="small"
                        label={error.severity}
                        color={
                          error.severity === 'critical'
                            ? 'error'
                            : error.severity === 'high'
                            ? 'warning'
                            : 'default'
                        }
                        sx={{ mt: 1 }}
                      />
                    </>
                  }
                />
              </ListItem>
            ))}
          </List>

          <Typography variant="subtitle1" sx={{ mt: 3, mb: 2 }}>
            Patches
          </Typography>
          <List>
            {activeSession.patches.map((patch) => (
              <ListItem
                key={patch.id}
                sx={{
                  borderBottom: '1px solid',
                  borderColor: 'divider',
                  '&:last-child': { borderBottom: 'none' },
                }}
              >
                <ListItemText
                  primary={patch.description}
                  secondary={
                    <>
                      <Typography variant="body2" color="text.secondary">
                        Type: {patch.type}
                      </Typography>
                      {patch.applied && (
                        <Box sx={{ mt: 1 }}>
                          {patch.success ? (
                            <Chip
                              size="small"
                              icon={<SuccessIcon />}
                              label="Applied Successfully"
                              color="success"
                            />
                          ) : (
                            <Chip
                              size="small"
                              icon={<ErrorIcon />}
                              label="Application Failed"
                              color="error"
                            />
                          )}
                        </Box>
                      )}
                    </>
                  }
                />
                <Box>
                  {!patch.applied ? (
                    <Tooltip title="Apply Patch">
                      <IconButton
                        onClick={() => applyPatch(patch)}
                        color="primary"
                      >
                        <ApplyIcon />
                      </IconButton>
                    </Tooltip>
                  ) : (
                    patch.is_reversible && (
                      <Tooltip title="Rollback Patch">
                        <IconButton
                          onClick={() => rollbackPatch(patch.id)}
                          color="warning"
                        >
                          <RollbackIcon />
                        </IconButton>
                      </Tooltip>
                    )
                  )}
                </Box>
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {/* Session List */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Recent Sessions
        </Typography>
        <List>
          {sessions.map((session) => (
            <ListItem
              key={session.id}
              sx={{
                borderBottom: '1px solid',
                borderColor: 'divider',
                '&:last-child': { borderBottom: 'none' },
              }}
            >
              <ListItemText
                primary={`Debug Session #${session.id}`}
                secondary={
                  <>
                    Pipeline: {session.pipeline_id}
                    <br />
                    Started: {format(new Date(session.created_at), 'PPp')}
                  </>
                }
              />
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip
                  label={session.status}
                  color={session.status === 'active' ? 'warning' : 'success'}
                  size="small"
                />
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => setActiveSession(session)}
                >
                  View Details
                </Button>
              </Box>
            </ListItem>
          ))}
        </List>
      </Paper>
    </Box>
  );
}
