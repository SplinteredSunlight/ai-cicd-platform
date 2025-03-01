import { useEffect, useState } from 'react';
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
  Tabs,
  Tab,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  BugReport as DebugIcon,
  Refresh as RefreshIcon,
  Check as ApplyIcon,
  Undo as RollbackIcon,
  BarChart as ChartIcon,
  Insights as InsightsIcon,
} from '@mui/icons-material';
import MLErrorClassification from '../../components/visualizations/MLErrorClassification';
import { useDebugStore, useDebugWebSocket } from '../../stores/debug.store';
import { format } from 'date-fns';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`debugger-tabpanel-${index}`}
      aria-labelledby={`debugger-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
    </div>
  );
}

export default function DebuggerPage() {
  const [tabValue, setTabValue] = useState(0);
  const [realtimeEnabled, setRealtimeEnabled] = useState(false);
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
    mlClassifications,
    realtimeErrors,
    clearRealtimeErrors,
  } = useDebugStore();

  // Initialize WebSocket listeners
  useDebugWebSocket();

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleRealtimeToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRealtimeEnabled(event.target.checked);
    if (!event.target.checked) {
      clearRealtimeErrors();
    }
  };

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

  // Prepare data for ML visualizations
  const getErrorsForVisualization = () => {
    if (realtimeEnabled && realtimeErrors.length > 0) {
      return realtimeErrors;
    }
    
    if (selectedSession) {
      return selectedSession.errors;
    }
    
    return [];
  };

  const getMLClassificationsForVisualization = () => {
    const errors = getErrorsForVisualization();
    return errors
      .map(error => error.id)
      .filter(id => mlClassifications[id])
      .map(id => mlClassifications[id]);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4">
          Self-Healing Debugger
        </Typography>
        <Box sx={{ flexGrow: 1 }} />
        <FormControlLabel
          control={
            <Switch
              checked={realtimeEnabled}
              onChange={handleRealtimeToggle}
              color="primary"
            />
          }
          label="Real-time Mode"
        />
      </Box>

      <Tabs value={tabValue} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tab icon={<DebugIcon />} label="Debug Sessions" />
        <Tab icon={<ChartIcon />} label="ML Visualizations" />
        <Tab icon={<InsightsIcon />} label="Insights" />
      </Tabs>

      {error && (
        <Card sx={{ mb: 3, bgcolor: 'error.light' }}>
          <CardContent>
            <Typography color="error">{error}</Typography>
          </CardContent>
        </Card>
      )}

      <TabPanel value={tabValue} index={0}>
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
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <MLErrorClassification 
          errors={getErrorsForVisualization()}
          mlClassifications={getMLClassificationsForVisualization()}
          isRealTime={realtimeEnabled}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            ML-Based Error Classification Insights
          </Typography>
          <Typography paragraph>
            The ML-based error classification system analyzes errors in real-time and provides insights
            into their categories, severity, and potential causes. This helps in quickly identifying
            patterns and common issues across your CI/CD pipelines.
          </Typography>
          <Typography variant="subtitle1" gutterBottom>
            Key Benefits:
          </Typography>
          <ul>
            <li>
              <Typography>
                <strong>Early Detection:</strong> Identify potential issues before they cause pipeline failures
              </Typography>
            </li>
            <li>
              <Typography>
                <strong>Pattern Recognition:</strong> Discover recurring issues across different pipelines
              </Typography>
            </li>
            <li>
              <Typography>
                <strong>Automated Classification:</strong> Errors are automatically categorized by type, severity, and pipeline stage
              </Typography>
            </li>
            <li>
              <Typography>
                <strong>Real-time Analysis:</strong> Get immediate insights as errors occur in your pipelines
              </Typography>
            </li>
          </ul>
          <Typography paragraph>
            Switch to the ML Visualizations tab to see detailed charts and graphs of error patterns
            across your pipelines. Toggle the "Real-time Mode" switch to see live error data as it comes in.
          </Typography>
        </Paper>
      </TabPanel>
    </Box>
  );
}
