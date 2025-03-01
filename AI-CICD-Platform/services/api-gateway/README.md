# API Gateway Service

The API Gateway service is a central entry point for all client requests to the AI CI/CD Platform. It handles authentication, authorization, routing, rate limiting, circuit breaking, and caching.

## Features

- **Authentication & Authorization**: Secure access to services with JWT tokens, API keys, and role-based permissions
- **Enhanced Authentication**: Multi-factor authentication, refresh tokens, and rate limiting for auth endpoints
- **Service Routing**: Dynamic routing of requests to appropriate microservices
- **Rate Limiting**: Prevent abuse by limiting request rates with advanced protection mechanisms
- **Circuit Breaking**: Protect services from cascading failures
- **Enhanced Caching**: Improve performance with advanced caching strategies, including user and role-specific caching
- **Metrics & Monitoring**: Track service health and performance
- **API Versioning**: Support multiple API versions with version negotiation and backward compatibility

## Architecture

The API Gateway is built with FastAPI and consists of several core services:

- **AuthService**: Handles authentication and authorization
- **RoutingService**: Routes requests to appropriate services
- **ResilienceService**: Implements rate limiting and circuit breaking
- **MetricsService**: Collects and reports metrics
- **VersionService**: Manages API versioning and negotiation
- **ApiKeyService**: Handles API key management and validation

## API Versioning

The API Gateway implements a comprehensive API versioning system that allows for multiple API versions to coexist, providing backward compatibility while enabling evolution of the API.

### Version Negotiation

Clients can specify the desired API version in several ways:

1. **URL Path**: `/api/v2/service/endpoint`
2. **Accept-Version Header**: `Accept-Version: 2`
3. **Query Parameter**: `?version=2` or `?v=2`

The API Gateway uses a configurable negotiation strategy to determine which version to use:

- **Header First**: Prioritizes the Accept-Version header, then URL path, then query parameter
- **Path First**: Prioritizes the URL path, then Accept-Version header, then query parameter
- **Query First**: Prioritizes the query parameter, then Accept-Version header, then URL path

If no version is specified, the latest version is used.

### Version Response Headers

The API Gateway adds version information to response headers:

- **X-API-Version**: The version used for the request
- **X-API-Latest-Version**: The latest available version (if different from the requested version)
- **Warning**: Deprecation warning (if the requested version is deprecated)
- **Sunset**: Sunset date (if the requested version has a planned end-of-life)
- **Link**: Link to API documentation for the version

### Version Compatibility

The API Gateway supports version compatibility in several ways:

1. **Version-specific Endpoints**: Different versions can have different endpoint implementations
2. **Version-specific Permissions**: Different versions can have different permission requirements
3. **Version Transformation**: Request and response data can be transformed between versions
4. **Version Restrictions**: Users and API keys can be restricted to specific versions

### API Version Management

API versions are managed with the following attributes:

- **Version**: The version identifier (e.g., "1", "2")
- **Release Date**: When the version was released
- **Sunset Date**: When the version will be retired (if applicable)
- **Deprecated**: Whether the version is deprecated
- **Supported Features**: Features supported by this version
- **Changes from Previous**: Changes from the previous version
- **Documentation URL**: Link to documentation for this version

## Enhanced Authentication Flow

The API Gateway implements a robust authentication system with multiple methods and security features:

### JWT Authentication with Token Management

JSON Web Tokens (JWT) are used for stateless authentication with enhanced security features:

- **Token Blacklisting**: Revoked tokens are tracked to prevent unauthorized use
- **Token Rotation**: Refresh tokens are rotated on use to prevent token theft
- **Token Reuse Detection**: Detects and prevents refresh token reuse
- **JTI Claim**: Unique token identifiers for tracking and revocation
- **Redis-backed Storage**: Efficient token management with Redis (with in-memory fallback)
- **Version-specific Tokens**: Tokens can be restricted to specific API versions

Each token contains:
- User ID and profile information
- Roles and permissions
- Token expiration time
- Token ID (jti)
- Issuance time
- Token type (access, refresh)
- API version information

### API Key Authentication

API keys provide an alternative authentication method with the following features:

- **Secure Storage**: API keys are securely hashed before storage
- **Prefix-based Lookup**: Fast lookup using key prefixes
- **Service Restrictions**: Keys can be restricted to specific services
- **Version Restrictions**: Keys can be restricted to specific API versions
- **Permission Scoping**: Keys can have specific permissions
- **Expiration**: Keys can have expiration dates
- **Revocation**: Keys can be revoked at any time
- **User Association**: Keys are associated with specific users
- **Metadata**: Keys can have additional metadata for tracking and auditing

### Multi-Factor Authentication (MFA)

The API Gateway supports multi-factor authentication for enhanced security:

- Time-based One-Time Password (TOTP)
- SMS verification (planned)
- Email verification (planned)

