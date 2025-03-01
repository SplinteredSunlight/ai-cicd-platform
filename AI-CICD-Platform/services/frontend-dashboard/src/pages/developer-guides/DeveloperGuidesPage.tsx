import { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Tabs, 
  Tab, 
  CircularProgress, 
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  Card,
  CardContent,
  Grid,
  Link
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Code as CodeIcon,
  Architecture as ArchitectureIcon,
  Api as ApiIcon,
  Storage as DatabaseIcon,
  BugReport as TestingIcon,
  Terminal as CliIcon,
  CloudSync as DeploymentIcon,
  Construction as ContributionIcon,
  Info as InfoIcon,
  ArrowForward as ArrowForwardIcon
} from '@mui/icons-material';

// Define the developer guides content
const gettingStartedGuide = {
  title: 'Getting Started',
  icon: <InfoIcon />,
  sections: [
    {
      title: 'Development Environment Setup',
      content: 'To set up your development environment for the AI CI/CD Platform, follow these steps:\n\n1. Clone the repository: `git clone https://github.com/splinteredsunlight/ai-cicd-platform.git`\n2. Install dependencies for all services (see README.md in each service directory)\n3. Set up environment variables by copying `.env.example` to `.env` in each service directory\n4. Start the development servers using Docker Compose: `docker-compose up -d`\n\nThis will start all services in development mode with hot reloading enabled.'
    },
    {
      title: 'Project Structure',
      content: 'The AI CI/CD Platform is organized into several microservices:\n\n- **api-gateway**: API Gateway service for routing and authentication\n- **ai-pipeline-generator**: Service for generating CI/CD pipelines\n- **security-enforcement**: Service for security scanning and enforcement\n- **self-healing-debugger**: Service for automatic error detection and fixing\n- **frontend-dashboard**: React/TypeScript dashboard for the platform\n\nEach service has its own directory with a consistent structure including source code, tests, and documentation.'
    },
    {
      title: 'Development Workflow',
      content: 'The recommended development workflow is:\n\n1. Create a new branch for your feature or bugfix\n2. Implement your changes with appropriate tests\n3. Run tests locally to ensure everything passes\n4. Submit a pull request with a detailed description\n5. Address any feedback from code reviews\n6. Once approved, your changes will be merged to the main branch\n\nThe platform uses a CI/CD pipeline that automatically runs tests, linting, and security scans on all pull requests.'
    },
    {
      title: 'Coding Standards',
      content: 'The project follows these coding standards:\n\n- **TypeScript/JavaScript**: Follow the ESLint configuration\n- **Python**: Follow PEP 8 style guide\n- **Documentation**: Document all public APIs and complex functions\n- **Testing**: Write unit tests for all new functionality\n- **Commits**: Use descriptive commit messages with issue references\n\nCode quality is enforced through linting and automated tests in the CI pipeline.'
    },
    {
      title: 'Getting Help',
      content: 'If you need help with development, you can:\n\n- Check the documentation in the `docs` directory\n- Review the code comments and type definitions\n- Ask questions in the project\'s GitHub Discussions\n- Join the developer community on Discord\n- Refer to these developer guides for specific topics'
    }
  ]
};

