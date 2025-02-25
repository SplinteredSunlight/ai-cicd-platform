import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Chip,
  LinearProgress,
} from '@mui/material';
import { ServiceHealth as ServiceHealthType } from '../../../config/api';

interface ServiceHealthProps {
  services: Record<string, ServiceHealthType>;
}

export default function ServiceHealth({ services }: ServiceHealthProps) {
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'down':
        return 'error';
      default:
        return 'default';
    }
  };

  const getResponseTimeColor = (time: number) => {
    if (time < 100) return 'success';
    if (time < 300) return 'warning';
    return 'error';
  };

  const formatResponseTime = (time: number) => {
    return `${time.toFixed(2)}ms`;
  };

  const formatErrorRate = (rate: number) => {
    return `${(rate * 100).toFixed(2)}%`;
  };

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Service Health
      </Typography>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Service</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Response Time</TableCell>
              <TableCell>Error Rate</TableCell>
              <TableCell>Last Error</TableCell>
              <TableCell>Last Checked</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.entries(services).map(([name, health]) => (
              <TableRow key={name}>
                <TableCell>
                  <Typography variant="subtitle2">{name}</Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={health.status}
                    color={getStatusColor(health.status)}
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2">
                      {formatResponseTime(health.response_time)}
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min((health.response_time / 500) * 100, 100)}
                      color={getResponseTimeColor(health.response_time)}
                      sx={{ width: 50, height: 4, borderRadius: 2 }}
                    />
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography
                    variant="body2"
                    color={health.error_rate > 0.05 ? 'error' : 'textSecondary'}
                  >
                    {formatErrorRate(health.error_rate)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography
                    variant="body2"
                    color="error"
                    sx={{
                      maxWidth: 200,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {health.last_error || '-'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="textSecondary">
                    {new Date(health.last_checked).toLocaleString()}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
}
