from fastapi import FastAPI, HTTPException, Depends, Request, Response, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime, timedelta

from .config import get_settings, SERVICE_ROUTES, ERROR_TEMPLATES, CACHE_CONFIGS
from .models.gateway_models import (
    RequestContext,
    ServiceResponse,
    ErrorResponse,
    UserInfo,
    MFAMethod,
    ApiKey,
    VersionNegotiationStrategy,
    ApiVersion
)
from .services.auth_service import AuthService
from .services.resilience_service import ResilienceService
from .services.routing_service import RoutingService
from .services.metrics_service import MetricsService
from .services.cache_service import CacheService
from .services.token_service import TokenService
from .services.version_service import VersionService
from .services.api_key_service import ApiKeyService
from .services.websocket_service import WebSocketService, WebSocketEvent

# Configure structured logging
logger = structlog.get_logger()

app = FastAPI(
    title="AI CI/CD Platform API Gateway",
    description="API Gateway for AI-powered CI/CD Automation & Security Platform",
    version="0.2.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GatewayService:
    def __init__(self):
        self.settings = get_settings()
        self.auth_service = AuthService()
        self.resilience_service = ResilienceService()
        self.routing_service = RoutingService()
        self.metrics_service = MetricsService()
        self.cache_service = CacheService()
        self.token_service = TokenService()
        self.version_service = VersionService()
        self.api_key_service = ApiKeyService()
        self.websocket_service = WebSocketService()

    def get_auth_service(self) -> AuthService:
        return self.auth_service

    def get_resilience_service(self) -> ResilienceService:
        return self.resilience_service

    def get_routing_service(self) -> RoutingService:
        return self.routing_service

    def get_metrics_service(self) -> MetricsService:
        return self.metrics_service
        
    def get_cache_service(self) -> CacheService:
        return self.cache_service
        
    def get_token_service(self) -> TokenService:
        return self.token_service
        
    def get_version_service(self) -> VersionService:
        return self.version_service
        
    def get_api_key_service(self) -> ApiKeyService:
        return self.api_key_service
        
    def get_websocket_service(self) -> WebSocketService:
        return self.websocket_service

gateway_service = GatewayService()

# Mount WebSocket service
gateway_service.websocket_service.mount_to_app(app, "/ws")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    await gateway_service.auth_service.cleanup()
    await gateway_service.resilience_service.cleanup()
    await gateway_service.routing_service.cleanup()
    await gateway_service.metrics_service.cleanup()
    await gateway_service.cache_service.cleanup()
    await gateway_service.token_service.cleanup()

@app.post("/api/v{version}/events/emit")
async def emit_event(
    version: str,
    event: WebSocketEvent,
    current_user: UserInfo = Depends(get_current_user),
    websocket_service: WebSocketService = Depends(gateway_service.get_websocket_service),
    version_service: VersionService = Depends(gateway_service.get_version_service)
):
    """Emit a WebSocket event to connected clients"""
    # Validate API version
    if not await version_service.is_version_supported(version):
        raise HTTPException(
            status_code=400,
            detail=f"API version {version} is not supported"
        )
    
    # Check authentication
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    # Check permissions (only admins can emit events)
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )
    
    # Emit event
    await websocket_service.emit_event(event)
    
    return {"status": "success", "message": "Event emitted successfully"}

@app.get("/")
async def root(
    request: Request,
    accept_version: Optional[str] = Header(None),
    version_service: VersionService = Depends(gateway_service.get_version_service)
):
    # Negotiate API version
    api_version, is_explicit = await version_service.negotiate_version(
        request, 
        accept_version
    )
    
    # Create response
    response = {
        "status": "healthy",
        "service": "api-gateway",
        "version": "0.2.0",
        "api_version": api_version
    }
    
    # Create FastAPI response to add headers
    fastapi_response = JSONResponse(content=response)
    await version_service.add_version_headers(fastapi_response, api_version)
    
    return fastapi_response