const frontendGuide = {
  title: 'Frontend Development',
  icon: <CodeIcon />,
  sections: [
    {
      title: 'Frontend Architecture',
      content: 'The frontend dashboard is built with React, TypeScript, and Material UI. It follows a component-based architecture with the following key concepts:\n\n- **Pages**: Top-level components that represent routes\n- **Layouts**: Components that define the structure of pages\n- **Components**: Reusable UI elements\n- **Stores**: State management using Zustand\n- **Services**: API and WebSocket communication\n\nThe application uses React Router for routing and Axios for API requests.'
    },
    {
      title: 'State Management',
      content: 'The frontend uses Zustand for state management. Each feature has its own store that manages related state:\n\n```typescript\n// Example store definition\nimport { create } from \'zustand\';\n\ninterface MetricsState {\n  metrics: Metric[];\n  loading: boolean;\n  error: string | null;\n  fetchMetrics: () => Promise<void>;\n}\n\nexport const useMetricsStore = create<MetricsState>((set) => ({\n  metrics: [],\n  loading: false,\n  error: null,\n  fetchMetrics: async () => {\n    set({ loading: true, error: null });\n    try {\n      const response = await apiClient.get(\'/metrics\');\n      set({ metrics: response.data, loading: false });\n    } catch (error) {\n      set({ error: error.message, loading: false });\n    }\n  }\n}));\n```\n\nStores should be kept small and focused on specific features.'
    },
    {
      title: 'Component Development',
      content: 'When developing new components, follow these guidelines:\n\n1. Create a new directory in `src/components` for related components\n2. Use TypeScript interfaces for props\n3. Use Material UI\'s `sx` prop for styling\n4. Make components responsive\n5. Write unit tests for each component\n\nExample component structure:\n\n```typescript\ninterface MyComponentProps {\n  title: string;\n  data: DataItem[];\n  onAction: (id: string) => void;\n}\n\nexport default function MyComponent({ title, data, onAction }: MyComponentProps) {\n  // Component implementation\n}\n```'
    },
    {
      title: 'WebSocket Integration',
      content: 'The frontend uses WebSockets for real-time updates. The WebSocketService manages the connection and provides methods for subscribing to events:\n\n```typescript\n// Example WebSocket usage\nimport { useEffect } from \'react\';\nimport { useWebSocketService } from \'../services/websocket.service\';\n\nfunction MyComponent() {\n  const webSocketService = useWebSocketService();\n  \n  useEffect(() => {\n    // Subscribe to an event\n    const cleanup = webSocketService.subscribe(\'event_name\', (data) => {\n      // Handle the event data\n    });\n    \n    // Return cleanup function\n    return cleanup;\n  }, [webSocketService]);\n  \n  // Component implementation\n}\n```\n\nAlways return the cleanup function from useEffect to prevent memory leaks.'
    },
    {
      title: 'Adding New Pages',
      content: 'To add a new page to the dashboard:\n\n1. Create a new component in `src/pages`\n2. Add a route in `App.tsx`\n3. Add a navigation item in `MainLayout.tsx`\n4. Create tests in `src/__tests__/pages`\n\nExample route addition:\n\n```typescript\n<Route\n  path="/my-new-page"\n  element={\n    <PrivateRoute>\n      <MainLayout>\n        <MyNewPage />\n      </MainLayout>\n    </PrivateRoute>\n  }\n/>\n```'
    }
  ]
};

