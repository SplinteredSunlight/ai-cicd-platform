from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid

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

class UserRole(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"

class AuthToken(BaseModel):
    """Model for authentication tokens"""
    access_token: str
    token_type: TokenType
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None

class UserInfo(BaseModel):
    """Model for user information"""
    user_id: str
    username: str
    email: str
    roles: List[UserRole]
    permissions: List[str]
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

    @property
    def is_exceeded(self) -> bool:
        return self.request_count >= self.limit

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.request_count)

class CacheEntry(BaseModel):
    """Model for cache entries"""
    key: str
    value: Any
    expires_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RequestContext(BaseModel):
    """Model for request context"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: str
    endpoint: str
    user: Optional[UserInfo] = None
    trace_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ServiceResponse(BaseModel):
    """Model for service responses"""
    status_code: int
    headers: Dict[str, str] = Field(default_factory=dict)
    body: Any
    duration_ms: float
    cached: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ErrorResponse(BaseModel):
    """Model for error responses"""
    status_code: int
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

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
                }
            }
        }
