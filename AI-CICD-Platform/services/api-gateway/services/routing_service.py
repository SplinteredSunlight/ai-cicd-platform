from typing import Dict, List, Optional, Tuple
import asyncio
import httpx
from datetime import datetime, timedelta
import json
from urllib.parse import urljoin

from ..config import get_settings, SERVICE_ROUTES
from ..models.gateway_models import (
    ServiceRegistration,
    ServiceEndpoint,
    ServiceStatus,
    RequestContext,
    ServiceResponse
)

class RoutingService:
    def __init__(self):
        self.settings = get_settings()
        
        # Service registry
        self._services: Dict[str, ServiceRegistration] = {}
        
        # HTTP client for forwarding requests
        self._client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True
        )
        
        # Start background tasks
        self._health_check_task = asyncio.create_task(self._health_check_loop())

    async def register_service(
        self,
        registration: ServiceRegistration
    ) -> bool:
        """
        Register a new service
        """
        try:
            # Validate service health before registering
            is_healthy = await self._check_service_health(
                registration.health_check_url
            )
            if not is_healthy:
                return False
            
            registration.last_health_check = datetime.utcnow()
            self._services[registration.service_id] = registration
            return True

        except Exception as e:
            print(f"Service registration failed: {str(e)}")
            return False

    async def deregister_service(self, service_id: str) -> bool:
        """
        Remove a service from registry
        """
        if service_id in self._services:
            del self._services[service_id]
            return True
        return False

    async def get_service(
        self,
        service_name: str
    ) -> Optional[ServiceRegistration]:
        """
        Get service by name
        """
        for service in self._services.values():
            if service.name == service_name:
                return service
        return None

    async def route_request(
        self,
        service: str,
        endpoint: str,
        method: str,
        headers: Dict[str, str],
        body: Optional[Dict] = None
    ) -> ServiceResponse:
        """
        Route request to appropriate service
        """
        try:
            # Get service configuration
            service_config = SERVICE_ROUTES.get(service)
            if not service_config:
                raise ValueError(f"Unknown service: {service}")
            
            # Get endpoint configuration
            endpoint_config = service_config["endpoints"].get(endpoint)
            if not endpoint_config:
                raise ValueError(f"Unknown endpoint: {endpoint}")
            
            # Get service registration
            service_reg = await self.get_service(service)
            if not service_reg:
                # Fall back to default URL from config
                service_url = self.settings.service_registry.get(service)
                if not service_url:
                    raise ValueError(f"Service {service} not available")
            else:
                service_url = service_reg.url
            
            # Build request URL
            url = urljoin(
                service_url,
                f"{service_config['prefix']}{endpoint_config['path']}"
            )
            
            # Forward request
            start_time = datetime.utcnow()
            async with self._client.stream(
                method=method,
                url=url,
                headers=headers,
                json=body
            ) as response:
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Stream response content
                content = await response.aread()
                try:
                    body = json.loads(content)
                except:
                    body = content.decode()
                
                return ServiceResponse(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    body=body,
                    duration_ms=duration
                )

        except Exception as e:
            raise Exception(f"Request routing failed: {str(e)}")

    async def get_service_status(
        self,
        service_id: str
    ) -> Tuple[ServiceStatus, Optional[str]]:
        """
        Get service status and any error message
        """
        service = self._services.get(service_id)
        if not service:
            return ServiceStatus.DOWN, "Service not registered"
        
        if (datetime.utcnow() - service.last_health_check) > timedelta(minutes=5):
            return ServiceStatus.DEGRADED, "Health check overdue"
        
        return service.status, None

    async def _health_check_loop(self):
        """
        Background task to perform health checks
        """
        while True:
            try:
                for service in list(self._services.values()):
                    try:
                        is_healthy = await self._check_service_health(
                            service.health_check_url
                        )
                        service.status = (
                            ServiceStatus.HEALTHY if is_healthy
                            else ServiceStatus.DOWN
                        )
                        service.last_health_check = datetime.utcnow()
                    except:
                        service.status = ServiceStatus.DOWN
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Health check loop error: {str(e)}")
                await asyncio.sleep(60)

    async def _check_service_health(self, health_check_url: str) -> bool:
        """
        Check if service is healthy
        """
        try:
            async with self._client.stream(
                "GET",
                health_check_url,
                timeout=5.0
            ) as response:
                return response.status_code == 200
        except:
            return False

    async def cleanup(self):
        """
        Cleanup resources
        """
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        if self._client:
            await self._client.aclose()