const backendGuide = {
  title: 'Backend Development',
  icon: <ApiIcon />,
  sections: [
    {
      title: 'Backend Architecture',
      content: 'The backend is composed of several microservices built with Python and FastAPI. Each service has a specific responsibility and communicates with other services through the API Gateway.\n\nKey architectural concepts:\n\n- **Service Independence**: Each service can be developed and deployed independently\n- **API Gateway**: Central entry point for all client requests\n- **Event-Driven Communication**: Services communicate through events when appropriate\n- **Containerization**: Each service runs in its own Docker container'
    },
    {
      title: 'Creating New Endpoints',
      content: 'To add a new endpoint to a service:\n\n1. Define the request/response models using Pydantic\n2. Implement the endpoint in the appropriate router\n3. Add validation and error handling\n4. Write tests for the endpoint\n\nExample endpoint implementation:\n\n```python\nfrom fastapi import APIRouter, Depends, HTTPException\nfrom pydantic import BaseModel\nfrom typing import List\n\nrouter = APIRouter(prefix="/items", tags=["items"])\n\nclass Item(BaseModel):\n    id: str\n    name: str\n    description: str = None\n\n@router.get("/", response_model=List[Item])\nasync def get_items():\n    # Implementation\n    return items\n\n@router.post("/", response_model=Item, status_code=201)\nasync def create_item(item: Item):\n    # Implementation\n    return item\n```'
    },
    {
      title: 'Service Communication',
      content: 'Services can communicate with each other in several ways:\n\n1. **HTTP Requests**: Direct API calls between services\n2. **Message Queue**: Asynchronous communication for non-critical operations\n3. **WebSockets**: Real-time communication for events\n\nExample service-to-service communication:\n\n```python\nasync def notify_security_service(pipeline_id: str, scan_results: dict):\n    async with httpx.AsyncClient() as client:\n        response = await client.post(\n            f"{settings.SECURITY_SERVICE_URL}/api/v1/scan-results",\n            json={\n                "pipeline_id": pipeline_id,\n                "results": scan_results\n            },\n            headers={"Authorization": f"Bearer {get_service_token()}"}\n        )\n        response.raise_for_status()\n        return response.json()\n```'
    },
    {
      title: 'Error Handling',
      content: 'Proper error handling is crucial for maintaining a robust system. Follow these guidelines:\n\n1. Use appropriate HTTP status codes\n2. Return structured error responses\n3. Log detailed error information\n4. Handle expected exceptions gracefully\n\nExample error handling:\n\n```python\nfrom fastapi import HTTPException\nfrom logging import getLogger\n\nlogger = getLogger(__name__)\n\ntry:\n    result = await some_operation()\n    return result\nexcept OperationError as e:\n    logger.error(f"Operation failed: {str(e)}", exc_info=True)\n    raise HTTPException(\n        status_code=400,\n        detail={\n            "message": "Operation failed",\n            "error_code": "OPERATION_ERROR",\n            "details": str(e)\n        }\n    )\nexcept Exception as e:\n    logger.error(f"Unexpected error: {str(e)}", exc_info=True)\n    raise HTTPException(status_code=500, detail="Internal server error")\n```'
    },
    {
      title: 'Authentication and Authorization',
      content: 'The platform uses JWT-based authentication and role-based authorization:\n\n1. **Authentication**: JWT tokens issued by the API Gateway\n2. **Authorization**: Role-based access control for endpoints\n\nExample authentication implementation:\n\n```python\nfrom fastapi import Depends, HTTPException, status\nfrom fastapi.security import OAuth2PasswordBearer\nfrom jose import JWTError, jwt\nfrom pydantic import BaseModel\n\noauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")\n\nclass TokenData(BaseModel):\n    username: str\n    roles: list[str] = []\n\nasync def get_current_user(token: str = Depends(oauth2_scheme)):\n    credentials_exception = HTTPException(\n        status_code=status.HTTP_401_UNAUTHORIZED,\n        detail="Could not validate credentials",\n        headers={"WWW-Authenticate": "Bearer"},\n    )\n    try:\n        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])\n        username: str = payload.get("sub")\n        if username is None:\n            raise credentials_exception\n        token_data = TokenData(username=username, roles=payload.get("roles", []))\n    except JWTError:\n        raise credentials_exception\n    return token_data\n\nasync def require_admin(current_user: TokenData = Depends(get_current_user)):\n    if "admin" not in current_user.roles:\n        raise HTTPException(\n            status_code=status.HTTP_403_FORBIDDEN,\n            detail="Insufficient permissions"\n        )\n    return current_user\n```'
    }
  ]
};

