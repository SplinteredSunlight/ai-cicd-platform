# Frontend Dashboard

React/TypeScript dashboard for the AI CI/CD Platform. Part of [splinteredsunlight/ai-cicd-platform](https://github.com/splinteredsunlight/ai-cicd-platform).

## Features

- 📊 Real-time metrics and analytics
- 🔄 Pipeline management and monitoring
- 🛡️ Security vulnerability tracking
- 🔧 Self-healing debugger interface
- 🤖 ML-based error classification
- 🔌 WebSocket-powered real-time updates
- ⚙️ System configuration and settings
- 📚 Interactive API documentation
- 📖 Comprehensive user guides

## Tech Stack

- React 18
- TypeScript
- Material UI
- Zustand (State Management)
- Vite (Build Tool)
- Nivo (Charts)
- React Router
- Axios
- Socket.IO (WebSocket client)
- Swagger UI (API Documentation)

## Development Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   
   Configure the following variables in `.env`:
   ```
   VITE_API_URL=http://localhost:8000
   VITE_ENABLE_DEBUG_MODE=true
   VITE_ENABLE_ANALYTICS=false
   VITE_APP_NAME="AI CI/CD Platform"
   VITE_DEFAULT_THEME=light
   VITE_POLLING_INTERVAL=30000
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

4. Access the dashboard:
   - URL: http://localhost:3000
   - Development credentials:
     - Email: admin@example.com
     - Password: admin123

## WebSocket Infrastructure

The dashboard uses a robust WebSocket infrastructure for real-time updates across the application:

### Client-Side Implementation

- **WebSocketService**: Singleton service that manages WebSocket connections
  - Handles connection, authentication, and reconnection
  - Provides event subscription system with cleanup functions
  - Maintains connection state and notifies subscribers of changes

### Server-Side Implementation

- **WebSocketService** in API Gateway:
  - Manages client connections and authentication
  - Tracks connected users and their roles
  - Provides targeted event emission (by user, role, or broadcast)
  - Handles custom event registration

### Event Types

- `debug_session_created`: New debugging session created
- `debug_session_updated`: Existing session updated
- `debug_error_detected`: New error detected in pipeline
- `debug_ml_classification`: ML classification results available
- `debug_patch_generated`: Auto-fix patch generated
- `debug_patch_applied`: Patch applied to fix error
- `debug_patch_rollback`: Patch rolled back due to issues
- `architecture_diagram_update`: Architecture diagram updates available

## ML-Based Error Classification

The dashboard includes advanced ML-based error classification visualizations:

### Features

- **Multi-model Classification**: Uses ensemble of ML models to classify errors by:
  - Category (dependency, permission, syntax, etc.)
  - Severity (critical, high, medium, low)
  - Pipeline stage (checkout, build, test, deploy)

- **Confidence Visualization**: Displays model confidence scores for classifications

- **Real-time Updates**: Classifications streamed via WebSockets as they're processed

- **Interactive Visualizations**:
  - Error distribution by category (pie chart)
  - Error severity breakdown (bar chart)
  - ML classification confidence (radar chart)
  - Error correlation heatmap
  - Error flow diagram (Sankey)

### Technical Implementation

- **Feature Extraction**: Custom feature extraction from error messages and context
- **Model Types**: Support for Random Forest, Naive Bayes, and Logistic Regression
- **Visualization Components**: Responsive charts using Nivo with mobile optimization
- **State Management**: Zustand store for ML classifications with WebSocket integration

## API Documentation

The dashboard includes comprehensive API documentation for developers:

### Features

- **Interactive API Explorer**: Swagger UI-based interface for exploring and testing API endpoints
- **WebSocket Event Documentation**: Detailed documentation of WebSocket events and their payloads
- **Authentication Guide**: Step-by-step guide for authentication flow
- **Tabbed Interface**: Easy navigation between different documentation sections
- **Request/Response Examples**: Example requests and responses for all endpoints

### Technical Implementation

- **OpenAPI Specification**: Standard OpenAPI 3.0 specification for REST API endpoints
- **Swagger UI Integration**: Interactive API documentation and testing
- **WebSocket Event Catalog**: Comprehensive list of all WebSocket events with payload schemas
- **Authentication Flow Documentation**: Clear documentation of JWT-based authentication
- **Responsive Design**: Mobile-friendly documentation interface

## Architecture Diagrams

The dashboard features interactive architecture diagram visualizations:

### Features

- **Interactive Diagrams**: Renders Mermaid-based architecture diagrams
- **Multiple Diagram Types**: Support for system, service, component, sequence, and class diagrams
- **Real-time Updates**: Diagrams are updated in real-time via WebSockets
- **Tabbed Interface**: Navigate between multiple diagrams in a single widget
- **Responsive Design**: Diagrams adapt to different screen sizes and devices

### Technical Implementation

- **Mermaid Integration**: Uses Mermaid.js for rendering diagrams from text definitions
- **Lazy Loading**: Components are lazy-loaded for better performance
- **WebSocket Updates**: Real-time diagram updates via WebSocket events
- **Diagram Templates**: Pre-configured dashboard templates for architecture visualization
- **Responsive Rendering**: SVG-based diagrams that scale to fit any container

## User Guides

The dashboard includes comprehensive user guides to help users navigate and utilize the platform effectively:

### Features

- **Getting Started Guide**: Overview of the platform and first steps for new users
- **Feature-Specific Guides**: Detailed instructions for each major feature of the platform
- **Tabbed Interface**: Easy navigation between different guide sections
- **Accordion Sections**: Collapsible sections for better organization of content
- **Interactive Elements**: Cards and buttons for quick navigation between related guides

### Technical Implementation

- **Component-Based Structure**: Each guide is a separate component for maintainability
- **Material UI Components**: Uses Accordion, Tabs, Cards, and other Material UI components
- **Responsive Design**: Mobile-friendly layout that adapts to different screen sizes
- **Structured Content**: Well-organized content with clear headings and sections
- **Icon Integration**: Feature-specific icons for visual recognition

## Project Structure

```
src/
├── config/           # Configuration files
│   ├── api.ts       # API endpoints and types
│   ├── openapi.json # OpenAPI specification
│   └── theme.ts     # MUI theme configuration
├── layouts/         # Page layouts
│   ├── AuthLayout/  # Authentication pages layout
│   └── MainLayout/  # Main application layout
├── pages/          # Application pages
│   ├── auth/       # Authentication pages
│   ├── dashboard/  # Dashboard and analytics
│   ├── pipelines/  # Pipeline management
│   ├── security/   # Security monitoring
│   ├── debugger/   # Self-healing debugger
│   ├── settings/   # System settings
│   ├── api-docs/   # API documentation
│   └── user-guides/ # User guides and documentation
├── stores/         # State management
│   ├── auth.store.ts    # Authentication state
│   ├── metrics.store.ts # Analytics state
│   ├── pipeline.store.ts # Pipeline state
│   ├── security.store.ts # Security state
│   └── debug.store.ts   # Debugger state
├── services/       # Service layer
│   ├── websocket.service.ts # WebSocket connection management
│   └── api.service.ts  # API client
└── components/     # Reusable components
    ├── dashboard/  # Dashboard components
    └── visualizations/ # Data visualization components
        ├── ErrorClassificationChart.tsx # Error classification charts
        ├── MLErrorClassification.tsx # ML-based error visualizations
        └── ArchitectureDiagram.tsx # Architecture diagram visualizations
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run test` - Run tests
- `npm run coverage` - Generate test coverage report

## Development Guidelines

1. **TypeScript**:
   - Use strict type checking
   - Define interfaces for all data structures
   - Avoid using `any` type

2. **State Management**:
   - Use Zustand for global state
   - Keep component state local when possible
   - Use React Query for server state
   - Use WebSocket hooks for real-time data

3. **Styling**:
   - Use Material UI's `sx` prop for styling
   - Follow theme configuration
   - Maintain consistent spacing
   - Ensure responsive design for all components

4. **Components**:
   - Keep components focused and reusable
   - Use TypeScript interfaces for props
   - Document complex components
   - Implement responsive behavior for mobile/tablet

5. **Testing**:
   - Write unit tests for critical components
   - Test state management logic
   - Mock API calls and WebSocket events in tests
   - Test ML integration with mock classification data

## Production Deployment

1. Build the application:
   ```bash
   npm run build
   ```

2. Configure production environment:
   - Set `VITE_API_URL` to production API URL
   - Disable debug mode
   - Configure proper authentication

3. Deploy the `dist` directory to your hosting service

## Monitoring and Analytics

The dashboard includes built-in monitoring:

- Real-time metrics tracking
- Error logging
- Performance monitoring
- User activity tracking

## Troubleshooting

Common issues and solutions:

1. **API Connection Issues**:
   - Verify API URL in `.env`
   - Check API service status
   - Confirm CORS configuration

2. **WebSocket Connection Issues**:
   - Check WebSocket URL configuration
   - Verify authentication token is valid
   - Check browser console for connection errors
   - Ensure WebSocket server is running
   - Check for firewall or proxy issues

3. **Authentication Issues**:
   - Clear localStorage
   - Check token expiration
   - Verify API credentials

4. **Performance Issues**:
   - Check polling intervals
   - Monitor browser console
   - Review network requests
   - Check WebSocket message volume
   - Verify ML visualization rendering performance

5. **ML Classification Issues**:
   - Check ML model server status
   - Verify classification data format
   - Check WebSocket event handlers for ML events
   - Inspect classification confidence scores

6. **API Documentation Issues**:
   - Verify OpenAPI specification is valid
   - Check Swagger UI integration
   - Ensure API endpoints match the documentation
   - Verify WebSocket event documentation is up-to-date

7. **User Guides Issues**:
   - Check tab navigation functionality
   - Verify accordion sections expand/collapse properly
   - Ensure all guide content is displaying correctly
   - Check responsive layout on different screen sizes
   - Verify navigation between related guides works as expected

## Contributing

1. Follow TypeScript best practices
2. Maintain consistent code style
3. Write clear commit messages
4. Add/update tests as needed
5. Document changes

## License
