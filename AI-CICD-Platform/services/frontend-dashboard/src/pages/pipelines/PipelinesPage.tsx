import { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  PlayArrow as RunIcon,
  CheckCircle as ValidateIcon,
} from '@mui/icons-material';
import { usePipelineStore, usePipelineWebSocket } from '../../stores/pipeline.store';
import { format } from 'date-fns';

export default function PipelinesPage() {
  const {
    pipelines,
    isLoading,
    error,
    fetchPipelines,
    generatePipeline,
    validatePipeline,
    executePipeline,
  } = usePipelineStore();

  const [openDialog, setOpenDialog] = useState(false);
  const [repository, setRepository] = useState('');
  const [branch, setBranch] = useState('');

  // Initialize WebSocket listeners
  usePipelineWebSocket();

  useEffect(() => {
    fetchPipelines();
  }, [fetchPipelines]);

  const handleGeneratePipeline = async () => {
    await generatePipeline(repository, branch);
    setOpenDialog(false);
    setRepository('');
    setBranch('');
  };

  const handleValidatePipeline = async (pipelineId: string) => {
    await validatePipeline(pipelineId);
  };

  const handleExecutePipeline = async (pipelineId: string) => {
    await executePipeline(pipelineId);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Pipelines</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpenDialog(true)}
        >
          New Pipeline
        </Button>
      </Box>

      {error && (
        <Card sx={{ mb: 3, bgcolor: 'error.light' }}>
          <CardContent>
            <Typography color="error">{error}</Typography>
          </CardContent>
        </Card>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Repository</TableCell>
              <TableCell>Branch</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Last Updated</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {pipelines.map((pipeline) => (
              <TableRow key={pipeline.id}>
                <TableCell>{pipeline.name}</TableCell>
                <TableCell>{pipeline.repository}</TableCell>
                <TableCell>{pipeline.branch}</TableCell>
                <TableCell>{pipeline.status}</TableCell>
                <TableCell>
                  {format(new Date(pipeline.updated_at), 'PPp')}
                </TableCell>
                <TableCell align="right">
                  <IconButton
                    color="primary"
                    onClick={() => handleValidatePipeline(pipeline.id)}
                    disabled={isLoading}
                  >
                    <ValidateIcon />
                  </IconButton>
                  <IconButton
                    color="secondary"
                    onClick={() => handleExecutePipeline(pipeline.id)}
                    disabled={isLoading || pipeline.status === 'running'}
                  >
                    <RunIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>Generate New Pipeline</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Repository URL"
                value={repository}
                onChange={(e) => setRepository(e.target.value)}
                placeholder="https://github.com/username/repo"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Branch"
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                placeholder="main"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button
            onClick={handleGeneratePipeline}
            variant="contained"
            disabled={!repository || !branch || isLoading}
          >
            Generate
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