const databaseGuide = {
  title: 'Database Integration',
  icon: <DatabaseIcon />,
  sections: [
    {
      title: 'Database Architecture',
      content: 'The platform uses a combination of database technologies:\n\n- **PostgreSQL**: Primary relational database for structured data\n- **MongoDB**: Document database for flexible schema data\n- **Redis**: In-memory database for caching and real-time data\n\nEach service manages its own database connection and schema.'
    },
    {
      title: 'Database Models',
      content: 'Database models are defined using SQLAlchemy for PostgreSQL and Pydantic for MongoDB:\n\n```python\n# SQLAlchemy model example\nfrom sqlalchemy import Column, Integer, String, ForeignKey, DateTime\nfrom sqlalchemy.ext.declarative import declarative_base\nfrom datetime import datetime\n\nBase = declarative_base()\n\nclass Pipeline(Base):\n    __tablename__ = "pipelines"\n\n    id = Column(String, primary_key=True)\n    name = Column(String, nullable=False)\n    repository_url = Column(String, nullable=False)\n    created_at = Column(DateTime, default=datetime.utcnow)\n    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)\n    user_id = Column(String, ForeignKey("users.id"))\n```\n\n```python\n# Pydantic model for MongoDB\nfrom pydantic import BaseModel, Field\nfrom typing import List, Optional\nfrom datetime import datetime\nfrom bson import ObjectId\n\nclass PydanticObjectId(str):\n    @classmethod\n    def __get_validators__(cls):\n        yield cls.validate\n\n    @classmethod\n    def validate(cls, v):\n        if not ObjectId.is_valid(v):\n            raise ValueError("Invalid ObjectId")\n        return str(v)\n\nclass BuildLog(BaseModel):\n    id: PydanticObjectId = Field(default_factory=lambda: str(ObjectId()))\n    pipeline_id: str\n    build_number: int\n    status: str\n    logs: List[str]\n    started_at: datetime\n    completed_at: Optional[datetime] = None\n\n    class Config:\n        schema_extra = {\n            "example": {\n                "pipeline_id": "abc123",\n                "build_number": 42,\n                "status": "success",\n                "logs": ["Step 1: Clone repository", "Step 2: Install dependencies"],\n                "started_at": "2023-01-01T00:00:00Z",\n                "completed_at": "2023-01-01T00:05:00Z"\n            }\n        }\n```'
    },
    {
      title: 'Database Migrations',
      content: 'Database migrations are managed using Alembic for PostgreSQL:\n\n1. Create a new migration: `alembic revision --autogenerate -m "description"`\n2. Apply migrations: `alembic upgrade head`\n3. Rollback migrations: `alembic downgrade -1`\n\nMigrations are automatically applied during service startup in development mode.'
    },
    {
      title: 'Query Optimization',
      content: 'When writing database queries, follow these optimization guidelines:\n\n1. Use indexes for frequently queried fields\n2. Limit the number of returned records\n3. Select only the needed columns\n4. Use joins efficiently\n5. Consider caching for frequently accessed data\n\nExample optimized query:\n\n```python\nfrom sqlalchemy import select, join\n\nasync def get_user_pipelines(user_id: str, limit: int = 10, offset: int = 0):\n    query = select(\n        Pipeline.id,\n        Pipeline.name,\n        Pipeline.status,\n        Pipeline.updated_at\n    ).join(\n        User, User.id == Pipeline.user_id\n    ).where(\n        User.id == user_id\n    ).order_by(\n        Pipeline.updated_at.desc()\n    ).limit(limit).offset(offset)\n    \n    result = await database.fetch_all(query)\n    return result\n```'
    },
    {
      title: 'Transactions',
      content: 'Use transactions for operations that require atomicity:\n\n```python\nasync def transfer_pipeline(pipeline_id: str, from_user_id: str, to_user_id: str):\n    async with database.transaction():\n        # Verify ownership\n        pipeline = await get_pipeline(pipeline_id)\n        if pipeline.user_id != from_user_id:\n            raise HTTPException(status_code=403, detail="Not authorized")\n        \n        # Update ownership\n        query = update(Pipeline).where(Pipeline.id == pipeline_id).values(user_id=to_user_id)\n        await database.execute(query)\n        \n        # Create audit log\n        await create_audit_log(\n            action="transfer_pipeline",\n            resource_id=pipeline_id,\n            user_id=from_user_id,\n            details={"to_user_id": to_user_id}\n        )\n        \n        return await get_pipeline(pipeline_id)\n```'
    }
  ]
};

