import pytest
import sys
import os
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from httpx import Response, AsyncClient

# Add the parent directory to sys.path to allow imports from the main application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.routing_service import RoutingService
from models.gateway_models import (
    ServiceRegistration, 
    ServiceEndpoint, 
    ServiceStatus,
    ServiceResponse
)
from config import SERVICE_ROUTES

@pytest.fixture
def mock_httpx_client():
    """
    Create a mock for the httpx AsyncClient.
    """
    with patch('httpx.AsyncClient', autospec=True) as mock_client:
        # Create a mock instance
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        
        # Mock the stream method
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.aread.return_value = json.dumps({"message": "Success"}).encode()
        
        # Set up the context manager return value
        mock_instance.stream.return_value.__aenter__.return_value = mock_response
        
        yield mock_instance

@pytest.fixture
def routing_service(mock_httpx_client):
    """
    Create a RoutingService instance with a mocked HTTP client.
    """
    service = RoutingService()
    # Replace the real HTTP client with our mock
    service._client = mock_httpx_client
    return service

def test_routing_service_initialization():
    """
    Test that the RoutingService can be initialized correctly.
    """
    routing_service = RoutingService()
    assert routing_service is not None
    # Cleanup to prevent background tasks from running
    asyncio.run(routing_service.cleanup())

@pytest.mark.asyncio
async def test_register_service(routing_service, mock_httpx_client):
    """
    Test registering a service with the routing service.
    """
    # Mock the health check response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_httpx_client.stream.return_value.__aenter__.return_value = mock_response
    
    # Create a service registration
    service_reg = ServiceRegistration(
        name="test-service",
        version="1.0.0",
        url="http://test-service:8080",
        health_check_url="http://test-service:8080/health",
        endpoints={
            "test": ServiceEndpoint(
                method="GET",
                path="/test",
                rate_limit=100,
                cache_enabled=False,
                timeout=30
            )
        }
    )
    
    # Register the service
    result = await routing_service.register_service(service_reg)
    
    # Verify the service was registered
    assert result is True
    assert await routing_service.get_service("test-service") is not None

@pytest.mark.asyncio
async def test_deregister_service(routing_service):
    """
    Test deregistering a service from the routing service.
    """
    # Add a service to the registry
    service_reg = ServiceRegistration(
        service_id="test-id",
        name="test-service",
        version="1.0.0",
        url="http://test-service:8080",
        health_check_url="http://test-service:8080/health",
        endpoints={},
        last_health_check=datetime.utcnow()
    )
    routing_service._services["test-id"] = service_reg
    
    # Deregister the service
    result = await routing_service.deregister_service("test-id")
    
    # Verify the service was deregistered
    assert result is True
    assert "test-id" not in routing_service._services

@pytest.mark.asyncio
async def test_get_service(routing_service):
    """
    Test retrieving a service by name.
    """
    # Add a service to the registry
    service_reg = ServiceRegistration(
        service_id="test-id",
        name="test-service",
        version="1.0.0",
        url="http://test-service:8080",
        health_check_url="http://test-service:8080/health",
        endpoints={},
        last_health_check=datetime.utcnow()
    )
    routing_service._services["test-id"] = service_reg
    
    # Get the service
    result = await routing_service.get_service("test-service")
    
    # Verify the correct service was returned
    assert result is not None
    assert result.service_id == "test-id"
    assert result.name == "test-service"

@pytest.mark.asyncio
async def test_route_request_success(routing_service, mock_httpx_client):
    """
    Test routing a request to a service successfully.
    """
    # Mock the response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.aread.return_value = json.dumps({"result": "success"}).encode()
    mock_httpx_client.stream.return_value.__aenter__.return_value = mock_response
    
    # Route a request
    response = await routing_service.route_request(
        service="pipeline-generator",
        endpoint="generate",
        method="POST",
        headers={"Content-Type": "application/json"},
        body={"description": "Test pipeline"}
    )
    
    # Verify the response
    assert response.status_code == 200
    assert response.body == {"result": "success"}
    assert isinstance(response.duration_ms, float)
    
    # Verify the request was made correctly
    mock_httpx_client.stream.assert_called_once()
    call_args = mock_httpx_client.stream.call_args[1]
    assert call_args["method"] == "POST"
    assert "pipeline-generator" in call_args["url"]
    assert "/generate" in call_args["url"]
    assert call_args["headers"] == {"Content-Type": "application/json"}
    assert call_args["json"] == {"description": "Test pipeline"}

@pytest.mark.asyncio
async def test_route_request_unknown_service(routing_service):
    """
    Test routing a request to an unknown service.
    """
    with pytest.raises(Exception) as excinfo:
        await routing_service.route_request(
            service="unknown-service",
            endpoint="test",
            method="GET",
            headers={}
        )
    
    assert "Unknown service" in str(excinfo.value)

@pytest.mark.asyncio
async def test_route_request_unknown_endpoint(routing_service):
    """
    Test routing a request to an unknown endpoint.
    """
    with pytest.raises(Exception) as excinfo:
        await routing_service.route_request(
            service="pipeline-generator",
            endpoint="unknown-endpoint",
            method="GET",
            headers={}
        )
    
    assert "Unknown endpoint" in str(excinfo.value)

@pytest.mark.asyncio
async def test_service_status(routing_service):
    """
    Test getting the status of a service.
    """
    # Add a service to the registry
    service_reg = ServiceRegistration(
        service_id="test-id",
        name="test-service",
        version="1.0.0",
        url="http://test-service:8080",
        health_check_url="http://test-service:8080/health",
        endpoints={},
        status=ServiceStatus.HEALTHY,
        last_health_check=datetime.utcnow()
    )
    routing_service._services["test-id"] = service_reg
    
    # Get the service status
    status, error = await routing_service.get_service_status("test-id")
    
    # Verify the status
    assert status == ServiceStatus.HEALTHY
    assert error is None
    
    # Test with an overdue health check
    service_reg.last_health_check = datetime.utcnow() - timedelta(minutes=10)
    status, error = await routing_service.get_service_status("test-id")
    
    # Verify the status is degraded
    assert status == ServiceStatus.DEGRADED
    assert "Health check overdue" in error
    
    # Test with a non-existent service
    status, error = await routing_service.get_service_status("non-existent")
    
    # Verify the status is down
    assert status == ServiceStatus.DOWN
    assert "Service not registered" in error

@pytest.mark.asyncio
async def test_health_check(routing_service, mock_httpx_client):
    """
    Test the health check functionality.
    """
    # Mock a healthy response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_httpx_client.stream.return_value.__aenter__.return_value = mock_response
    
    # Check health
    result = await routing_service._check_service_health("http://test-service:8080/health")
    
    # Verify the result
    assert result is True
    
    # Mock an unhealthy response
    mock_response.status_code = 500
    result = await routing_service._check_service_health("http://test-service:8080/health")
    
    # Verify the result
    assert result is False
    
    # Mock an exception
    mock_httpx_client.stream.side_effect = Exception("Connection error")
    result = await routing_service._check_service_health("http://test-service:8080/health")
    
    # Verify the result
    assert result is False
    
    # Reset the mock
    mock_httpx_client.stream.side_effect = None
