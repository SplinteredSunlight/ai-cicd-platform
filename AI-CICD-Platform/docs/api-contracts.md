# API Contracts

This document defines the API contracts between the various components of the AI CI/CD Platform. These contracts ensure that components can communicate effectively and maintain compatibility as they evolve.

## Overview

The AI CI/CD Platform uses a microservices architecture, with each service exposing RESTful APIs and, in some cases, WebSocket interfaces. All APIs follow these general principles:

- Use JSON for request and response bodies
- Use standard HTTP methods and status codes
- Include version information in the URL path
- Implement consistent error handling
- Document using OpenAPI (Swagger) specification

## API Gateway

The API Gateway serves as the central entry point for all client requests and handles authentication, rate limiting, and routing.

### Base URL

```
https://api.cicd-platform.example.com/v1
```

### Authentication Endpoints

#### Login

```
POST /auth/login
```

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "user123",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "admin"
  }
}
```

#### Refresh Token

```
POST /auth/refresh
```

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Logout

```
POST /auth/logout
```

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

### System Status

```
GET /api/status
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.2.3",
  "services": {
    "pipeline_generator": "healthy",
    "security_enforcement": "healthy",
    "self_healing_debugger": "healthy"
  },
  "uptime": 86400
}
```

## AI Pipeline Generator

The AI Pipeline Generator service creates and optimizes CI/CD pipelines using machine learning.

### Base URL (via API Gateway)

```
https://api.cicd-platform.example.com/v1/pipeline
```

### Endpoints

#### Analyze Repository

```
POST /analyze
```

**Request:**
```json
{
  "repository_url": "https://github.com/user/repo",
  "branch": "main",
  "access_token": "github_pat_..."
}
```

**Response:**
```json
{
  "analysis_id": "analysis123",
  "status": "in_progress",
  "estimated_completion_time": "2023-04-15T14:30:00Z"
}
```

#### Get Analysis Results

```
GET /analyze/{analysis_id}
```

**Response:**
```json
{
  "analysis_id": "analysis123",
  "status": "completed",
  "repository": "https://github.com/user/repo",
  "dependencies": [
    {
      "type": "npm",
      "packages": ["react", "express", "lodash"]
    },
    {
      "type": "docker",
      "images": ["node:14", "nginx:latest"]
    }
  ],
  "recommended_pipeline_type": "node_fullstack",
  "completion_time": "2023-04-15T14:25:30Z"
}
```

#### Generate Pipeline

```
POST /generate
```

**Request:**
```json
{
  "repository_url": "https://github.com/user/repo",
  "branch": "main",
  "access_token": "github_pat_...",
  "platform": "github_actions",
  "options": {
    "include_tests": true,
    "include_security_scans": true,
    "deployment_target": "aws"
  }
}
```

**Response:**
```json
{
  "generation_id": "gen123",
  "status": "in_progress",
  "estimated_completion_time": "2023-04-15T14:40:00Z"
}
```

#### Get Generated Pipeline

```
GET /generate/{generation_id}
```

**Response:**
```json
{
  "generation_id": "gen123",
  "status": "completed",
  "repository": "https://github.com/user/repo",
  "platform": "github_actions",
  "pipeline_config": {
    "filename": ".github/workflows/ci.yml",
    "content": "name: CI\non:\n  push:\n    branches: [ main ]..."
  },
  "pull_request_url": "https://github.com/user/repo/pull/42",
  "completion_time": "2023-04-15T14:38:30Z"
}
```

#### Optimize Pipeline

```
POST /optimize
```

**Request:**
```json
{
  "repository_url": "https://github.com/user/repo",
  "branch": "main",
  "access_token": "github_pat_...",
  "pipeline_file": ".github/workflows/ci.yml",
  "optimization_goals": ["speed", "cost"]
}
```

**Response:**
```json
{
  "optimization_id": "opt123",
  "status": "in_progress",
  "estimated_completion_time": "2023-04-15T15:00:00Z"
}
```

#### Get Pipeline Templates

```
GET /templates
```

**Response:**
```json
{
  "templates": [
    {
      "id": "node_basic",
      "name": "Node.js Basic",
      "description": "Basic CI/CD pipeline for Node.js applications",
      "platforms": ["github_actions", "gitlab_ci", "jenkins"]
    },
    {
      "id": "python_django",
      "name": "Python Django",
      "description": "CI/CD pipeline for Django applications",
      "platforms": ["github_actions", "gitlab_ci", "jenkins"]
    }
  ]
}
```

## Security Enforcement

The Security Enforcement service scans for vulnerabilities and enforces security policies.

### Base URL (via API Gateway)

```
https://api.cicd-platform.example.com/v1/security
```

### Endpoints

#### Initiate Security Scan

```
POST /scan
```

**Request:**
```json
{
  "repository_url": "https://github.com/user/repo",
  "branch": "main",
  "access_token": "github_pat_...",
  "scan_type": "full",
  "scanners": ["trivy", "snyk", "zap"],
  "notification_email": "user@example.com"
}
```

**Response:**
```json
{
  "scan_id": "scan123",
  "status": "initiated",
  "estimated_completion_time": "2023-04-15T16:00:00Z"
}
```

#### Get Scan Status

```
GET /scan/{scan_id}
```

**Response:**
```json
{
  "scan_id": "scan123",
  "status": "in_progress",
  "progress": 45,
  "current_stage": "dependency_scanning",
  "estimated_completion_time": "2023-04-15T16:00:00Z"
}
```

#### Get Scan Results

```
GET /scan/{scan_id}/results
```

**Response:**
```json
{
  "scan_id": "scan123",
  "status": "completed",
  "repository": "https://github.com/user/repo",
  "branch": "main",
  "completion_time": "2023-04-15T15:55:30Z",
  "summary": {
    "total_vulnerabilities": 12,
    "critical": 2,
    "high": 3,
    "medium": 5,
    "low": 2
  },
  "vulnerabilities": [
    {
      "id": "CVE-2023-1234",
      "severity": "critical",
      "package": "lodash",
      "version": "4.17.15",
      "fixed_version": "4.17.21",
      "description": "Prototype pollution vulnerability in lodash...",
      "scanner": "snyk"
    }
  ],
  "report_url": "https://cicd-platform.example.com/reports/scan123.pdf"
}
```

#### List Vulnerabilities

```
GET /vulnerabilities
```

**Query Parameters:**
- `repository`: Repository URL
- `severity`: Filter by severity (critical, high, medium, low)
- `status`: Filter by status (open, fixed, ignored)
- `page`: Page number
- `limit`: Results per page

**Response:**
```json
{
  "total": 42,
  "page": 1,
  "limit": 10,
  "vulnerabilities": [
    {
      "id": "CVE-2023-1234",
      "severity": "critical",
      "package": "lodash",
      "version": "4.17.15",
      "fixed_version": "4.17.21",
      "description": "Prototype pollution vulnerability in lodash...",
      "repository": "https://github.com/user/repo",
      "status": "open",
      "discovered_at": "2023-04-10T12:00:00Z"
    }
  ]
}
```

#### Create/Update Security Policy

```
POST /policy
```

**Request:**
```json
{
  "name": "Production Policy",
  "description": "Security policy for production applications",
  "rules": [
    {
      "type": "vulnerability",
      "severity": "critical",
      "action": "block_deployment"
    },
    {
      "type": "vulnerability",
      "severity": "high",
      "action": "require_approval"
    },
    {
      "type": "secret_detection",
      "action": "block_deployment"
    }
  ],
  "applies_to": {
    "repositories": ["https://github.com/user/repo"],
    "branches": ["main", "production"]
  }
}
```

**Response:**
```json
{
  "policy_id": "policy123",
  "name": "Production Policy",
  "created_at": "2023-04-15T16:30:00Z",
  "updated_at": "2023-04-15T16:30:00Z"
}
```

#### Generate Compliance Report

```
GET /compliance
```

**Query Parameters:**
- `repository`: Repository URL
- `standard`: Compliance standard (e.g., "nist", "soc2", "pci")
- `format`: Report format (e.g., "pdf", "json", "html")

**Response:**
```json
{
  "report_id": "report123",
  "status": "generated",
  "repository": "https://github.com/user/repo",
  "standard": "nist",
  "compliance_score": 85,
  "report_url": "https://cicd-platform.example.com/reports/compliance/report123.pdf",
  "generated_at": "2023-04-15T17:00:00Z"
}
```

## Self-Healing Debugger

The Self-Healing Debugger service automatically detects and fixes pipeline errors.

### Base URL (via API Gateway)

```
https://api.cicd-platform.example.com/v1/debug
```

### Endpoints

#### Analyze Pipeline Logs

```
POST /analyze
```

**Request:**
```json
{
  "repository_url": "https://github.com/user/repo",
  "pipeline_id": "pipeline123",
  "access_token": "github_pat_...",
  "platform": "github_actions",
  "logs_url": "https://api.github.com/repos/user/repo/actions/runs/123456/logs"
}
```

**Response:**
```json
{
  "analysis_id": "debug123",
  "status": "in_progress",
  "estimated_completion_time": "2023-04-15T17:30:00Z"
}
```

#### Get Analysis Results

```
GET /analyze/{analysis_id}
```

**Response:**
```json
{
  "analysis_id": "debug123",
  "status": "completed",
  "repository": "https://github.com/user/repo",
  "pipeline_id": "pipeline123",
  "completion_time": "2023-04-15T17:28:30Z",
  "errors": [
    {
      "type": "dependency_error",
      "message": "Failed to install package 'react-router'",
      "location": "build_step",
      "line_number": 42,
      "confidence": 0.95,
      "suggested_fix": "Update package.json to use compatible version of react-router",
      "auto_fixable": true
    }
  ]
}
```

#### Apply Auto-Patch

```
POST /patch
```

**Request:**
```json
{
  "analysis_id": "debug123",
  "repository_url": "https://github.com/user/repo",
  "branch": "main",
  "access_token": "github_pat_...",
  "errors_to_fix": ["all"],
  "create_pull_request": true
}
```

**Response:**
```json
{
  "patch_id": "patch123",
  "status": "in_progress",
  "estimated_completion_time": "2023-04-15T17:45:00Z"
}
```

#### Get Patch Status

```
GET /patch/{patch_id}
```

**Response:**
```json
{
  "patch_id": "patch123",
  "status": "completed",
  "repository": "https://github.com/user/repo",
  "branch": "main",
  "completion_time": "2023-04-15T17:43:30Z",
  "fixes_applied": [
    {
      "error_type": "dependency_error",
      "file": "package.json",
      "change": "Updated react-router from ^5.0.0 to ^6.0.0"
    }
  ],
  "pull_request_url": "https://github.com/user/repo/pull/43"
}
```

#### List Error Patterns

```
GET /patterns
```

**Query Parameters:**
- `category`: Filter by category (dependency, permission, configuration, etc.)
- `platform`: Filter by CI/CD platform
- `page`: Page number
- `limit`: Results per page

**Response:**
```json
{
  "total": 150,
  "page": 1,
  "limit": 10,
  "patterns": [
    {
      "id": "pattern123",
      "category": "dependency",
      "subcategory": "npm",
      "pattern": "Failed to resolve dependencies",
      "description": "Node.js dependency resolution failure",
      "platforms": ["github_actions", "gitlab_ci", "jenkins"],
      "auto_fixable": true
    }
  ]
}
```

#### Start Interactive Debugging Session

```
POST /session
```

**Request:**
```json
{
  "repository_url": "https://github.com/user/repo",
  "pipeline_id": "pipeline123",
  "access_token": "github_pat_...",
  "platform": "github_actions"
}
```

**Response:**
```json
{
  "session_id": "session123",
  "status": "created",
  "websocket_url": "wss://api.cicd-platform.example.com/v1/debug/session/session123",
  "expires_at": "2023-04-15T19:00:00Z"
}
```

## WebSocket APIs

In addition to RESTful APIs, the platform provides WebSocket interfaces for real-time communication.

### Debug Session WebSocket

```
wss://api.cicd-platform.example.com/v1/debug/session/{session_id}
```

#### Messages from Client to Server

**Execute Command:**
```json
{
  "type": "command",
  "command": "ls -la",
  "working_directory": "/app"
}
```

**Apply Fix:**
```json
{
  "type": "apply_fix",
  "error_id": "error123",
  "fix_type": "automatic"
}
```

**End Session:**
```json
{
  "type": "end_session"
}
```

#### Messages from Server to Client

**Command Output:**
```json
{
  "type": "command_output",
  "output": "total 24\ndrwxr-xr-x  5 user  group  160 Apr 15 17:50 .\ndrwxr-xr-x  3 user  group   96 Apr 15 17:45 ..\n-rw-r--r--  1 user  group  284 Apr 15 17:50 package.json\n-rw-r--r--  1 user  group  954 Apr 15 17:50 README.md\ndrwxr-xr-x 10 user  group  320 Apr 15 17:50 src",
  "exit_code": 0
}
```

**Error Detection:**
```json
{
  "type": "error_detected",
  "error_id": "error123",
  "error_type": "dependency_error",
  "message": "Failed to install package 'react-router'",
  "location": "package.json",
  "suggested_fixes": [
    {
      "fix_id": "fix123",
      "description": "Update react-router to version 6.0.0",
      "file_changes": [
        {
          "file": "package.json",
          "change_type": "modify",
          "line_number": 15,
          "original": "\"react-router\": \"^5.0.0\"",
          "replacement": "\"react-router\": \"^6.0.0\""
        }
      ]
    }
  ]
}
```

**Fix Applied:**
```json
{
  "type": "fix_applied",
  "error_id": "error123",
  "fix_id": "fix123",
  "status": "success",
  "message": "Successfully updated package.json"
}
```

**Session Status:**
```json
{
  "type": "session_status",
  "status": "active",
  "expires_at": "2023-04-15T19:00:00Z"
}
```

### Pipeline Events WebSocket

```
wss://api.cicd-platform.example.com/v1/events/pipeline
```

#### Messages from Server to Client

**Pipeline Started:**
```json
{
  "type": "pipeline_started",
  "pipeline_id": "pipeline123",
  "repository": "https://github.com/user/repo",
  "branch": "main",
  "started_at": "2023-04-15T18:00:00Z"
}
```

**Pipeline Stage Completed:**
```json
{
  "type": "stage_completed",
  "pipeline_id": "pipeline123",
  "stage": "build",
  "status": "success",
  "duration": 45.2,
  "completed_at": "2023-04-15T18:01:30Z"
}
```

**Pipeline Completed:**
```json
{
  "type": "pipeline_completed",
  "pipeline_id": "pipeline123",
  "status": "success",
  "duration": 180.5,
  "completed_at": "2023-04-15T18:03:00Z",
  "summary": {
    "stages": 4,
    "successful_stages": 4,
    "failed_stages": 0
  }
}
```

**Pipeline Failed:**
```json
{
  "type": "pipeline_failed",
  "pipeline_id": "pipeline123",
  "status": "failed",
  "failed_stage": "test",
  "error_message": "Tests failed: 3 tests failed",
  "duration": 120.3,
  "completed_at": "2023-04-15T18:02:00Z",
  "debug_url": "https://api.cicd-platform.example.com/v1/debug/analyze/debug123"
}
```

## Error Handling

All APIs use consistent error handling with standard HTTP status codes and error response format.

### Error Response Format

```json
{
  "error": {
    "code": "invalid_request",
    "message": "The request was invalid",
    "details": [
      {
        "field": "email",
        "message": "Email is required"
      }
    ],
    "reference": "error123",
    "timestamp": "2023-04-15T18:30:00Z",
    "request_id": "req123"
  }
}
```

### Common Error Codes

- `invalid_request`: The request was invalid
- `authentication_required`: Authentication is required
- `invalid_credentials`: Invalid credentials provided
- `permission_denied`: Permission denied
- `resource_not_found`: Resource not found
- `rate_limit_exceeded`: Rate limit exceeded
- `internal_error`: Internal server error
- `service_unavailable`: Service temporarily unavailable

## API Versioning

The platform uses URL path versioning to ensure backward compatibility:

- `/v1/`: Version 1 (current)
- `/v2/`: Version 2 (future)

When a new version is released, the previous version will be maintained for a deprecation period of at least 6 months.

## OpenAPI Documentation

Each service provides OpenAPI (Swagger) documentation at:

```
https://api.cicd-platform.example.com/v1/{service}/docs
```

For example:
- API Gateway: `https://api.cicd-platform.example.com/v1/docs`
- Pipeline Generator: `https://api.cicd-platform.example.com/v1/pipeline/docs`
- Security Enforcement: `https://api.cicd-platform.example.com/v1/security/docs`
- Self-Healing Debugger: `https://api.cicd-platform.example.com/v1/debug/docs`

