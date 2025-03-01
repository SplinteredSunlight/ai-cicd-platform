import { useState, useEffect } from 'react';
import { Box, Typography, Paper, Tabs, Tab, CircularProgress, Alert } from '@mui/material';
import SwaggerUI from 'swagger-ui-react';
import 'swagger-ui-react/swagger-ui.css';
import openApiSpec from '../../config/openapi.json';

// Define the WebSocket event documentation
const websocketEvents = [
  {
    name: 'debug_session_created',
    description: 'Emitted when a new debugging session is created',
    payload: {
      session_id: 'string',
      pipeline_id: 'string',
      created_at: 'string (ISO date)',
      status: 'string'
    }
  },
  {
    name: 'debug_session_updated',
    description: 'Emitted when an existing debugging session is updated',
    payload: {
      session_id: 'string',
      status: 'string',
      updated_at: 'string (ISO date)'
    }
  },
  {
    name: 'debug_error_detected',
    description: 'Emitted when a new error is detected in a pipeline',
    payload: {
      session_id: 'string',
      error: {
        id: 'string',
        message: 'string',
        category: 'string',
        severity: 'string',
        stack_trace: 'string (optional)'
      }
    }
  },
  {
    name: 'debug_ml_classification',
    description: 'Emitted when ML classification results are available',
    payload: {
      session_id: 'string',
      error_id: 'string',
      classifications: [
        {
          category: 'string',
          confidence: 'number (0-1)',
          model: 'string'
        }
      ]
    }
  },
  {
    name: 'debug_patch_generated',
    description: 'Emitted when an auto-fix patch is generated',
    payload: {
      session_id: 'string',
      error_id: 'string',
      patch: {
        id: 'string',
        description: 'string',
        type: 'string',
        is_reversible: 'boolean'
      }
    }
  },
  {
    name: 'debug_patch_applied',
    description: 'Emitted when a patch is applied to fix an error',
    payload: {
      session_id: 'string',
      error_id: 'string',
      patch_id: 'string',
      success: 'boolean',
      message: 'string (optional)'
    }
  },
  {
    name: 'debug_patch_rollback',
    description: 'Emitted when a patch is rolled back due to issues',
    payload: {
      session_id: 'string',
      patch_id: 'string',
      success: 'boolean',
      message: 'string'
    }
  },
  {
    name: 'architecture_diagram_update',
    description: 'Emitted when architecture diagram updates are available',
    payload: {
      diagram_id: 'string',
      type: 'string (system, service, component, etc.)',
      content: 'string (Mermaid diagram definition)',
      updated_at: 'string (ISO date)'
    }
  }
];

// Define the authentication documentation
const authenticationDocs = {
  title: 'Authentication',
  description: 'The AI CI/CD Platform uses JWT (JSON Web Tokens) for authentication.',
  sections: [
    {
      title: 'Obtaining a Token',
      content: 'To obtain a JWT token, send a POST request to the /auth/login endpoint with your email and password. The response will include a token that should be included in subsequent requests.'
    },
    {
      title: 'Using the Token',
      content: 'Include the token in the Authorization header of your requests using the Bearer scheme: Authorization: Bearer <your_token>'
    },
    {
      title: 'Token Expiration',
      content: 'Tokens expire after 24 hours. You will need to obtain a new token after expiration.'
    },
    {
      title: 'Logout',
      content: 'To invalidate a token before its expiration, send a POST request to the /auth/logout endpoint with the token in the Authorization header.'
    }
  ]
};

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
      id={`api-docs-tabpanel-${index}`}
      aria-labelledby={`api-docs-tab-${index}`}
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
    id: `api-docs-tab-${index}`,
    'aria-controls': `api-docs-tabpanel-${index}`,
  };
}

export default function ApiDocsPage() {
  const [value, setValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate loading the API documentation
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
        API Documentation
      </Typography>
      <Typography variant="body1" paragraph>
        This documentation provides details about the AI CI/CD Platform API, including endpoints, request/response formats, and authentication.
      </Typography>

      <Paper sx={{ width: '100%', mb: 2 }}>
        <Tabs
          value={value}
          onChange={handleChange}
          indicatorColor="primary"
          textColor="primary"
          aria-label="API documentation tabs"
        >
          <Tab label="REST API" {...a11yProps(0)} />
          <Tab label="WebSocket Events" {...a11yProps(1)} />
          <Tab label="Authentication" {...a11yProps(2)} />
        </Tabs>

        <TabPanel value={value} index={0}>
          <SwaggerUI spec={openApiSpec} />
        </TabPanel>

        <TabPanel value={value} index={1}>
          <Typography variant="h5" gutterBottom>
            WebSocket Events
          </Typography>
          <Typography variant="body1" paragraph>
            The AI CI/CD Platform uses WebSockets for real-time updates. The following events are emitted by the server:
          </Typography>

          {websocketEvents.map((event, index) => (
            <Paper key={index} sx={{ p: 2, mb: 2 }}>
              <Typography variant="h6" gutterBottom>
                {event.name}
              </Typography>
              <Typography variant="body2" paragraph>
                {event.description}
              </Typography>
              <Typography variant="subtitle2" gutterBottom>
                Payload:
              </Typography>
              <Box
                component="pre"
                sx={{
                  p: 2,
                  backgroundColor: 'rgba(0, 0, 0, 0.04)',
                  borderRadius: 1,
                  overflow: 'auto',
                  fontSize: '0.875rem',
                }}
              >
                {JSON.stringify(event.payload, null, 2)}
              </Box>
            </Paper>
          ))}
        </TabPanel>

        <TabPanel value={value} index={2}>
          <Typography variant="h5" gutterBottom>
            {authenticationDocs.title}
          </Typography>
          <Typography variant="body1" paragraph>
            {authenticationDocs.description}
          </Typography>

          {authenticationDocs.sections.map((section, index) => (
            <Box key={index} sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                {section.title}
              </Typography>
              <Typography variant="body2" paragraph>
                {section.content}
              </Typography>
            </Box>
          ))}

          <Typography variant="h6" gutterBottom>
            Example Authentication Flow
          </Typography>
          <Box
            component="pre"
            sx={{
              p: 2,
              backgroundColor: 'rgba(0, 0, 0, 0.04)',
              borderRadius: 1,
              overflow: 'auto',
              fontSize: '0.875rem',
            }}
          >
{`// 1. Login to obtain a token
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

// Response
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "123",
      "name": "John Doe",
      "email": "user@example.com",
      "role": "admin"
    }
  }
}

// 2. Use the token in subsequent requests
GET /pipelines
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

// 3. Logout to invalidate the token
POST /auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`}
          </Box>
        </TabPanel>
      </Paper>
    </Box>
  );
}
