import { Box, Paper, Typography } from '@mui/material';
import { TrendingUp as UpIcon, TrendingDown as DownIcon } from '@mui/icons-material';

interface StatusCardProps {
  title: string;
  value: number;
  change: number;
  unit?: string;
  subtitle?: string;
}

export default function StatusCard({
  title,
  value,
  change,
  unit = '',
  subtitle,
}: StatusCardProps) {
  const isPositive = change >= 0;
  const changeColor = isPositive ? 'success.main' : 'error.main';
  const Icon = isPositive ? UpIcon : DownIcon;
  const changeText = `${isPositive ? '+' : ''}${change}%`;

  return (
    <Paper
      sx={{
        p: 2,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
        {title}
      </Typography>

      <Box sx={{ display: 'flex', alignItems: 'baseline', mb: 1 }}>
        <Typography variant="h4" component="span">
          {value}
          {unit && (
            <Typography variant="h6" component="span" color="text.secondary">
              {unit}
            </Typography>
          )}
        </Typography>
      </Box>

      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          mt: 'auto',
        }}
      >
        <Icon
          sx={{
            mr: 0.5,
            fontSize: '1.2rem',
            color: changeColor,
          }}
        />
        <Typography
          variant="body2"
          sx={{
            color: changeColor,
            mr: 1,
          }}
        >
          {changeText}
        </Typography>
        {subtitle && (
          <Typography variant="caption" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </Box>
    </Paper>
  );
}
