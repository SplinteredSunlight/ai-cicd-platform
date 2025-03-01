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
  Refresh as RefreshIcon,
  Security as SecurityIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useSecurityStore, useSecurityWebSocket } from '../../stores/security.store';
import { format } from 'date-fns';

export default function SecurityPage() {
  // Initialize WebSocket listeners
  useSecurityWebSocket();
  const {
    vulnerabilities,
    scans,
    selectedScan,
    isLoading,
    error,
    fetchVulnerabilities,
    fetchScans,
    startScan,
    getScanDetails,
  } = useSecurityStore();

  useEffect(() => {
    fetchVulnerabilities();
    fetchScans();
  }, [fetchVulnerabilities, fetchScans]);

  const handleStartScan = async () => {
    await startScan();
  };

  const handleSelectScan = async (scanId: string) => {
    await getScanDetails(scanId);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'error';
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Security</Typography>
        <Button
          variant="contained"
          startIcon={<SecurityIcon />}
          onClick={handleStartScan}
          disabled={isLoading}
        >
          Start New Scan
        </Button>
      </Box>

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
              <Typography variant="h6">Vulnerabilities</Typography>
              <IconButton
                onClick={() => fetchVulnerabilities()}
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
                    <TableCell>Title</TableCell>
                    <TableCell>Severity</TableCell>
                    <TableCell>Component</TableCell>
                    <TableCell>Fix Available</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {vulnerabilities.map((vuln) => (
                    <TableRow key={vuln.id}>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <WarningIcon
                            fontSize="small"
                            sx={{
                              mr: 1,
                              color: `${getSeverityColor(vuln.severity)}.main`,
                            }}
                          />
                          {vuln.title}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={vuln.severity}
                          color={getSeverityColor(vuln.severity)}
                        />
                      </TableCell>
                      <TableCell>{vuln.affected_component}</TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={vuln.fix_available ? 'Yes' : 'No'}
                          color={vuln.fix_available ? 'success' : 'default'}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Security Scans</Typography>
              <IconButton
                onClick={() => fetchScans()}
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
                    <TableCell>Status</TableCell>
                    <TableCell>Vulnerabilities</TableCell>
                    <TableCell>Started</TableCell>
                    <TableCell>Completed</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {scans.map((scan) => (
                    <TableRow
                      key={scan.id}
                      selected={selectedScan?.id === scan.id}
                      onClick={() => handleSelectScan(scan.id)}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell>
                        <Chip
                          size="small"
                          label={scan.status}
                          color={
                            scan.status === 'completed'
                              ? 'success'
                              : scan.status === 'failed'
                              ? 'error'
                              : 'default'
                          }
                        />
                      </TableCell>
                      <TableCell>{scan.vulnerabilities_found}</TableCell>
                      <TableCell>
                        {format(new Date(scan.started_at), 'PPp')}
                      </TableCell>
                      <TableCell>
                        {scan.completed_at
                          ? format(new Date(scan.completed_at), 'PPp')
                          : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
