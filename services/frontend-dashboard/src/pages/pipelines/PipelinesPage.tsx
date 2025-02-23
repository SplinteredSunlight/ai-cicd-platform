import { useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { format } from 'date-fns';
import { usePipelineStore } from '../../stores/pipeline.store';

const STATUS_CONFIG = {
  pending: { color: 'default', label: 'Pending' },
  running: { color: 'info', label: 'Running' },
  completed: { color: 'success', label: 'Completed' },
  failed: { color: 'error', label: 'Failed' },
} as const;

export default function PipelinesPage() {
  const { pipelines, isLoading, error, fetchPipelines } = usePipelineStore();

  useEffect(() => {
    fetchPipelines();
  }, [fetchPipelines]);

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

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Pipelines</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            // TODO: Implement pipeline creation dialog
          }}
        >
          New Pipeline
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Updated</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {pipelines.map((pipeline) => {
              const status = STATUS_CONFIG[pipeline.status];
              return (
                <TableRow key={pipeline.id}>
                  <TableCell>{pipeline.name}</TableCell>
                  <TableCell>
                    <Chip
                      label={status.label}
                      color={status.color}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {format(new Date(pipeline.created_at), 'MMM d, yyyy HH:mm')}
                  </TableCell>
                  <TableCell>
                    {format(new Date(pipeline.updated_at), 'MMM d, yyyy HH:mm')}
                  </TableCell>
                  <TableCell align="right">
                    <Button
                      size="small"
                      onClick={() => {
                        // TODO: Implement pipeline details view
                      }}
                    >
                      View Details
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
            {pipelines.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <Typography variant="body2" color="text.secondary">
                    No pipelines found
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