@app.get("/api/versions")
async def list_versions(
    version_service: VersionService = Depends(gateway_service.get_version_service)
):
    """List available API versions"""
    # Get all versions
    versions = version_service._versions
    
    # Format response
    response = {
        "versions": [
            {
                "version": v.version,
                "release_date": v.release_date.isoformat(),
                "sunset_date": v.sunset_date.isoformat() if v.sunset_date else None,
                "deprecated": v.deprecated,
                "supported_features": v.supported_features,
                "documentation_url": v.documentation_url
            }
            for v in versions.values()
        ],
        "latest_version": (await version_service.get_latest_version()).version
    }
    
    return response

@app.post("/api/v{version}/auth/token")
async def login(
    version: str,
    username: str,
    password: str,
    request: Request,
    auth_service: AuthService = Depends(gateway_service.get_auth_service),
    version_service: VersionService = Depends(gateway_service.get_version_service)
):
    """Get authentication token"""
    # Validate API version
    if not await version_service.is_version_supported(version):
        raise HTTPException(
            status_code=400,
            detail=f"API version {version} is not supported"
        )
    
    user = await auth_service.authenticate_user(username, password, request)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    
    # Check if user is allowed to use this API version
    if user.allowed_versions and version not in user.allowed_versions:
        raise HTTPException(
            status_code=403,
            detail=f"User is not authorized to use API version {version}"
        )
    
    # Check if MFA is enabled for this user
    if user.metadata.get("mfa_enabled", False):
        # Return a partial token that can be used only for MFA verification
        partial_token = await auth_service.create_access_token(
            user,
            expires_delta=timedelta(minutes=5),  # Short-lived token for MFA
            include_refresh_token=False,
            additional_claims={"api_version": version}
        )
        
        response = {
            "status": "mfa_required",
            "token": partial_token.access_token,
            "mfa_methods": user.metadata.get("mfa_methods", []),
            "message": "MFA verification required",
            "api_version": version
        }
        
        # Create FastAPI response to add headers
        fastapi_response = JSONResponse(content=response)
        await version_service.add_version_headers(fastapi_response, version)
        
        return fastapi_response
    
    # If MFA is not enabled, return a full token
    token = await auth_service.create_access_token(
        user,
        additional_claims={"api_version": version}
    )
    
    response = {
        "access_token": token.access_token,
        "token_type": token.token_type,
        "expires_in": token.expires_in,
        "refresh_token": token.refresh_token,
        "api_version": version
    }
    
    # Create FastAPI response to add headers
    fastapi_response = JSONResponse(content=response)
    await version_service.add_version_headers(fastapi_response, version)
    
    return fastapi_response

@app.post("/api/v{version}/auth/mfa/verify")
async def verify_mfa(
    version: str,
    code: str,
    token: str,
    request: Request,
    auth_service: AuthService = Depends(gateway_service.get_auth_service),
    version_service: VersionService = Depends(gateway_service.get_version_service)
):
    """Verify MFA code and get full access token"""
    # Validate API version
    if not await version_service.is_version_supported(version):
        raise HTTPException(
            status_code=400,
            detail=f"API version {version} is not supported"
        )
    
    # Verify the partial token
    user = await auth_service.verify_token(token)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
    
    # Verify the MFA code
    if not await auth_service.verify_mfa(user.user_id, code, request):
        raise HTTPException(
            status_code=401,
            detail="Invalid MFA code"
        )
    
    # Return a full token
    token = await auth_service.create_access_token(
        user,
        additional_claims={"api_version": version}
    )
    
    response = {
        "access_token": token.access_token,
        "token_type": token.token_type,
        "expires_in": token.expires_in,
        "refresh_token": token.refresh_token,
        "api_version": version
    }
    
    # Create FastAPI response to add headers
    fastapi_response = JSONResponse(content=response)
    await version_service.add_version_headers(fastapi_response, version)
    
    return fastapi_response