const testingGuide = {
  title: 'Testing',
  icon: <TestingIcon />,
  sections: [
    {
      title: 'Testing Strategy',
      content: 'The platform employs a comprehensive testing strategy with multiple levels of tests:\n\n- **Unit Tests**: Test individual functions and components\n- **Integration Tests**: Test interactions between components\n- **API Tests**: Test API endpoints\n- **End-to-End Tests**: Test complete user flows\n- **Performance Tests**: Test system performance under load\n\nTests are run automatically in the CI pipeline for all pull requests.'
    },
    {
      title: 'Frontend Testing',
      content: 'Frontend tests use Vitest, React Testing Library, and MSW for API mocking:\n\n```typescript\nimport { render, screen, waitFor } from \'@testing-library/react\';\nimport userEvent from \'@testing-library/user-event\';\nimport { vi } from \'vitest\';\nimport PipelineList from \'./PipelineList\';\n\n// Mock the API client\nvi.mock(\'../services/api.service\', () => ({\n  apiClient: {\n    get: vi.fn().mockResolvedValue({\n      data: [\n        { id: \'1\', name: \'Pipeline 1\', status: \'success\' },\n        { id: \'2\', name: \'Pipeline 2\', status: \'failed\' },\n      ]\n    })\n  }\n}));\n\ndescribe(\'PipelineList\', () => {\n  it(\'renders pipelines from API\', async () => {\n    render(<PipelineList />);\n    \n    // Initially shows loading state\n    expect(screen.getByRole(\'progressbar\')).toBeInTheDocument();\n    \n    // Wait for data to load\n    await waitFor(() => {\n      expect(screen.queryByRole(\'progressbar\')).not.toBeInTheDocument();\n    });\n    \n    // Check that pipelines are rendered\n    expect(screen.getByText(\'Pipeline 1\')).toBeInTheDocument();\n    expect(screen.getByText(\'Pipeline 2\')).toBeInTheDocument();\n  });\n  \n  it(\'handles pipeline selection\', async () => {\n    const user = userEvent.setup();\n    const onSelect = vi.fn();\n    \n    render(<PipelineList onSelect={onSelect} />);\n    \n    // Wait for data to load\n    await waitFor(() => {\n      expect(screen.queryByRole(\'progressbar\')).not.toBeInTheDocument();\n    });\n    \n    // Click on a pipeline\n    await user.click(screen.getByText(\'Pipeline 1\'));\n    \n    // Check that onSelect was called with the correct pipeline\n    expect(onSelect).toHaveBeenCalledWith(\'1\');\n  });\n});\n```'
    },
    {
      title: 'Backend Testing',
      content: 'Backend tests use pytest and the FastAPI TestClient:\n\n```python\nimport pytest\nfrom fastapi.testclient import TestClient\nfrom main import app\n\nclient = TestClient(app)\n\ndef test_read_pipelines():\n    response = client.get("/api/v1/pipelines/")\n    assert response.status_code == 200\n    data = response.json()\n    assert isinstance(data, list)\n\ndef test_create_pipeline():\n    pipeline_data = {\n        "name": "Test Pipeline",\n        "repository_url": "https://github.com/test/repo.git"\n    }\n    response = client.post("/api/v1/pipelines/", json=pipeline_data)\n    assert response.status_code == 201\n    data = response.json()\n    assert data["name"] == pipeline_data["name"]\n    assert data["repository_url"] == pipeline_data["repository_url"]\n    assert "id" in data\n```'
    },
    {
      title: 'Mocking',
      content: 'Use mocking to isolate the code being tested:\n\n```python\nfrom unittest.mock import patch, MagicMock\n\n@patch("services.github_service.GitHubClient")\ndef test_analyze_repository(mock_github_client):\n    # Setup the mock\n    mock_instance = MagicMock()\n    mock_github_client.return_value = mock_instance\n    mock_instance.get_repository.return_value = {\n        "name": "test-repo",\n        "language": "Python",\n        "has_workflow": True\n    }\n    \n    # Call the function being tested\n    result = analyze_repository("test/repo")\n    \n    # Assertions\n    mock_instance.get_repository.assert_called_once_with("test/repo")\n    assert result["language"] == "Python"\n    assert result["has_workflow"] == True\n```'
    },
    {
      title: 'Test Coverage',
      content: 'Aim for high test coverage, especially for critical components:\n\n1. Frontend: Use Vitest coverage reports\n2. Backend: Use pytest-cov for coverage reports\n\nThe CI pipeline enforces minimum coverage thresholds:\n- Frontend: 80% coverage\n- Backend: 90% coverage\n\nTo run coverage reports locally:\n\n```bash\n# Frontend\nnpm run coverage\n\n# Backend\npytest --cov=app --cov-report=term-missing\n```'
    },
    {
      title: 'Performance Testing',
      content: 'Performance tests use Locust for load testing and benchmarking:\n\n```python\nfrom locust import HttpUser, task, between\n\nclass PipelineUser(HttpUser):\n    wait_time = between(1, 3)\n    \n    def on_start(self):\n        # Login\n        response = self.client.post("/api/v1/auth/login", json={\n            "username": "test@example.com",\n            "password": "password"\n        })\n        self.token = response.json()["access_token"]\n        self.headers = {\"Authorization\": f"Bearer {self.token}"}\n    \n    @task\n    def get_pipelines(self):\n        self.client.get("/api/v1/pipelines/", headers=self.headers)\n    \n    @task\n    def get_dashboard(self):\n        self.client.get("/api/v1/dashboard/metrics", headers=self.headers)\n```\n\nRun performance tests with: `locust -f locustfile.py`'
    }
  ]
};

