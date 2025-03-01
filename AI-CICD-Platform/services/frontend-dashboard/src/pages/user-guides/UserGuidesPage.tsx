import { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Tabs, 
  Tab, 
  CircularProgress, 
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  Card,
  CardContent,
  CardMedia,
  Grid
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Dashboard as DashboardIcon,
  PlayArrow as PipelineIcon,
  Security as SecurityIcon,
  BugReport as DebugIcon,
  Settings as SettingsIcon,
  Api as ApiIcon,
  ViewQuilt as CustomDashboardIcon,
  Info as InfoIcon,
  ArrowForward as ArrowForwardIcon
} from '@mui/icons-material';

// Define the user guides content
const dashboardGuide = {
  title: 'Dashboard',
  icon: <DashboardIcon />,
  sections: [
    {
      title: 'Overview',
      content: 'The dashboard provides a high-level overview of your CI/CD pipelines, security status, and system health. It displays real-time metrics and analytics to help you monitor your development workflow.'
    },
    {
      title: 'Real-time Metrics',
      content: 'The dashboard displays real-time metrics for your pipelines, including build success rates, deployment frequency, and average build times. These metrics are updated in real-time via WebSockets.'
    },
    {
      title: 'Pipeline Status',
      content: 'The Pipeline Status widget shows the current status of your active pipelines. You can click on a pipeline to view more details or navigate to the Pipelines page for comprehensive management.'
    },
    {
      title: 'Security Summary',
      content: 'The Security Summary widget provides an overview of security vulnerabilities detected in your codebase. It categorizes vulnerabilities by severity and shows trends over time.'
    },
    {
      title: 'Service Health',
      content: 'The Service Health widget displays the status of your services and infrastructure. It shows uptime, response times, and any active incidents.'
    },
    {
      title: 'Customizing Your Dashboard',
      content: 'You can customize your dashboard by clicking the "Customize" button in the top-right corner. This allows you to add, remove, or rearrange widgets to suit your needs. You can also create multiple custom dashboards for different purposes.'
    }
  ]
};

const customDashboardGuide = {
  title: 'Custom Dashboard',
  icon: <CustomDashboardIcon />,
  sections: [
    {
      title: 'Creating a Custom Dashboard',
      content: 'To create a custom dashboard, navigate to the Custom Dashboard page and click the "Create New Dashboard" button. Give your dashboard a name and select the widgets you want to include.'
    },
    {
      title: 'Adding Widgets',
      content: 'To add widgets to your custom dashboard, click the "Add Widget" button and select from the available widgets. You can add multiple instances of the same widget with different configurations.'
    },
    {
      title: 'Configuring Widgets',
      content: 'Each widget can be configured by clicking the gear icon in the widget header. This allows you to customize the data displayed, time ranges, and visualization options.'
    },
    {
      title: 'Arranging Widgets',
      content: 'You can drag and drop widgets to rearrange them on your dashboard. Widgets can be resized by dragging the bottom-right corner.'
    },
    {
      title: 'Saving and Sharing',
      content: 'Your custom dashboard is automatically saved as you make changes. You can share your dashboard with team members by clicking the "Share" button and selecting the users or teams you want to share with.'
    }
  ]
};

const pipelinesGuide = {
  title: 'Pipelines',
  icon: <PipelineIcon />,
  sections: [
    {
      title: 'Pipeline Management',
      content: 'The Pipelines page allows you to manage your CI/CD pipelines. You can view all pipelines, create new ones, and monitor their status.'
    },
    {
      title: 'Creating a Pipeline',
      content: 'To create a new pipeline, click the "Create Pipeline" button and follow the wizard. You\'ll need to specify your repository, build configuration, and deployment targets.'
    },
    {
      title: 'Pipeline Configuration',
      content: 'Each pipeline can be configured with custom build steps, test environments, and deployment targets. The platform supports a wide range of programming languages and frameworks.'
    },
    {
      title: 'Monitoring Builds',
      content: 'You can monitor the status of your builds in real-time. The platform provides detailed logs, test results, and performance metrics for each build.'
    },
    {
      title: 'Pipeline Analytics',
      content: 'The Pipeline Analytics section provides insights into your pipeline performance over time. You can track metrics like build success rate, average build time, and deployment frequency.'
    }
  ]
};

