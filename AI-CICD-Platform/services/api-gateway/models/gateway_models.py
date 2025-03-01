from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from enum import Enum
import uuid

class VersionNegotiationStrategy(str, Enum):
    HEADER_FIRST = "header_first"
    PATH_FIRST = "path_first"
    QUERY_FIRST = "query_first"

class ApiVersion(BaseModel):
    """Model for API version information"""
    version: str
    release_date: datetime
    sunset_date: Optional[datetime] = None
    deprecated: bool = False
    supported_features: List[str] = Field(default_factory=list)
    changes_from_previous: Optional[List[str]] = None
    documentation_url: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "version": "2",
                "release_date": "2025-02-01T00:00:00Z",
                "sunset_date": None,
                "deprecated": False,
                "supported_features": ["basic_auth", "mfa", "token_refresh", "api_keys"],
                "changes_from_previous": ["Added API key authentication", "Enhanced token security"],
                "documentation_url": "/docs/v2"
            }
        }

class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"

class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class TokenType(str, Enum):
    BEARER = "bearer"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    SAML = "saml"

class MFAMethod(str, Enum):
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"
    HARDWARE_KEY = "hardware_key"
    BIOMETRIC = "biometric"

class UserRole(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"
    SECURITY = "security"
    AUDITOR = "auditor"

class AuthProvider(str, Enum):
    INTERNAL = "internal"
    OAUTH2 = "oauth2"
    SAML = "saml"
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"
    OKTA = "okta"
    AUTH0 = "auth0"

class AuthToken(BaseModel):
    """Model for authentication tokens"""
    access_token: str
    token_type: TokenType
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    id_token: Optional[str] = None  # For OpenID Connect
    token_id: Optional[str] = None  # JTI claim
    issued_at: Optional[datetime] = None
    not_before: Optional[datetime] = None
    provider: Optional[AuthProvider] = None
    api_version: Optional[str] = None  # API version this token is valid for
    version_scope: Optional[List[str]] = None  # API versions this token can access

class OAuth2Token(BaseModel):
    """Model for OAuth2 tokens"""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    id_token: Optional[str] = None  # For OpenID Connect
    provider: AuthProvider

class SAMLToken(BaseModel):
    """Model for SAML tokens"""
    assertion: str
    provider: AuthProvider
    session_index: Optional[str] = None
    not_on_or_after: Optional[datetime] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)

class UserInfo(BaseModel):
    """Model for user information"""
    user_id: str
    username: str
    email: str
    roles: List[UserRole]
    permissions: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    auth_provider: Optional[AuthProvider] = None
    mfa_enabled: bool = False
    mfa_methods: List[MFAMethod] = Field(default_factory=list)
    last_login: Optional[datetime] = None
    last_password_change: Optional[datetime] = None
    account_locked: bool = False
    account_expires: Optional[datetime] = None
    external_ids: Dict[str, str] = Field(default_factory=dict)  # For mapping to external identity providers
    api_keys: List[str] = Field(default_factory=list)  # API keys associated with this user
    allowed_versions: Optional[List[str]] = None  # If None, all versions are allowed
    version_specific_permissions: Dict[str, List[str]] = Field(default_factory=dict)  # Version -> permissions

class ApiKey(BaseModel):
    """Model for API keys"""
    key_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key_prefix: str
    key_hash: str
    user_id: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    enabled: bool = True
    permissions: List[str] = Field(default_factory=list)
    allowed_versions: Optional[List[str]] = None  # If None, all versions are allowed
    allowed_services: Optional[List[str]] = None  # If None, all services are allowed
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ServiceEndpoint(BaseModel):
    """Model for service endpoint configuration"""
    method: str
    path: str
    rate_limit: int
    cache_enabled: bool
    timeout: Optional[int] = None
    circuit_breaker: Optional[Dict] = None
    auth_required: bool = True
    roles_required: List[UserRole] = []
    min_api_version: Optional[str] = None  # Minimum API version required
    max_api_version: Optional[str] = None  # Maximum API version supported
    version_specific_config: Dict[str, Dict[str, Any]] = Field(default_factory=dict)  # Version-specific configurations

class ServiceRegistration(BaseModel):
    """Model for service registration"""
    service_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    version: str
    url: str
    health_check_url: str
    status: ServiceStatus = ServiceStatus.HEALTHY
    endpoints: Dict[str, ServiceEndpoint]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    last_health_check: Optional[datetime] = None
    supported_api_versions: List[str] = Field(default_factory=list)  # API versions supported by this service

