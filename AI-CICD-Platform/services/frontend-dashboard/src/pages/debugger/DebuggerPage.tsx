import { useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import {
  BugReport as DebugIcon,
  Refresh as RefreshIcon,
  Check as ApplyIcon,
  Undo as RollbackIcon,
} from '@mui/icons-material';
import { useDebugStore } from '../../stores/debug.store';
import { format } from 'date-fns';

export default function DebuggerPage() {
  const {
    sessions,
    selectedSession,
    isLoading,
    error,
    fetchSessions,
    getSession,
    analyzeError,
    applyPatch,
    rollbackPatch,
  } = useDebugStore();

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const handleSelectSession = async (sessionId: string) => {
    await getSession(sessionId);
  };

  const handleAnalyzeError = async (errorId: string) => {
    await analyzeError(errorId);
  };

  const handleApplyPatch = async (sessionId: string, patchId: string) => {
    await applyPatch(sessionId, patchId);
  };

  const handleRollbackPatch = async (sessionId: string, patchId: string) => {
    await rollbackPatch(sessionId, patchId);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Self-Healing Debugger
      </Typography>

      {error && (
        <Card sx={{ mb: 3, bgcolor: 'error.light' }}>
          <CardContent>
            <Typography color="error">{error}</Typography>
          </CardContent>
        </Card>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Debug Sessions</Typography>
              <IconButton
                onClick={() => fetchSessions()}
                disabled={isLoading}
                sx={{ ml: 'auto' }}
              >
                <RefreshIcon />
              </IconButton>
            </Box>

            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Pipeline</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {sessions.map((session) => (
                    <TableRow
                      key={session.id}
                      selected={selectedSession?.id === session.id}
                    >
                      <TableCell>{session.pipeline_id}</TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={session.status}
                          color={
                            session.status === 'completed'
                              ? 'success'
                              : session.status === 'failed'
                              ? 'error'
                              : 'default'
                          }
                        />
                      </TableCell>
                      <TableCell>
                        {format(new Date(session.created_at), 'PPp')}
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={() => handleSelectSession(session.id)}
                          disabled={isLoading}
                        >
                          <DebugIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          {selectedSession && (
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Session Details
              </Typography>

              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Errors
              </Typography>
              {selectedSession.errors.map((error) => (
                <Card key={error.id} sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="subtitle1">{error.message}</Typography>
                    <Typography color="text.secondary" sx={{ mb: 1 }}>
                      {error.category} - {error.severity}
                    </Typography>
                    {error.stack_trace && (
                      <Box
                        component="pre"
                        sx={{
                          p: 1,
                          bgcolor: 'grey.100',
                          borderRadius: 1,
                          overflow: 'auto',
                          fontSize: '0.875rem',
                        }}
                      >
                        {error.stack_trace}
                      </Box>
                    )}
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => handleAnalyzeError(error.id)}
                      disabled={isLoading}
                      sx={{ mt: 1 }}
                    >
                      Analyze Error
                    </Button>
                  </CardContent>
                </Card>
              ))}

              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Patches
              </Typography>
              {selectedSession.patches.map((patch) => (
                <Card key={patch.id} sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="subtitle1">{patch.type}</Typography>
                    <Typography color="text.secondary" sx={{ mb: 1 }}>
                      {patch.description}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      {!patch.applied && (
                        <Button
                          variant="contained"
                          size="small"
                          startIcon={<ApplyIcon />}
                          onClick={() =>
                            handleApplyPatch(selectedSession.id, patch.id)
                          }
                          disabled={isLoading}
                        >
                          Apply Patch
                        </Button>
                      )}
                      {patch.applied && patch.is_reversible && (
                        <Button
                          variant="outlined"
                          size="small"
                          color="warning"
                          startIcon={<RollbackIcon />}
                          onClick={() =>
                            handleRollbackPatch(selectedSession.id, patch.id)
                          }
                          disabled={isLoading}
                        >
                          Rollback
                        </Button>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Paper>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}