const securityGuide = {
  title: 'Security',
  icon: <SecurityIcon />,
  sections: [
    {
      title: 'Security Overview',
      content: 'The Security page provides a comprehensive view of security vulnerabilities in your codebase. It integrates with multiple security scanners to detect issues early in the development process.'
    },
    {
      title: 'Vulnerability Management',
      content: 'You can view and manage detected vulnerabilities, prioritize them based on severity, and track their resolution status. The platform provides detailed information about each vulnerability, including affected components and recommended fixes.'
    },
    {
      title: 'Security Policies',
      content: 'You can define security policies that are enforced during the build process. These policies can block builds with critical vulnerabilities or require approval for deployments with known issues.'
    },
    {
      title: 'Compliance Reporting',
      content: 'The platform generates compliance reports for various standards and regulations. These reports can be exported for audit purposes.'
    },
    {
      title: 'Security Integrations',
      content: 'The platform integrates with popular security tools and vulnerability databases, including OWASP, CVE, and NIST. You can configure these integrations in the Settings page.'
    }
  ]
};

const debuggerGuide = {
  title: 'Self-Healing Debugger',
  icon: <DebugIcon />,
  sections: [
    {
      title: 'Debugger Overview',
      content: 'The Self-Healing Debugger automatically detects and fixes common issues in your pipelines. It uses machine learning to classify errors and generate appropriate fixes.'
    },
    {
      title: 'Error Classification',
      content: 'The debugger classifies errors into categories like dependency issues, permission problems, syntax errors, and more. This classification helps in quickly identifying the root cause of failures.'
    },
    {
      title: 'Automatic Fixes',
      content: 'For many common issues, the debugger can generate and apply fixes automatically. These fixes are reversible and can be reviewed before application.'
    },
    {
      title: 'ML-Based Analysis',
      content: 'The platform uses machine learning models to analyze error patterns and improve classification accuracy over time. You can view the confidence scores for each classification.'
    },
    {
      title: 'Debug Sessions',
      content: 'Each debugging session is tracked and can be reviewed later. This helps in understanding recurring issues and improving your development process.'
    }
  ]
};

const settingsGuide = {
  title: 'Settings',
  icon: <SettingsIcon />,
  sections: [
    {
      title: 'User Settings',
      content: 'You can configure your user profile, notification preferences, and authentication settings in the User Settings section.'
    },
    {
      title: 'System Configuration',
      content: 'Administrators can configure system-wide settings, including integration endpoints, security policies, and resource limits.'
    },
    {
      title: 'Team Management',
      content: 'You can manage teams, assign roles, and configure access permissions in the Team Management section.'
    },
    {
      title: 'Integrations',
      content: 'The platform supports integrations with various tools and services. You can configure these integrations in the Integrations section.'
    },
    {
      title: 'Appearance',
      content: 'You can customize the appearance of the platform, including theme, layout, and widget preferences.'
    }
  ]
};

const apiDocsGuide = {
  title: 'API Documentation',
  icon: <ApiIcon />,
  sections: [
    {
      title: 'API Overview',
      content: 'The API Documentation page provides comprehensive documentation for the platform\'s REST API and WebSocket events. You can explore endpoints, request/response formats, and authentication methods.'
    },
    {
      title: 'REST API',
      content: 'The REST API section provides interactive documentation for all API endpoints. You can test endpoints directly from the documentation page.'
    },
    {
      title: 'WebSocket Events',
      content: 'The WebSocket Events section documents all events emitted by the platform\'s WebSocket server. This is useful for implementing real-time features in your applications.'
    },
    {
      title: 'Authentication',
      content: 'The Authentication section explains how to authenticate with the API using JWT tokens. It includes examples for obtaining and using tokens.'
    },
    {
      title: 'API Clients',
      content: 'The platform provides client libraries for various programming languages. You can find documentation and examples for these clients in the API Clients section.'
    }
  ]
};