@app.post("/api/v{version}/auth/mfa/setup")
async def setup_mfa(
    version: str,
    method: MFAMethod,
    current_user: UserInfo = Depends(get_current_user),
    auth_service: AuthService = Depends(gateway_service.get_auth_service),
    version_service: VersionService = Depends(gateway_service.get_version_service)
):
    """Set up MFA for the current user"""
    # Validate API version
    if not await version_service.is_version_supported(version):
        raise HTTPException(
            status_code=400,
            detail=f"API version {version} is not supported"
        )
    
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    # Set up MFA
    mfa_data = await auth_service.setup_mfa(current_user.user_id, method)
    
    response = {
        "status": "success",
        "method": method,
        "data": mfa_data,
        "api_version": version
    }
    
    # Create FastAPI response to add headers
    fastapi_response = JSONResponse(content=response)
    await version_service.add_version_headers(fastapi_response, version)
    
    return fastapi_response

@app.post("/api/v{version}/auth/refresh")
async def refresh_token(
    version: str,
    refresh_token: str,
    request: Request,
    auth_service: AuthService = Depends(gateway_service.get_auth_service),
    version_service: VersionService = Depends(gateway_service.get_version_service)
):
    """Refresh access token using refresh token"""
    # Validate API version
    if not await version_service.is_version_supported(version):
        raise HTTPException(
            status_code=400,
            detail=f"API version {version} is not supported"
        )
    
    try:
        new_token = await auth_service.refresh_access_token(refresh_token, request)
        
        # Add API version to token claims
        new_token.api_version = version
        
        response = {
            "access_token": new_token.access_token,
            "token_type": new_token.token_type,
            "expires_in": new_token.expires_in,
            "refresh_token": new_token.refresh_token,
            "api_version": version
        }
        
        # Create FastAPI response to add headers
        fastapi_response = JSONResponse(content=response)
        await version_service.add_version_headers(fastapi_response, version)
        
        return fastapi_response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

@app.post("/api/v{version}/auth/logout")
async def logout(
    version: str,
    token: str,
    auth_service: AuthService = Depends(gateway_service.get_auth_service),
    version_service: VersionService = Depends(gateway_service.get_version_service)
):
    """Logout and revoke token"""
    # Validate API version
    if not await version_service.is_version_supported(version):
        raise HTTPException(
            status_code=400,
            detail=f"API version {version} is not supported"
        )
    
    await auth_service.revoke_token(token)
    
    response = {
        "status": "success", 
        "message": "Token revoked successfully",
        "api_version": version
    }
    
    # Create FastAPI response to add headers
    fastapi_response = JSONResponse(content=response)
    await version_service.add_version_headers(fastapi_response, version)
    
    return fastapi_response

async def get_current_user(
    request: Request,
    auth_service: AuthService = Depends(gateway_service.get_auth_service),
    api_key_service: ApiKeyService = Depends(gateway_service.get_api_key_service),
    version_service: VersionService = Depends(gateway_service.get_version_service)
) -> Optional[UserInfo]:
    """Get current user from token or API key"""
    # Try to get API version from request path
    path = request.url.path
    version = None
    match = version_service._extract_version_from_path(path)
    if match:
        version = match
    
    # Try Authorization header first (Bearer token)
    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            scheme, token = auth_header.split()
            if scheme.lower() == "bearer":
                user = await auth_service.verify_token(token)
                if user:
                    # Check if token is valid for this API version
                    token_version = user.metadata.get("api_version")
                    if token_version and version and token_version != version:
                        return None
                    
                    return user
        except:
            pass
    
    # Try X-API-Key header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        # Extract service from path
        service = None
        path_parts = path.split("/")
        if len(path_parts) > 3:  # /api/v1/service/...
            service = path_parts[3]
        
        # Validate API key
        result = await api_key_service.validate_api_key(api_key, service, version)
        if result:
            api_key_record, user = result
            return user
    
    return None