### Refresh Tokens

Refresh tokens allow clients to obtain new access tokens without requiring the user to re-authenticate.

## API Endpoints

### Version Information Endpoints

#### List API Versions

```
GET /api/versions
```

Response:
```json
{
  "versions": [
    {
      "version": "1",
      "release_date": "2024-01-01T00:00:00Z",
      "sunset_date": null,
      "deprecated": false,
      "supported_features": ["basic_auth", "mfa", "token_refresh"],
      "documentation_url": "/docs/v1"
    },
    {
      "version": "2",
      "release_date": "2025-02-01T00:00:00Z",
      "sunset_date": null,
      "deprecated": false,
      "supported_features": ["basic_auth", "mfa", "token_refresh", "enhanced_auth", "api_keys", "version_negotiation"],
      "documentation_url": "/docs/v2"
    }
  ],
  "latest_version": "2"
}
```

### Authentication Endpoints

#### Login

```
POST /api/v{version}/auth/token
```

Request:
```json
{
  "username": "string",
  "password": "string"
}
```

Response (without MFA):
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "string",
  "api_version": "2"
}
```

Response (with MFA required):
```json
{
  "status": "mfa_required",
  "token": "string",
  "mfa_methods": ["totp"],
  "message": "MFA verification required",
  "api_version": "2"
}
```

#### MFA Verification

```
POST /api/v{version}/auth/mfa/verify
```

Request:
```json
{
  "code": "string",
  "token": "string"
}
```

Response:
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "string",
  "api_version": "2"
}
```

#### MFA Setup

```
POST /api/v{version}/auth/mfa/setup
```

Request:
```json
{
  "method": "totp"
}
```

Response:
```json
{
  "status": "success",
  "method": "totp",
  "data": {
    "secret": "string",
    "provisioning_uri": "string"
  },
  "api_version": "2"
}
```

#### Refresh Token

```
POST /api/v{version}/auth/refresh
```

Request:
```json
{
  "refresh_token": "string"
}
```

Response:
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "string",
  "api_version": "2"
}
```

#### Logout

```
POST /api/v{version}/auth/logout
```

Request:
```json
{
  "token": "string"
}
```

Response:
```json
{
  "status": "success",
  "message": "Token revoked successfully",
  "api_version": "2"
}
```

### API Key Endpoints

#### Create API Key

```
POST /api/v{version}/auth/api-keys
```

Request:
```json
{
  "name": "My API Key",
  "permissions": ["read:all", "write:own"],
  "allowed_versions": ["1", "2"],
  "allowed_services": ["pipeline-generator", "security-enforcement"],
  "expires_in_days": 30,
  "metadata": {
    "purpose": "CI/CD integration"
  }
}
```

Response:
```json
{
  "status": "success",
  "api_key": "ak_1234567890abcdef...",
  "key_id": "key_1234567890",
  "name": "My API Key",
  "created_at": "2025-02-26T00:00:00Z",
  "expires_at": "2025-03-28T00:00:00Z",
  "api_version": "2"
}
```

#### List API Keys

```
GET /api/v{version}/auth/api-keys
```

Response:
```json
{
  "api_keys": [
    {
      "key_id": "key_1234567890",
      "key_prefix": "ak_12345678",
      "name": "My API Key",
      "created_at": "2025-02-26T00:00:00Z",
      "expires_at": "2025-03-28T00:00:00Z",
      "last_used": "2025-02-26T01:00:00Z",
      "enabled": true,
      "permissions": ["read:all", "write:own"],
      "allowed_versions": ["1", "2"],
      "allowed_services": ["pipeline-generator", "security-enforcement"]
    }
  ],
  "api_version": "2"
}
```

#### Revoke API Key

```
DELETE /api/v{version}/auth/api-keys/{key_id}
```

Response:
```json
{
  "status": "success",
  "message": "API key revoked successfully",
  "api_version": "2"
}
```

### Service Endpoints

All service endpoints are accessed through the API Gateway using the following pattern:

```
{METHOD} /api/v{version}/{service}/{endpoint}
```

For example:
```
POST /api/v2/pipeline-generator/generate
```

## Configuration

The API Gateway can be configured using environment variables or a `.env` file:

```
# Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30
JWT_REFRESH_EXPIRATION_DAYS=7
JWT_BLACKLIST_ENABLED=true
JWT_BLACKLIST_TOKEN_CHECKS=access,refresh

# Token Security
TOKEN_ROTATION_ENABLED=true
TOKEN_REUSE_DETECTION_ENABLED=true
TOKEN_JTI_CLAIM_ENABLED=true

# API Versioning
DEFAULT_API_VERSION=2
VERSION_NEGOTIATION_STRATEGY=header_first
INCLUDE_VERSION_HEADERS=true