const cicdGuide = {
  title: 'CI/CD Pipeline',
  icon: <DeploymentIcon />,
  sections: [
    {
      title: 'CI/CD Architecture',
      content: 'The platform uses GitHub Actions for CI/CD pipelines. The workflow includes:\n\n1. **Build**: Build Docker images for all services\n2. **Test**: Run unit and integration tests\n3. **Security Scan**: Scan for vulnerabilities\n4. **Deploy**: Deploy to staging or production environments\n\nThe pipeline is defined in `.github/workflows/ci-cd.yml`.'
    },
    {
      title: 'Workflow Configuration',
      content: 'The CI/CD workflow is configured to run on pull requests and pushes to the main branch:\n\n```yaml\nname: CI/CD Pipeline\n\non:\n  push:\n    branches: [ main ]\n  pull_request:\n    branches: [ main ]\n\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      \n      - name: Set up Docker Buildx\n        uses: docker/setup-buildx-action@v2\n      \n      - name: Build and push\n        uses: docker/build-push-action@v4\n        with:\n          context: ./services/api-gateway\n          push: ${{ github.event_name != \'pull_request\' }}\n          tags: ${{ secrets.DOCKER_REGISTRY }}/api-gateway:${{ github.sha }}\n  \n  test:\n    runs-on: ubuntu-latest\n    needs: build\n    steps:\n      - uses: actions/checkout@v3\n      \n      - name: Set up Python\n        uses: actions/setup-python@v4\n        with:\n          python-version: \'3.10\'\n      \n      - name: Install dependencies\n        run: |\n          python -m pip install --upgrade pip\n          pip install pytest pytest-cov\n          pip install -r requirements.txt\n      \n      - name: Run tests\n        run: pytest --cov=app --cov-report=xml\n      \n      - name: Upload coverage\n        uses: codecov/codecov-action@v3\n        with:\n          file: ./coverage.xml\n  \n  deploy:\n    runs-on: ubuntu-latest\n    needs: [build, test]\n    if: github.event_name == \'push\' && github.ref == \'refs/heads/main\'\n    steps:\n      - name: Deploy to staging\n        uses: appleboy/ssh-action@master\n        with:\n          host: ${{ secrets.STAGING_HOST }}\n          username: ${{ secrets.STAGING_USERNAME }}\n          key: ${{ secrets.STAGING_SSH_KEY }}\n          script: |\n            cd /opt/ai-cicd-platform\n            docker-compose pull\n            docker-compose up -d\n```'
    },
    {
      title: 'Environment Configuration',
      content: 'The platform supports multiple deployment environments:\n\n- **Development**: Local development environment\n- **Staging**: Testing environment for pre-production validation\n- **Production**: Live environment for end users\n\nEnvironment-specific configuration is managed through environment variables and GitHub Secrets.'
    },
    {
      title: 'Deployment Process',
      content: 'The deployment process follows these steps:\n\n1. Build Docker images with version tags\n2. Push images to container registry\n3. Update deployment manifests\n4. Apply changes to the target environment\n5. Run database migrations\n6. Verify deployment health\n\nDeployments can be rolled back if issues are detected.'
    },
    {
      title: 'Monitoring and Logging',
      content: 'The CI/CD pipeline includes monitoring and logging:\n\n- **Build Logs**: Available in GitHub Actions\n- **Deployment Logs**: Collected from deployment targets\n- **Application Logs**: Aggregated using a logging service\n- **Metrics**: Collected for pipeline performance\n\nMonitoring alerts are configured for failed builds and deployments.'
    }
  ]
};

