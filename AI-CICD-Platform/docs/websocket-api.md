# WebSocket API Documentation

## Overview

The AI CI/CD Platform provides real-time updates through WebSocket connections. This document describes the WebSocket API endpoints, authentication, and event types.

## Connection

### Endpoint

```
ws://[API_HOST]/ws
```

For secure connections:

```
wss://[API_HOST]/ws
```

### Authentication

After establishing a WebSocket connection, clients must authenticate by sending an `authenticate` event with a valid JWT token:

```javascript
socket.emit('authenticate', { token: 'your-jwt-token' });
```

The server will respond with either:

- `authenticated` event with user information if authentication is successful
- `auth_error` event with an error message if authentication fails

## Event Categories

Events are organized into the following categories:

- `PIPELINE`: Events related to CI/CD pipelines
- `SECURITY`: Events related to security scans and vulnerabilities
- `DEBUG`: Events related to debugging and error handling
- `SYSTEM`: Events related to system status and metrics
- `ARCHITECTURE`: Events related to architecture diagrams and system structure
- `USER`: Events related to user actions and notifications

## Event Types

### Pipeline Events

| Event Type | Description | Data Structure |
|------------|-------------|----------------|
| `pipeline_created` | A new pipeline has been created | `{ pipelineId: string, pipeline: object }` |
| `pipeline_updated` | A pipeline has been updated | `{ pipelineId: string, pipeline: object }` |
| `pipeline_deleted` | A pipeline has been deleted | `{ pipelineId: string }` |
| `pipeline_execution_started` | A pipeline execution has started | `{ executionId: string, pipelineId: string, execution: object }` |
| `pipeline_execution_updated` | A pipeline execution has been updated | `{ executionId: string, pipelineId: string, execution: object }` |
| `pipeline_execution_completed` | A pipeline execution has completed | `{ executionId: string, pipelineId: string, execution: object }` |

### Security Events

| Event Type | Description | Data Structure |
|------------|-------------|----------------|
| `security_vulnerability_detected` | A security vulnerability has been detected | `{ vulnerabilityId: string, vulnerability: object }` |
| `security_vulnerability_updated` | A security vulnerability has been updated | `{ vulnerabilityId: string, vulnerability: object }` |
| `security_scan_started` | A security scan has started | `{ scanId: string, scan: object }` |
| `security_scan_updated` | A security scan has been updated | `{ scanId: string, scan: object }` |
| `security_scan_completed` | A security scan has completed | `{ scanId: string, scan: object }` |

### Debug Events

| Event Type | Description | Data Structure |
|------------|-------------|----------------|
| `debug_session_created` | A debug session has been created | `{ sessionId: string, session: object }` |
| `debug_session_updated` | A debug session has been updated | `{ sessionId: string, session: object }` |
| `debug_error_detected` | An error has been detected | `{ sessionId: string, errorId: string, error: object }` |
| `debug_ml_classification` | ML classification results for an error | `{ sessionId: string, errorId: string, classifications: object }` |
| `debug_patch_generated` | A patch has been generated | `{ sessionId: string, patchId: string, patch: object }` |
| `debug_patch_applied` | A patch has been applied | `{ sessionId: string, patchId: string, result: object }` |
| `debug_patch_rollback` | A patch has been rolled back | `{ sessionId: string, patchId: string, result: object }` |

### System Events

| Event Type | Description | Data Structure |
|------------|-------------|----------------|
| `system_status_update` | System status has been updated | `{ status: object }` |
| `system_metrics_update` | System metrics have been updated | `{ metrics: object }` |
| `system_alert` | A system alert has been triggered | `{ alertId: string, alert: object }` |

### Architecture Events

| Event Type | Description | Data Structure |
|------------|-------------|----------------|
| `architecture_diagram_update` | An architecture diagram has been updated | `{ diagramId: string, diagram: object }` |

## Event Priority

Events can have one of the following priority levels:

- `HIGH`: Critical events that require immediate attention
- `MEDIUM`: Important events that should be displayed prominently
- `LOW`: Informational events that can be displayed with lower prominence

## Client Implementation Example

```javascript
import { io } from 'socket.io-client';

// Connect to WebSocket server
const socket = io('wss://api.example.com/ws', {
  transports: ['websocket'],
  autoConnect: true
});

// Handle connection events
socket.on('connect', () => {
  console.log('Connected to WebSocket server');
  
  // Authenticate with JWT token
  socket.emit('authenticate', { token: 'your-jwt-token' });
});

socket.on('authenticated', (data) => {
  console.log('Authenticated successfully', data);
  
  // Subscribe to events
  setupEventListeners();
});

socket.on('auth_error', (error) => {
  console.error('Authentication failed', error);
});

socket.on('disconnect', () => {
  console.log('Disconnected from WebSocket server');
});

// Set up event listeners
function setupEventListeners() {
  // Pipeline events
  socket.on('pipeline_execution_started', (data) => {
    console.log('Pipeline execution started', data);
  });
  
  socket.on('pipeline_execution_completed', (data) => {
    console.log('Pipeline execution completed', data);
  });
  
  // Security events
  socket.on('security_vulnerability_detected', (data) => {
    console.log('Security vulnerability detected', data);
  });
  
  // Debug events
  socket.on('debug_error_detected', (data) => {
    console.log('Error detected', data);
  });
  
  // System events
  socket.on('system_alert', (data) => {
    console.log('System alert', data);
  });
}
```

## React Hooks

The frontend provides React hooks for easy integration with WebSocket events:

- `useWebSocketConnection`: Manages the WebSocket connection
- `useWebSocketEvent`: Subscribes to a specific event type
- `useWebSocketCategory`: Subscribes to all events in a category
- `useWebSocketEvents`: Subscribes to all events

Example usage:

```tsx
import { useWebSocketConnection, useWebSocketEvent, useWebSocketCategory } from '../hooks/useWebSocket';
import { EventCategory } from '../services/websocket.service';

function MyComponent() {
  // Connect to WebSocket server
  const { isConnected } = useWebSocketConnection(authToken);
  
  // Subscribe to a specific event
  const { data: pipelineData } = useWebSocketEvent('pipeline_execution_completed');
  
  // Subscribe to all security events
  const { events: securityEvents } = useWebSocketCategory(EventCategory.SECURITY);
  
  return (
    <div>
      <p>Connection status: {isConnected ? 'Connected' : 'Disconnected'}</p>
      
      {/* Render pipeline data */}
      {pipelineData && (
        <div>
          <h3>Latest Pipeline Execution</h3>
          <pre>{JSON.stringify(pipelineData, null, 2)}</pre>
        </div>
      )}
      
      {/* Render security events */}
      <h3>Security Events</h3>
      <ul>
        {securityEvents.map((event) => (
          <li key={event.data.vulnerabilityId || event.timestamp}>
            {event.event_type}: {event.data.vulnerability?.title || 'Unknown'}
          </li>
        ))}
      </ul>
    </div>
  );
}