# OAuth2 Configuration
OAUTH2_ISSUER_URL=https://your-oauth-provider.com
OAUTH2_CLIENT_ID=your-client-id
OAUTH2_CLIENT_SECRET=your-client-secret
OAUTH2_SCOPES=read,write,admin

# SAML Configuration
SAML_ENABLED=false
SAML_IDP_METADATA_URL=https://your-idp.com/metadata
SAML_SP_ENTITY_ID=your-entity-id
SAML_ACS_URL=https://your-service.com/saml/acs

# Social Login Configuration
SOCIAL_LOGIN_ENABLED=false
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Circuit Breaking
CIRCUIT_BREAKER_ENABLED=true
FAILURE_THRESHOLD=5
RECOVERY_TIMEOUT=30

# Redis (for rate limiting & caching)
REDIS_URL=redis://localhost:6379
REDIS_POOL_SIZE=10

# Caching
CACHE_ENABLED=true
CACHE_TTL=300
```

## Development

### Prerequisites

- Python 3.9+
- Redis (for rate limiting and caching)

### Installation

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the API Gateway
uvicorn main:app --reload
```

### Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=.
```

## Enhanced Caching Strategy

The API Gateway implements a sophisticated caching system to improve performance and reduce load on backend services:

### Caching Features

- **Redis-backed Cache**: High-performance caching with Redis (with in-memory fallback)
- **Configurable TTL**: Different cache durations for different types of content
- **User-specific Caching**: Cache responses per user when content varies by user
- **Role-specific Caching**: Cache responses per role when content varies by role
- **Version-specific Caching**: Cache responses per API version
- **Cache Invalidation**: Targeted cache invalidation by service, endpoint, or pattern
- **Cache Headers**: Proper cache control headers for HTTP caching
- **Cache Statistics**: Monitoring of cache hit rates and performance
- **Size Limits**: Prevent caching of oversized responses
- **Conditional Caching**: Smart decisions about what to cache based on response characteristics

### Cache Configuration Types

The API Gateway supports multiple cache configuration types:

- **default**: Standard caching (5 minutes)
- **short_term**: Short-lived cache (1 minute)
- **medium_term**: Medium-lived cache (10 minutes)
- **long_term**: Long-lived cache (1 hour)
- **user_specific**: User-specific cache (5 minutes)
- **role_specific**: Role-specific cache (10 minutes)
- **no_cache**: Explicitly disable caching

### Configuring Caching for Endpoints

Caching can be configured per endpoint in the service routes configuration:

```python
SERVICE_ROUTES = {
    "example-service": {
        "prefix": "/api/v1/example",
        "endpoints": {
            "get-data": {
                "method": "GET",
                "path": "/data",
                "cache_enabled": True,
                "cache_config": "medium_term",
                "cache_vary_by_user": False,
                "cache_vary_by_role": True
            }
        }
    }
}
```

## Rate Limiting Refinement

The API Gateway implements advanced rate limiting features to protect authentication endpoints from abuse:

### Authentication Rate Limiting

- **IP-based Rate Limiting**: Limits authentication attempts based on client IP address
- **Username-based Rate Limiting**: Limits authentication attempts for specific usernames
- **Progressive Lockouts**: Increases lockout duration with consecutive failed attempts
- **Differentiated Rate Limits**: Separate rate limits for login, MFA verification, and token refresh
- **Retry-After Headers**: Provides clients with information on when to retry
- **Configurable Thresholds**: Customizable limits, windows, and lockout durations
- **Version-specific Rate Limits**: Different rate limits for different API versions

### Rate Limit Configuration

Rate limiting can be configured using environment variables:

```
# Authentication Rate Limiting
AUTH_RATE_LIMIT_ENABLED=true
AUTH_RATE_LIMIT_MAX_ATTEMPTS=5
AUTH_RATE_LIMIT_WINDOW=15
AUTH_RATE_LIMIT_LOCKOUT_DURATION=30
AUTH_RATE_LIMIT_PROGRESSIVE_LOCKOUT=true
AUTH_RATE_LIMIT_TRACK_BY_USERNAME=true
AUTH_RATE_LIMIT_TRACK_BY_IP=true
```

## Security Considerations

- JWT tokens are signed using HMAC-SHA256 (HS256) by default
- Tokens include expiration times to limit their validity
- Refresh tokens are long-lived but can be revoked
- Token blacklisting prevents use of revoked tokens
- Token rotation prevents refresh token theft
- Rate limiting is applied to authentication endpoints to prevent brute force attacks
- Progressive lockouts provide increasing protection against repeated attacks
- Multi-factor authentication provides an additional layer of security
- Token IDs (jti) are used to uniquely identify tokens for revocation
- Cache varies by user and role to prevent information leakage
- OAuth2 and SAML support for enterprise authentication needs
- Social login options for improved user experience
- API keys are securely hashed using PBKDF2 with a unique salt
- Version-specific permissions allow for granular access control