const contributionGuide = {
  title: 'Contributing',
  icon: <ContributionIcon />,
  sections: [
    {
      title: 'Contribution Process',
      content: 'To contribute to the AI CI/CD Platform:\n\n1. Fork the repository\n2. Create a feature branch\n3. Implement your changes\n4. Write or update tests\n5. Update documentation\n6. Submit a pull request\n\nAll contributions must follow the project\'s coding standards and include appropriate tests.'
    },
    {
      title: 'Pull Request Guidelines',
      content: 'When submitting a pull request:\n\n1. Provide a clear description of the changes\n2. Reference any related issues\n3. Include screenshots for UI changes\n4. Ensure all tests pass\n5. Maintain or improve code coverage\n6. Follow the code style guidelines\n\nPull requests are reviewed by at least one maintainer before merging.'
    },
    {
      title: 'Code Review Process',
      content: 'The code review process ensures quality and consistency:\n\n1. Automated checks for linting and tests\n2. Review by at least one maintainer\n3. Address all feedback and comments\n4. Final approval before merging\n\nReviewers look for code quality, test coverage, documentation, and adherence to project standards.'
    },
    {
      title: 'Documentation Guidelines',
      content: 'Documentation is a crucial part of the project:\n\n1. Update README files for significant changes\n2. Document all public APIs\n3. Include code comments for complex logic\n4. Update architecture diagrams if needed\n5. Provide examples for new features\n\nDocumentation should be clear, concise, and helpful for other developers.'
    },
    {
      title: 'Issue Reporting',
      content: 'When reporting issues:\n\n1. Use the issue template\n2. Provide steps to reproduce\n3. Include relevant logs or screenshots\n4. Specify the environment and version\n5. Label the issue appropriately\n\nIssues are triaged by maintainers and assigned priority labels.'
    }
  ]
};

const cliGuide = {
  title: 'CLI Tools',
  icon: <CliIcon />,
  sections: [
    {
      title: 'CLI Overview',
      content: 'The platform includes several CLI tools for development and administration:\n\n- **task-tracker.py**: Manage and track development tasks\n- **context-manager.py**: Manage context for AI-assisted development\n- **setup-task-system.sh**: Set up the task tracking system\n- **generate-next-task-prompt.sh**: Generate prompts for the next task\n- **push-to-github.sh**: Push changes to GitHub'
    },
    {
      title: 'Task Tracker',
      content: 'The task-tracker.py script manages development tasks:\n\n```bash\n# List all tasks\npython scripts/task-tracker.py list\n\n# Mark a task as completed\npython scripts/task-tracker.py complete "Task name"\n\n# Add a new task\npython scripts/task-tracker.py add "New task" "Description" "Category"\n```\n\nThe script maintains a JSON file with task status and metadata.'
    },
    {
      title: 'Context Manager',
      content: 'The context-manager.py script manages context for AI-assisted development:\n\n```bash\n# Generate context for a task\npython scripts/context-manager.py generate "Task name"\n\n# Update context with new information\npython scripts/context-manager.py update "Task name" "New information"\n\n# Clear context for a task\npython scripts/context-manager.py clear "Task name"\n```\n\nThe script helps maintain relevant context for AI tools to assist with development tasks.'
    },
    {
      title: 'CI/CD Scripts',
      content: 'The platform includes scripts for CI/CD automation:\n\n```bash\n# Run all tests\n./scripts/run-tests.sh\n\n# Build all services\n./scripts/build-services.sh\n\n# Deploy to staging\n./scripts/deploy-staging.sh\n```\n\nThese scripts are used in the CI/CD pipeline and can also be run locally for testing.'
    },
    {
      title: 'Development Utilities',
      content: 'Additional utility scripts for development:\n\n```bash\n# Generate API documentation\n./scripts/generate-api-docs.sh\n\n# Update architecture diagrams\n./scripts/update-diagrams.sh\n\n# Analyze code quality\n./scripts/analyze-code.sh\n```\n\nThese utilities help maintain code quality and documentation.'
    }
  ]
};