class CircuitBreakerState(BaseModel):
    """Model for circuit breaker state"""
    service_id: str
    state: CircuitState
    failure_count: int
    last_failure: Optional[datetime] = None
    recovery_time: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RateLimitState(BaseModel):
    """Model for rate limit state"""
    key: str
    window_start: datetime
    request_count: int
    window_size: int
    limit: int
    failed_count: int = 0
    successful_count: int = 0
    consecutive_failures: int = 0
    last_attempt_time: Optional[datetime] = None
    lockout_until: Optional[datetime] = None

    @property
    def is_exceeded(self) -> bool:
        return self.request_count >= self.limit

    @property
    def is_locked_out(self) -> bool:
        if not self.lockout_until:
            return False
        return datetime.utcnow() < self.lockout_until

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.request_count)
    
    @property
    def failure_ratio(self) -> float:
        if self.request_count == 0:
            return 0.0
        return self.failed_count / self.request_count

class CacheEntry(BaseModel):
    """Model for cache entries"""
    key: str
    value: Any
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    user_id: Optional[str] = None
    role: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    api_version: Optional[str] = None  # API version this cache entry is for

class RequestContext(BaseModel):
    """Model for request context"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: str
    endpoint: str
    user: Optional[UserInfo] = None
    trace_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    api_version: str = "1"  # API version for this request
    is_version_explicit: bool = False  # Whether the version was explicitly specified

class ServiceResponse(BaseModel):
    """Model for service responses"""
    status_code: int
    headers: Dict[str, str] = Field(default_factory=dict)
    body: Any
    duration_ms: float
    cached: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    api_version: Optional[str] = None  # API version this response is for

class ErrorResponse(BaseModel):
    """Model for error responses"""
    status_code: int
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    api_version: Optional[str] = None  # API version this error is for

class MetricsSnapshot(BaseModel):
    """Model for service metrics"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service_id: str
    requests_total: int
    requests_failed: int
    response_time_ms: float
    cache_hits: int
    cache_misses: int
    rate_limit_hits: int
    circuit_breaker_trips: int
    active_connections: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    api_version_metrics: Dict[str, Dict[str, int]] = Field(default_factory=dict)  # Version-specific metrics

class AuditLog(BaseModel):
    """Model for audit logging"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str
    user_id: Optional[str]
    service: str
    endpoint: str
    action: str
    status: str
    details: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    auth_provider: Optional[AuthProvider] = None
    session_id: Optional[str] = None
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    severity: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    api_version: Optional[str] = None  # API version used for this request

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-02-23T12:15:53Z",
                "request_id": "req_123",
                "user_id": "user_456",
                "service": "pipeline-generator",
                "endpoint": "/generate",
                "action": "CREATE_PIPELINE",
                "status": "success",
                "details": {
                    "pipeline_id": "pipe_789",
                    "template": "nodejs-app"
                },
                "api_version": "2"
            }
        }

class TokenBlacklist(BaseModel):
    """Model for blacklisted tokens"""
    token_id: str
    user_id: str
    expires_at: datetime
    revoked_at: datetime = Field(default_factory=datetime.utcnow)
    revocation_reason: Optional[str] = None
    api_version: Optional[str] = None  # API version this token was for

class MFAVerification(BaseModel):
    """Model for MFA verification"""
    user_id: str
    method: MFAMethod
    code: str
    verification_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    verified: bool = False
    verified_at: Optional[datetime] = None
    attempts: int = 0
    max_attempts: int = 3
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MFASetup(BaseModel):
    """Model for MFA setup"""
    user_id: str
    method: MFAMethod
    secret: str
    verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    verified_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class OAuth2Config(BaseModel):
    """Model for OAuth2 configuration"""
    provider: AuthProvider
    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scope: List[str] = ["openid", "profile", "email"]
    redirect_uri: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SAMLConfig(BaseModel):
    """Model for SAML configuration"""
    provider: AuthProvider
    idp_metadata_url: str
    sp_entity_id: str
    acs_url: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class VersionedEndpoint(BaseModel):
    """Model for versioned endpoint configuration"""
    path: str
    min_version: str
    max_version: Optional[str] = None
    handler_path: str  # Path to the handler function
    deprecated: bool = False
    sunset_date: Optional[datetime] = None
    migration_path: Optional[str] = None  # Path to the new endpoint if deprecated
