import React, { useState, useEffect } from 'react';
import { useWebSocketCategory } from '../../hooks/useWebSocket';
import { EventCategory, EventPriority } from '../../services/websocket.service';
import { 
  Box, 
  Card, 
  CardContent, 
  CardHeader, 
  Typography, 
  IconButton, 
  Tooltip, 
  List, 
  ListItem, 
  ListItemText, 
  ListItemIcon, 
  Divider, 
  Chip, 
  Badge,
  Collapse,
  Button
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import SecurityIcon from '@mui/icons-material/Security';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';
import InfoIcon from '@mui/icons-material/Info';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import NotificationsIcon from '@mui/icons-material/Notifications';
import NotificationsOffIcon from '@mui/icons-material/NotificationsOff';

// Vulnerability severity levels
export enum VulnerabilitySeverity {
  CRITICAL = 'critical',
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low',
  INFO = 'info'
}

// Vulnerability data interface
interface Vulnerability {
  vulnerabilityId: string;
  title: string;
  description: string;
  severity: VulnerabilitySeverity;
  cveId?: string;
  affectedComponent?: string;
  detectedAt: string;
  status: 'open' | 'in_progress' | 'resolved' | 'ignored';
  remediation?: {
    description: string;
    steps?: string[];
    automatedFix?: boolean;
  };
  references?: {
    url: string;
    title: string;
  }[];
}

interface SecurityAlertsComponentProps {
  title?: string;
  maxItems?: number;
  height?: number | string;
  showRemediation?: boolean;
  onVulnerabilityClick?: (vulnerabilityId: string) => void;
}

const SecurityAlertsComponent: React.FC<SecurityAlertsComponentProps> = ({
  title = 'Security Alerts',
  maxItems = 5,
  height = 400,
  showRemediation = true,
  onVulnerabilityClick
}) => {
  // Subscribe to security category events
  const { events: securityEvents, clearEvents } = useWebSocketCategory(EventCategory.SECURITY);
  
  // State for vulnerabilities
  const [vulnerabilities, setVulnerabilities] = useState<Vulnerability[]>([]);
  const [expandedVulnerability, setExpandedVulnerability] = useState<string | null>(null);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  
  // Process security events to update vulnerabilities
  useEffect(() => {
    if (securityEvents.length === 0 || !notificationsEnabled) return;
    
    // Process events to update vulnerabilities
    securityEvents.forEach(event => {
      if (event.event_type === 'security_vulnerability_detected') {
        const vulnerability = event.data.vulnerability as Vulnerability;
        setVulnerabilities(prev => {
          // Add new vulnerability or update existing one
          const exists = prev.some(v => v.vulnerabilityId === vulnerability.vulnerabilityId);
          if (exists) {
            return prev.map(v => v.vulnerabilityId === vulnerability.vulnerabilityId ? vulnerability : v);
          } else {
            return [vulnerability, ...prev].slice(0, maxItems);
          }
        });
      } else if (event.event_type === 'security_vulnerability_updated') {
        const vulnerability = event.data.vulnerability as Vulnerability;
        setVulnerabilities(prev => 
          prev.map(v => v.vulnerabilityId === vulnerability.vulnerabilityId ? vulnerability : v)
        );
      }
    });
  }, [securityEvents, maxItems, notificationsEnabled]);
  
  // Get severity color
  const getSeverityColor = (severity: VulnerabilitySeverity) => {
    switch (severity) {
      case VulnerabilitySeverity.CRITICAL:
        return 'error';
      case VulnerabilitySeverity.HIGH:
        return 'error';
      case VulnerabilitySeverity.MEDIUM:
        return 'warning';
      case VulnerabilitySeverity.LOW:
        return 'info';
      case VulnerabilitySeverity.INFO:
        return 'default';
      default:
        return 'default';
    }
  };
  
  // Get severity icon
  const getSeverityIcon = (severity: VulnerabilitySeverity) => {
    switch (severity) {
      case VulnerabilitySeverity.CRITICAL:
      case VulnerabilitySeverity.HIGH:
        return <ErrorIcon color="error" />;
      case VulnerabilitySeverity.MEDIUM:
        return <WarningIcon color="warning" />;
      case VulnerabilitySeverity.LOW:
      case VulnerabilitySeverity.INFO:
        return <InfoIcon color="info" />;
      default:
        return <InfoIcon />;
    }
  };
  
  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };
  
  // Handle refresh
  const handleRefresh = () => {
    // In a real implementation, this would fetch the latest vulnerabilities
    // For now, we'll just clear the events to simulate a refresh
    clearEvents();
  };
  
  // Toggle expanded vulnerability
  const toggleExpanded = (vulnerabilityId: string) => {
    setExpandedVulnerability(prev => 
      prev === vulnerabilityId ? null : vulnerabilityId
    );
  };
  
  // Toggle notifications
  const toggleNotifications = () => {
    setNotificationsEnabled(prev => !prev);
  };
  
  // Count vulnerabilities by severity
  const criticalCount = vulnerabilities.filter(v => v.severity === VulnerabilitySeverity.CRITICAL).length;
  const highCount = vulnerabilities.filter(v => v.severity === VulnerabilitySeverity.HIGH).length;
  const mediumCount = vulnerabilities.filter(v => v.severity === VulnerabilitySeverity.MEDIUM).length;
  const lowCount = vulnerabilities.filter(v => v.severity === VulnerabilitySeverity.LOW).length;
  
  return (
    <Card sx={{ height, display: 'flex', flexDirection: 'column' }}>
      <CardHeader
        title={
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <SecurityIcon sx={{ mr: 1 }} />
            <Typography variant="h6">{title}</Typography>
            <Box sx={{ ml: 2, display: 'flex', gap: 1 }}>
              {criticalCount > 0 && (
                <Chip 
                  label={`${criticalCount} Critical`} 
                  color="error" 
                  size="small" 
                />
              )}
              {highCount > 0 && (
                <Chip 
                  label={`${highCount} High`} 
                  color="error" 
                  size="small" 
                  variant="outlined"
                />
              )}
              {mediumCount > 0 && (
                <Chip 
                  label={`${mediumCount} Medium`} 
                  color="warning" 
                  size="small" 
                  variant="outlined"
                />
              )}
            </Box>
          </Box>
        }
        action={
          <Box>
            <Tooltip title={notificationsEnabled ? "Disable Notifications" : "Enable Notifications"}>
              <IconButton onClick={toggleNotifications}>
                {notificationsEnabled ? <NotificationsIcon /> : <NotificationsOffIcon />}
              </IconButton>
            </Tooltip>
            <Tooltip title="Refresh">
              <IconButton onClick={handleRefresh}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        }
      />
      <CardContent sx={{ flex: 1, overflow: 'auto', p: 0 }}>
        {vulnerabilities.length === 0 ? (
          <Box sx={{ p: 2, textAlign: 'center' }}>
            <Typography color="textSecondary">No security vulnerabilities detected</Typography>
          </Box>
        ) : (
          <List disablePadding>
            {vulnerabilities.map((vulnerability, index) => (
              <React.Fragment key={vulnerability.vulnerabilityId}>
                <ListItem
                  alignItems="flex-start"
                  sx={{
                    p: 2,
                    cursor: 'pointer',
                    '&:hover': {
                      backgroundColor: theme => theme.palette.action.hover
                    }
                  }}
                  onClick={() => toggleExpanded(vulnerability.vulnerabilityId)}
                >
                  <ListItemIcon>
                    {getSeverityIcon(vulnerability.severity)}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                          {vulnerability.title}
                        </Typography>
                        <Chip
                          label={vulnerability.severity}
                          color={getSeverityColor(vulnerability.severity)}
                          size="small"
                          sx={{ ml: 2 }}
                        />
                        {vulnerability.cveId && (
                          <Chip
                            label={vulnerability.cveId}
                            size="small"
                            variant="outlined"
                            sx={{ ml: 1 }}
                          />
                        )}
                        <Box sx={{ flex: 1 }} />
                        {expandedVulnerability === vulnerability.vulnerabilityId ? 
                          <ExpandLessIcon /> : <ExpandMoreIcon />}
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                          {vulnerability.description.length > 100 && expandedVulnerability !== vulnerability.vulnerabilityId
                            ? `${vulnerability.description.substring(0, 100)}...`
                            : vulnerability.description}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          Detected: {formatDate(vulnerability.detectedAt)}
                        </Typography>
                        {vulnerability.affectedComponent && (
                          <Typography variant="caption" color="textSecondary" sx={{ ml: 2 }}>
                            Component: {vulnerability.affectedComponent}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
                
                <Collapse in={expandedVulnerability === vulnerability.vulnerabilityId} timeout="auto" unmountOnExit>
                  <Box sx={{ p: 2, pl: 9, bgcolor: 'background.paper' }}>
                    {showRemediation && vulnerability.remediation && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                          Remediation
                        </Typography>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          {vulnerability.remediation.description}
                        </Typography>
                        {vulnerability.remediation.steps && (
                          <Box component="ol" sx={{ pl: 2, mt: 1 }}>
                            {vulnerability.remediation.steps.map((step, stepIndex) => (
                              <li key={stepIndex}>
                                <Typography variant="body2">{step}</Typography>
                              </li>
                            ))}
                          </Box>
                        )}
                        {vulnerability.remediation.automatedFix && (
                          <Button 
                            variant="contained" 
                            color="primary" 
                            size="small" 
                            sx={{ mt: 1 }}
                            onClick={(e) => {
                              e.stopPropagation();
                              // In a real implementation, this would trigger the automated fix
                              console.log(`Applying automated fix for ${vulnerability.vulnerabilityId}`);
                            }}
                          >
                            Apply Automated Fix
                          </Button>
                        )}
                      </Box>
                    )}
                    
                    {vulnerability.references && vulnerability.references.length > 0 && (
                      <Box>
                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                          References
                        </Typography>
                        <Box component="ul" sx={{ pl: 2 }}>
                          {vulnerability.references.map((reference, refIndex) => (
                            <li key={refIndex}>
                              <Typography variant="body2">
                                <a 
                                  href={reference.url} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  {reference.title}
                                </a>
                              </Typography>
                            </li>
                          ))}
                        </Box>
                      </Box>
                    )}
                    
                    {onVulnerabilityClick && (
                      <Button 
                        variant="outlined" 
                        color="primary" 
                        size="small" 
                        sx={{ mt: 2 }}
                        onClick={(e) => {
                          e.stopPropagation();
                          onVulnerabilityClick(vulnerability.vulnerabilityId);
                        }}
                      >
                        View Details
                      </Button>
                    )}
                  </Box>
                </Collapse>
                
                {index < vulnerabilities.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  );
};

export default SecurityAlertsComponent;