const architectureGuide = {
  title: 'Architecture',
  icon: <ArchitectureIcon />,
  sections: [
    {
      title: 'System Architecture',
      content: 'The AI CI/CD Platform follows a microservices architecture with the following key components:\n\n1. **API Gateway**: Central entry point for all client requests\n2. **Frontend Dashboard**: React/TypeScript user interface\n3. **AI Pipeline Generator**: Service for generating CI/CD pipelines\n4. **Security Enforcement**: Service for security scanning and enforcement\n5. **Self-Healing Debugger**: Service for automatic error detection and fixing\n\nThese services communicate through REST APIs and WebSockets, with each service having its own database.'
    },
    {
      title: 'Data Flow',
      content: 'The data flow through the system follows these patterns:\n\n1. **User Requests**: Client requests enter through the API Gateway\n2. **Service Communication**: Services communicate through the API Gateway or directly\n3. **Real-time Updates**: WebSockets provide real-time updates to clients\n4. **Data Storage**: Each service manages its own data storage\n5. **Event Processing**: Events are processed asynchronously when appropriate\n\nThis architecture ensures scalability, resilience, and maintainability.'
    },
    {
      title: 'Security Architecture',
      content: 'The security architecture includes multiple layers of protection:\n\n1. **Authentication**: JWT-based authentication for all API requests\n2. **Authorization**: Role-based access control for endpoints\n3. **API Gateway Security**: Rate limiting, request validation, and threat protection\n4. **Service Security**: Each service implements its own security measures\n5. **Data Security**: Encryption for sensitive data at rest and in transit\n\nSecurity is enforced at every level of the system.'
    },
    {
      title: 'Scalability',
      content: 'The platform is designed for scalability:\n\n1. **Horizontal Scaling**: Services can be scaled independently\n2. **Load Balancing**: Requests are distributed across service instances\n3. **Database Scaling**: Database sharding and replication for high load\n4. **Caching**: Redis caching for frequently accessed data\n5. **Asynchronous Processing**: Background processing for CPU-intensive tasks\n\nThis approach allows the system to handle increasing load by adding more resources.'
    },
    {
      title: 'Resilience',
      content: 'The system includes several resilience patterns:\n\n1. **Circuit Breakers**: Prevent cascading failures\n2. **Retry Mechanisms**: Automatically retry failed operations\n3. **Fallbacks**: Provide alternative behavior when services are unavailable\n4. **Health Checks**: Monitor service health and take action when issues are detected\n5. **Graceful Degradation**: Continue operating with reduced functionality when components fail\n\nThese patterns ensure the system remains available even when components fail.'
    }
  ]
};

// Combine all guides
const allGuides = [
  gettingStartedGuide,
  frontendGuide,
  backendGuide,
  databaseGuide,
  testingGuide,
  cicdGuide,
  cliGuide,
  architectureGuide,
  contributionGuide
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
      id={`developer-guides-tabpanel-${index}`}
      aria-labelledby={`developer-guides-tab-${index}`}
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
    id: `developer-guides-tab-${index}`,
    'aria-controls': `developer-guides-tabpanel-${index}`,
  };
}

export default function DeveloperGuidesPage() {
  const [value, setValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate loading the developer guides
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
        Developer Guides
      </Typography>
      <Typography variant="body1" paragraph>
        Welcome to the AI CI/CD Platform developer guides. These guides provide detailed information for developers contributing to the platform or building integrations.
      </Typography>

      <Paper sx={{ width: '100%', mb: 2 }}>
        <Tabs
          value={value}
          onChange={handleChange}
          indicatorColor="primary"
          textColor="primary"
          aria-label="Developer guides tabs"
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
