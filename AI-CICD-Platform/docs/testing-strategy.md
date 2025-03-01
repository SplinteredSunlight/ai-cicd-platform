# Testing Strategy

This document outlines the testing strategy for the AI CI/CD Platform project.

## Testing Levels

### Unit Testing

- **Purpose**: Verify that individual components work as expected in isolation
- **Tools**: 
  - Backend: pytest
  - Frontend: Vitest
- **Coverage Target**: 80%+
- **Implementation**: 
  - Each service has its own test directory
  - Tests follow the same structure as the code
  - Mock external dependencies

### Integration Testing

- **Purpose**: Verify that components work together correctly
- **Tools**: 
  - Backend: pytest with pytest-asyncio
  - Frontend: Vitest with React Testing Library
- **Coverage Target**: 70%+
- **Implementation**:
  - Test API endpoints with real requests
  - Test service-to-service communication
  - Use test fixtures for consistent test data

### End-to-End Testing

- **Purpose**: Verify that the entire system works correctly from a user perspective
- **Tools**: Cypress (for future implementation)
- **Coverage**: Key user flows
- **Implementation**:
  - Test critical user journeys
  - Run against a fully deployed system
  - Automate in CI pipeline

## Testing Practices

### Test-Driven Development (TDD)

- Write tests before implementing features
- Use tests to guide the design of the code
- Ensure all requirements are covered by tests

### Continuous Integration

- Run tests on every commit
- Block PRs that break tests
- Generate and publish test coverage reports

### Mocking Strategy

- Mock external services and APIs
- Use dependency injection for easier testing
- Create reusable mock fixtures

## Service-Specific Testing

### Frontend Dashboard

- **Component Tests**: Test individual React components
- **Store Tests**: Test Zustand stores and state management
- **Integration Tests**: Test component interactions
- **Snapshot Tests**: Ensure UI consistency

### API Gateway

- **Routing Tests**: Test request routing logic
- **Authentication Tests**: Test auth middleware
- **Rate Limiting Tests**: Test rate limiting functionality
- **Circuit Breaker Tests**: Test circuit breaker patterns

### AI Pipeline Generator

- **Generation Tests**: Test pipeline generation logic
- **Template Tests**: Test template rendering
- **Integration Tests**: Test with different project types

### Security Enforcement

- **Scanner Tests**: Test individual scanners
- **Vulnerability Detection Tests**: Test detection accuracy
- **SBOM Generation Tests**: Test SBOM creation

### Self-Healing Debugger

- **Log Analysis Tests**: Test log parsing and error detection
  - Test expanded error pattern recognition across multiple CI/CD platforms
  - Verify correct categorization of different error types
  - Test AI-powered analysis for unmatched errors
  
- **Patch Generation Tests**: Test patch creation
  - Test template-based patch generation for various error types
  - Test patch generation for network, resource, test, and security issues
  - Verify patch validation and safety checks
  
- **Patch Application Tests**: Test patch application and rollback
  - Test dry-run simulation
  - Test actual patch application
  - Test rollback functionality
  
- **WebSocket Tests**: Test real-time debugging sessions
  - Test interactive debugging commands
  - Test batch patch application
  - Test session export functionality
  
- **ML-Based Classification Tests**: Test machine learning error classification
  - Test model training with historical error data
  - Test classification accuracy
  - Test integration with existing pattern matching

## Test Data Management

- Use fixtures for consistent test data
- Reset test state between tests
- Use separate test databases/storage

## Test Execution

### Local Development

```bash
# Backend service tests
cd services/<service-name>
pytest

# Frontend tests
cd services/frontend-dashboard
npm test
```

### CI Pipeline

Tests are automatically run in the GitHub Actions CI pipeline:
- On pull requests to main branch
- On direct pushes to main branch

See `.github/workflows/ci.yml` for the complete CI configuration.

## Test Reporting

- Coverage reports are generated for each service
- Reports are uploaded to Codecov
- Test results are displayed in GitHub PR checks

## Future Improvements

- Implement E2E testing with Cypress
- Add performance testing
- Add security testing (SAST/DAST)
- Implement contract testing between services