@app.api_route("/api/v{version}/{service}/{endpoint:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_request_versioned(
    version: str,
    service: str,
    endpoint: str,
    request: Request,
    response: Response,
    accept_version: Optional[str] = Header(None),
    current_user: Optional[UserInfo] = Depends(get_current_user),
    auth_service: AuthService = Depends(gateway_service.get_auth_service),
    resilience_service: ResilienceService = Depends(gateway_service.get_resilience_service),
    routing_service: RoutingService = Depends(gateway_service.get_routing_service),
    metrics_service: MetricsService = Depends(gateway_service.get_metrics_service),
    cache_service: CacheService = Depends(gateway_service.get_cache_service),
    version_service: VersionService = Depends(gateway_service.get_version_service)
):
    """
    Versioned proxy endpoint that handles all service requests
    """
    try:
        # Validate API version
        if not await version_service.is_version_supported(version):
            raise HTTPException(
                status_code=400,
                detail=f"API version {version} is not supported"
            )
        
        # Create request context with version information
        context = RequestContext(
            service=service,
            endpoint=endpoint,
            user=current_user,
            trace_id=str(uuid.uuid4()),
            api_version=version,
            is_version_explicit=True
        )

        # Check service configuration
        service_config = SERVICE_ROUTES.get(service)
        if not service_config:
            raise HTTPException(status_code=404, detail=f"Service {service} not found")

        endpoint_config = service_config["endpoints"].get(endpoint)
        if not endpoint_config:
            raise HTTPException(status_code=404, detail=f"Endpoint {endpoint} not found")
        
        # Check version compatibility for endpoint
        min_version = endpoint_config.get("min_api_version")
        max_version = endpoint_config.get("max_api_version")
        
        if min_version and version < min_version:
            raise HTTPException(
                status_code=400,
                detail=f"Endpoint requires API version {min_version} or higher"
            )
        
        if max_version and version > max_version:
            raise HTTPException(
                status_code=400,
                detail=f"Endpoint supports API version {max_version} or lower"
            )

        # Check authentication
        if endpoint_config.get("auth_required", True) and not current_user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )

        # Check permissions
        if current_user:
            # Check if user is allowed to use this API version
            if current_user.allowed_versions and version not in current_user.allowed_versions:
                raise HTTPException(
                    status_code=403,
                    detail=f"User is not authorized to use API version {version}"
                )
            
            # Check version-specific permissions if available
            version_permissions = current_user.version_specific_permissions.get(version, [])
            required_permissions = endpoint_config.get("permissions_required", [])
            
            # If we have version-specific permissions, use those instead of the global ones
            if version_permissions and required_permissions:
                if not any(perm in version_permissions for perm in required_permissions):
                    raise HTTPException(
                        status_code=403,
                        detail="Insufficient permissions for this API version"
                    )
            # Otherwise fall back to standard permission check
            elif not await auth_service.check_permissions(
                current_user,
                endpoint_config.get("roles_required", []),
                endpoint_config.get("permissions_required", [])
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions"
                )

        # Check rate limit
        rate_limit_key = f"{service}:{endpoint}:{version}:{current_user.user_id if current_user else 'anonymous'}"
        is_allowed, retry_after = await resilience_service.check_rate_limit(
            rate_limit_key,
            endpoint_config.get("rate_limit_type", "default")
        )
        
        if not is_allowed:
            await metrics_service.record_rate_limit(service, endpoint)
            return JSONResponse(
                status_code=429,
                content=ERROR_TEMPLATES["rate_limit_exceeded"],
                headers={"Retry-After": str(retry_after)}
            )

        # Check circuit breaker
        is_allowed, retry_after = await resilience_service.check_circuit_breaker(
            service,
            endpoint_config.get("circuit_breaker_type", "default")
        )
        
        if not is_allowed:
            await metrics_service.record_circuit_break(service)
            return JSONResponse(
                status_code=503,
                content=ERROR_TEMPLATES["circuit_open"],
                headers={"Retry-After": str(retry_after)}
            )

        # Check cache
        if endpoint_config.get("cache_enabled", False) and request.method == "GET":
            # Get cache configuration
            cache_config_type = endpoint_config.get("cache_config", "default")
            cache_config = CACHE_CONFIGS.get(cache_config_type, CACHE_CONFIGS["default"])
            
            # Determine if we should vary cache by user or role
            vary_by_user = endpoint_config.get("cache_vary_by_user", False)
            vary_by_role = endpoint_config.get("cache_vary_by_role", False)
            
            # Generate cache key with version information
            cache_key = f"v{version}:" + cache_service.generate_cache_key(
                service,
                endpoint,
                request.method,
                dict(request.query_params),
                current_user,
                vary_by_user,
                vary_by_role
            )
            
            # Try to get from cache
            cached_response = await cache_service.get_cached_response(cache_key, cache_config)
            if cached_response:
                # Apply cache headers
                response = JSONResponse(
                    content=cached_response.body,
                    status_code=cached_response.status_code,
                    headers=cached_response.headers
                )
                await cache_service.apply_cache_headers(response, cache_config, is_cached=True)
                
                # Add version headers
                await version_service.add_version_headers(response, version)
                
                # Record metrics
                await metrics_service.record_request_metrics(
                    context,
                    cached_response,
                    cache_hit=True
                )
                
                return response

        # Forward request
        body = await request.json() if request.method in ["POST", "PUT"] else None
        
        # Add version information to headers
        headers = dict(request.headers)
        headers["X-API-Version"] = version
        
        service_response = await routing_service.route_request(
            service,
            endpoint,
            request.method,
            headers,
            body
        )

        # Record metrics
        await metrics_service.record_request_metrics(
            context,
            service_response,
            cache_hit=False
        )

        # Cache successful GET responses if appropriate
        if endpoint_config.get("cache_enabled", False) and request.method == "GET":
            # Get cache configuration
            cache_config_type = endpoint_config.get("cache_config", "default")
            cache_config = CACHE_CONFIGS.get(cache_config_type, CACHE_CONFIGS["default"])
            
            # Check if response should be cached
            should_cache = await cache_service.should_cache_response(
                request, 
                service_response,
                cache_config
            )
            
            if should_cache and service_response.status_code < 400:
                # Cache the response
                await cache_service.cache_response(
                    cache_key,
                    service_response,
                    endpoint_config.get("cache_ttl"),
                    cache_config
                )
                
                # Apply cache headers to response
                response = JSONResponse(
                    content=service_response.body,
                    status_code=service_response.status_code,
                    headers=service_response.headers
                )
                await cache_service.apply_cache_headers(response, cache_config, is_cached=False)
                
                # Add version headers
                await version_service.add_version_headers(response, version)
                
                return response

        # Update circuit breaker
        if service_response.status_code >= 500:
            await resilience_service.record_failure(
                service,
                endpoint_config.get("circuit_breaker_type", "default")
            )
        else:
            await resilience_service.record_success(service)

        # Create response with version headers
        response = JSONResponse(
            content=service_response.body,
            status_code=service_response.status_code,
            headers=service_response.headers
        )
        await version_service.add_version_headers(response, version)
        
        return response

    except Exception as e:
        logger.error(
            "request_failed",
            service=service,
            endpoint=endpoint,
            version=version,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@app.api_route("/{service}/{endpoint:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_request(
    service: str,
    endpoint: str,
    request: Request,
    response: Response,
    current_user: Optional[UserInfo] = Depends(get_current_user),
    auth_service: AuthService = Depends(gateway_service.get_auth_service),
    resilience_service: ResilienceService = Depends(gateway_service.get_resilience_service),
    routing_service: RoutingService = Depends(gateway_service.get_routing_service),
    metrics_service: MetricsService = Depends(gateway_service.get_metrics_service)
):
    """
    Main proxy endpoint that handles all service requests
    """
    try:
        # Create request context
        context = RequestContext(
            service=service,
            endpoint=endpoint,
            user=current_user,
            trace_id=str(uuid.uuid4())
        )

        # Check service configuration
        service_config = SERVICE_ROUTES.get(service)
        if not service_config:
            raise HTTPException(status_code=404, detail=f"Service {service} not found")

        endpoint_config = service_config["endpoints"].get(endpoint)
        if not endpoint_config:
            raise HTTPException(status_code=404, detail=f"Endpoint {endpoint} not found")

        # Check authentication
        if endpoint_config.get("auth_required", True) and not current_user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )

        # Check permissions
        if current_user and not await auth_service.check_permissions(
            current_user,
            endpoint_config.get("roles_required", []),
            endpoint_config.get("permissions_required", [])
        ):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions"
            )

        # Check rate limit
        rate_limit_key = f"{service}:{endpoint}:{current_user.user_id if current_user else 'anonymous'}"
        is_allowed, retry_after = await resilience_service.check_rate_limit(
            rate_limit_key,
            endpoint_config.get("rate_limit_type", "default")
        )
        
        if not is_allowed:
            await metrics_service.record_rate_limit(service, endpoint)
            return JSONResponse(
                status_code=429,
                content=ERROR_TEMPLATES["rate_limit_exceeded"],
                headers={"Retry-After": str(retry_after)}
            )

        # Check circuit breaker
        is_allowed, retry_after = await resilience_service.check_circuit_breaker(
            service,
            endpoint_config.get("circuit_breaker_type", "default")
        )
        
        if not is_allowed:
            await metrics_service.record_circuit_break(service)
            return JSONResponse(
                status_code=503,
                content=ERROR_TEMPLATES["circuit_open"],
                headers={"Retry-After": str(retry_after)}
            )

        # Check cache
        if endpoint_config.get("cache_enabled", False) and request.method == "GET":
            # Get cache configuration
            cache_config_type = endpoint_config.get("cache_config", "default")
            cache_config = CACHE_CONFIGS.get(cache_config_type, CACHE_CONFIGS["default"])
            
            # Determine if we should vary cache by user or role
            vary_by_user = endpoint_config.get("cache_vary_by_user", False)
            vary_by_role = endpoint_config.get("cache_vary_by_role", False)
            
            # Generate cache key
            cache_key = cache_service.generate_cache_key(
                service,
                endpoint,
                request.method,
                dict(request.query_params),
                current_user,
                vary_by_user,
                vary_by_role
            )
            
            # Try to get from cache
            cached_response = await cache_service.get_cached_response(cache_key, cache_config)
            if cached_response:
                # Apply cache headers
                response = JSONResponse(
                    content=cached_response.body,
                    status_code=cached_response.status_code,
                    headers=cached_response.headers
                )
                await cache_service.apply_cache_headers(response, cache_config, is_cached=True)
                
                # Record metrics
                await metrics_service.record_request_metrics(
                    context,
                    cached_response,
                    cache_hit=True
                )
                
                return response

        # Forward request
        body = await request.json() if request.method in ["POST", "PUT"] else None
        service_response = await routing_service.route_request(
            service,
            endpoint,
            request.method,
            dict(request.headers),
            body
        )

        # Record metrics
        await metrics_service.record_request_metrics(
            context,
            service_response,
            cache_hit=False
        )

        # Cache successful GET responses if appropriate
        if endpoint_config.get("cache_enabled", False) and request.method == "GET":
            # Get cache configuration
            cache_config_type = endpoint_config.get("cache_config", "default")
            cache_config = CACHE_CONFIGS.get(cache_config_type, CACHE_CONFIGS["default"])
            
            # Check if response should be cached
            should_cache = await cache_service.should_cache_response(
                request, 
                service_response,
                cache_config
            )
            
            if should_cache and service_response.status_code < 400:
                # Cache the response
                await cache_service.cache_response(
                    cache_key,
                    service_response,
                    endpoint_config.get("cache_ttl"),
                    cache_config
                )
                
                # Apply cache headers to response
                response = JSONResponse(
                    content=service_response.body,
                    status_code=service_response.status_code,
                    headers=service_response.headers
                )
                await cache_service.apply_cache_headers(response, cache_config, is_cached=False)
                
                return response

        # Update circuit breaker
        if service_response.status_code >= 500:
            await resilience_service.record_failure(
                service,
                endpoint_config.get("circuit_breaker_type", "default")
            )
        else:
            await resilience_service.record_success(service)

        return service_response

    except Exception as e:
        logger.error(
            "request_failed",
            service=service,
            endpoint=endpoint,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
