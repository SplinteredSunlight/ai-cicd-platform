import { Paper, Box, Typography } from '@mui/material';

interface StatusCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: 'primary' | 'error' | 'warning' | 'success';
}

export default function StatusCard({ title, value, icon, color }: StatusCardProps) {
  return (
    <Paper
      sx={{
        p: 3,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          right: 0,
          p: 2,
          color: `${color}.main`,
          opacity: 0.2,
          transform: 'scale(2)',
          transformOrigin: 'top right',
        }}
      >
        {icon}
      </Box>
      
      <Typography variant="h3" component="div" sx={{ mb: 1, color: `${color}.main` }}>
        {value}
      </Typography>
      
      <Typography
        variant="subtitle2"
        component="div"
        sx={{
          color: 'text.secondary',
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
        }}
      >
        {title}
      </Typography>
    </Paper>
  );
}