const gettingStartedGuide = {
  title: 'Getting Started',
  icon: <InfoIcon />,
  sections: [
    {
      title: 'Platform Overview',
      content: 'The AI CI/CD Platform is a comprehensive solution for managing your continuous integration and continuous deployment workflows. It combines advanced AI capabilities with robust DevOps tools to streamline your development process.'
    },
    {
      title: 'Key Features',
      content: 'The platform offers several key features:\n\n- Real-time pipeline monitoring and management\n- Advanced security vulnerability detection and remediation\n- Self-healing debugger with ML-based error classification\n- Customizable dashboards for monitoring and analytics\n- Comprehensive API for integration with other tools'
    },
    {
      title: 'First Steps',
      content: 'To get started with the platform, follow these steps:\n\n1. Create your user account or sign in with your existing credentials\n2. Connect your code repositories\n3. Create your first pipeline\n4. Configure security scanning\n5. Explore the dashboard and customize it to your needs'
    },
    {
      title: 'User Interface',
      content: 'The platform\'s user interface is organized into several main sections:\n\n- Dashboard: Overview of your pipelines and system status\n- Pipelines: Detailed pipeline management\n- Security: Security vulnerability tracking and management\n- Debugger: Self-healing debugger for automatic error resolution\n- Settings: System and user configuration\n- API Docs: Documentation for the platform\'s API'
    },
    {
      title: 'Getting Help',
      content: 'If you need help using the platform, you can:\n\n- Refer to these user guides\n- Contact support through the Help menu\n- Join our community forum for discussions with other users\n- Check our knowledge base for detailed articles and tutorials'
    }
  ]
};

// Combine all guides
const allGuides = [
  gettingStartedGuide,
  dashboardGuide,
  customDashboardGuide,
  pipelinesGuide,
  securityGuide,
  debuggerGuide,
  settingsGuide,
  apiDocsGuide
];

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
      id={`user-guides-tabpanel-${index}`}
      aria-labelledby={`user-guides-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `user-guides-tab-${index}`,
    'aria-controls': `user-guides-tabpanel-${index}`,
  };
}

export default function UserGuidesPage() {
  const [value, setValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate loading the user guides
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  }, []);

  const handleChange = (_event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h4" component="h1" gutterBottom>
        User Guides
      </Typography>
      <Typography variant="body1" paragraph>
        Welcome to the AI CI/CD Platform user guides. These guides provide step-by-step instructions for using the platform's features and capabilities.
      </Typography>

      <Paper sx={{ width: '100%', mb: 2 }}>
        <Tabs
          value={value}
          onChange={handleChange}
          indicatorColor="primary"
          textColor="primary"
          aria-label="User guides tabs"
          variant="scrollable"
          scrollButtons="auto"
        >
          {allGuides.map((guide, index) => (
            <Tab 
              key={index} 
              label={guide.title} 
              icon={guide.icon} 
              iconPosition="start" 
              {...a11yProps(index)} 
            />
          ))}
        </Tabs>

        {allGuides.map((guide, index) => (
          <TabPanel key={index} value={value} index={index}>
            <Typography variant="h5" gutterBottom>
              {guide.title}
            </Typography>
            
            {index === 0 && (
              <Box sx={{ mb: 4 }}>
                <Grid container spacing={3}>
                  {allGuides.slice(1).map((featureGuide, featureIndex) => (
                    <Grid item xs={12} sm={6} md={4} key={featureIndex}>
                      <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                        <CardContent sx={{ flexGrow: 1 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                            <Box sx={{ mr: 1, color: 'primary.main' }}>
                              {featureGuide.icon}
                            </Box>
                            <Typography variant="h6" component="h3">
                              {featureGuide.title}
                            </Typography>
                          </Box>
                          <Typography variant="body2" color="text.secondary">
                            {featureGuide.sections[0].content.substring(0, 120)}...
                          </Typography>
                        </CardContent>
                        <Box sx={{ p: 2, pt: 0 }}>
                          <Button 
                            size="small" 
                            endIcon={<ArrowForwardIcon />}
                            onClick={() => setValue(featureIndex + 1)}
                          >
                            Learn More
                          </Button>
                        </Box>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </Box>
            )}

            {guide.sections.map((section, sectionIndex) => (
              <Accordion key={sectionIndex} defaultExpanded={sectionIndex === 0}>
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon />}
                  aria-controls={`panel${sectionIndex}-content`}
                  id={`panel${sectionIndex}-header`}
                >
                  <Typography variant="h6">{section.title}</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
                    {section.content}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            ))}
          </TabPanel>
        ))}
      </Paper>
    </Box>
  );
}