## API Changes and Deprecation

1. **Backward Compatibility**: We strive to maintain backward compatibility within a version
2. **Deprecation Notice**: APIs scheduled for deprecation will be marked with a deprecation notice
3. **Sunset Period**: Deprecated APIs will be supported for at least 6 months
4. **Change Notification**: Major changes will be announced at least 3 months in advance

## Rate Limiting

The API Gateway implements rate limiting to prevent abuse:

- **Anonymous Requests**: 60 requests per hour
- **Authenticated Requests**: 1000 requests per hour
- **Webhook Callbacks**: 3000 requests per hour

Rate limit headers are included in all responses:
- `X-RateLimit-Limit`: Total requests allowed in the period
- `X-RateLimit-Remaining`: Remaining requests in the period
- `X-RateLimit-Reset`: Time when the rate limit resets (Unix timestamp)

## Authentication and Authorization

All APIs (except public endpoints) require authentication using one of these methods:

1. **Bearer Token**: JWT token obtained via the login endpoint
   ```
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

2. **API Key**: For service-to-service communication
   ```
   X-API-Key: api_key_123456
   ```

3. **OAuth 2.0**: For third-party integrations
   ```
   Authorization: Bearer oauth_token_123456
   ```

## Pagination

List endpoints support pagination using the following query parameters:

- `page`: Page number (default: 1)
- `limit`: Results per page (default: 10, max: 100)

Paginated responses include metadata:

```json
{
  "total": 42,
  "page": 1,
  "limit": 10,
  "pages": 5,
  "items": [
    // Result items
  ]
}
```

## Filtering and Sorting

List endpoints support filtering and sorting using query parameters:

- Filtering: `field=value` (e.g., `status=active`)
- Sorting: `sort=field` or `sort=-field` for descending order (e.g., `sort=-created_at`)

## CORS Support

The API Gateway supports Cross-Origin Resource Sharing (CORS) with the following headers:

- `Access-Control-Allow-Origin`: Configured origins or `*` for public APIs
- `Access-Control-Allow-Methods`: `GET, POST, PUT, DELETE, OPTIONS`
- `Access-Control-Allow-Headers`: `Content-Type, Authorization, X-API-Key`
