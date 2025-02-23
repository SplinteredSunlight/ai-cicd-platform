import { Box, Grid, Typography, Chip, Tooltip } from '@mui/material';
import {
  CheckCircle as HealthyIcon,
  Warning as DegradedIcon,
  Error as DownIcon,
} from '@mui/icons-material';
import { ServiceHealth as ServiceHealthType } from '../../../config/api';
import { format } from 'date-fns';

interface ServiceHealthProps {
  services: Record<string, ServiceHealthType>;
}

const STATUS_CONFIG = {
  healthy: {
    icon: HealthyIcon,
    color: 'success',
    label: 'Healthy',
  },
  degraded: {
    icon: DegradedIcon,
    color: 'warning',
    label: 'Degraded',
  },
  down: {
    icon: DownIcon,
    color: 'error',
    label: 'Down',
  },
} as const;

export default function ServiceHealth({ services }: ServiceHealthProps) {
  return (
    <Grid container spacing={3}>
      {Object.entries(services).map(([serviceName, health]) => {
        const config = STATUS_CONFIG[health.status];
        const StatusIcon = config.icon;

        return (
          <Grid item xs={12} sm={6} md={4} key={serviceName}>
            <Box
              sx={{
                p: 2,
                border: 1,
                borderColor: 'divider',
                borderRadius: 1,
                bgcolor: 'background.paper',
              }}
            >
              {/* Service Name and Status */}
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Typography
                  variant="subtitle1"
                  component="div"
                  sx={{ flexGrow: 1, fontWeight: 'medium' }}
                >
                  {serviceName}
                </Typography>
                <Chip
                  icon={<StatusIcon />}
                  label={config.label}
                  color={config.color}
                  size="small"
                />
              </Box>

              {/* Metrics */}
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Response Time: {health.response_time.toFixed(2)}ms
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Error Rate: {(health.error_rate * 100).toFixed(1)}%
                </Typography>
              </Box>

              {/* Last Error (if any) */}
              {health.last_error && (
                <Tooltip title={health.last_error} arrow>
                  <Typography
                    variant="body2"
                    color="error"
                    sx={{
                      mt: 1,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    Last Error: {health.last_error}
                  </Typography>
                </Tooltip>
              )}

              {/* Last Checked */}
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ display: 'block', mt: 1 }}
              >
                Last checked: {format(new Date(health.last_checked), 'HH:mm:ss')}
              </Typography>
            </Box>
          </Grid>
        );
      })}
    </Grid>
  );
}
