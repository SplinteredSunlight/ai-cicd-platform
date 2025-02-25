from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn
from typing import Optional, Dict, Any
import uuid
from datetime import datetime

from .config import get_settings, SERVICE_ROUTES, ERROR_TEMPLATES
from .models.gateway_models import (
    RequestContext,
    ServiceResponse,
    ErrorResponse,
    UserInfo
)
from .services.auth_service import AuthService
from .services.resilience_service import ResilienceService
from .services.routing_service import RoutingService
from .services.metrics_service import MetricsService

# Configure structured logging
logger = structlog.get_logger()

app = FastAPI(
    title="AI CI/CD Platform API Gateway",
    description="API Gateway for AI-powered CI/CD Automation & Security Platform",
    version="0.1.0"
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

    def get_auth_service(self) -> AuthService:
        return self.auth_service

    def get_resilience_service(self) -> ResilienceService:
        return self.resilience_service

    def get_routing_service(self) -> RoutingService:
        return self.routing_service

    def get_metrics_service(self) -> MetricsService:
        return self.metrics_service

gateway_service = GatewayService()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    await gateway_service.auth_service.cleanup()
    await gateway_service.resilience_service.cleanup()
    await gateway_service.routing_service.cleanup()
    await gateway_service.metrics_service.cleanup()

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": "0.1.0"
    }

@app.post("/api/v1/auth/token")
async def login(
    username: str,
    password: str,
    auth_service: AuthService = Depends(gateway_service.get_auth_service)
):
    """Get authentication token"""
    user = await auth_service.authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    
    return await auth_service.create_access_token(user)

async def get_current_user(
    request: Request,
    auth_service: AuthService = Depends(gateway_service.get_auth_service)
) -> Optional[UserInfo]:
    """Get current user from token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            return None
        
        return await auth_service.verify_token(token)
    except:
        return None

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
            cache_key = metrics_service.generate_cache_key(
                service,
                endpoint,
                request.method,
                dict(request.query_params)
            )
            
            cached_response = await metrics_service.get_cached_response(cache_key)
            if cached_response:
                await metrics_service.record_request_metrics(
                    context,
                    cached_response,
                    cache_hit=True
                )
                return cached_response

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

        # Cache successful GET responses
        if (
            endpoint_config.get("cache_enabled", False) and
            request.method == "GET" and
            service_response.status_code < 400
        ):
            await metrics_service.cache_response(
                cache_key,
                service_response,
                endpoint_config.get("cache_ttl")
            )

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
