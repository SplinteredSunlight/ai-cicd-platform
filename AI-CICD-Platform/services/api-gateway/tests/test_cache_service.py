import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
import json

from ..services.cache_service import CacheService
from ..models.gateway_models import (
    ServiceResponse,
    UserInfo,
    UserRole,
    CacheEntry
)

# Test fixtures
@pytest.fixture
def cache_service():
    """Create an instance of CacheService for testing"""
    service = CacheService()
    # Mock the Redis connection
    service._redis = AsyncMock()
    service._cache = AsyncMock()
    return service

@pytest.fixture
def mock_user():
    """Create a mock user for testing"""
    return UserInfo(
        user_id="test_user_id",
        username="testuser",
        email="test@example.com",
        roles=[UserRole.DEVELOPER],
        permissions=["read:all", "write:own"],
        metadata={}
    )

@pytest.fixture
def mock_admin_user():
    """Create a mock admin user for testing"""
    return UserInfo(
        user_id="admin_id",
        username="admin",
        email="admin@example.com",
        roles=[UserRole.ADMIN],
        permissions=["*"],
        metadata={}
    )

@pytest.fixture
def mock_service_response():
    """Create a mock service response for testing"""
    return ServiceResponse(
        status_code=200,
        headers={"Content-Type": "application/json"},
        body={"data": "test data"},
        duration_ms=10.5
    )

@pytest.fixture
def mock_request():
    """Create a mock request for testing"""
    mock_req = MagicMock()
    mock_req.method = "GET"
    mock_req.headers = {}
    mock_req.query_params = {}
    return mock_req

# Test cache key generation
@pytest.mark.asyncio
async def test_generate_cache_key_basic(cache_service):
    """Test basic cache key generation"""
    key = cache_service.generate_cache_key(
        service="test-service",
        endpoint="test-endpoint",
        method="GET",
        params={}
    )
    
    assert "test-service" in key
    assert "test-endpoint" in key
    assert "GET" in key

@pytest.mark.asyncio
async def test_generate_cache_key_with_params(cache_service):
    """Test cache key generation with parameters"""
    key = cache_service.generate_cache_key(
        service="test-service",
        endpoint="test-endpoint",
        method="GET",
        params={"param1": "value1", "param2": "value2"}
    )
    
    assert "test-service" in key
    assert "test-endpoint" in key
    assert "GET" in key
    assert "params:" in key  # Hash of parameters

@pytest.mark.asyncio
async def test_generate_cache_key_with_user(cache_service, mock_user):
    """Test cache key generation with user variation"""
    key = cache_service.generate_cache_key(
        service="test-service",
        endpoint="test-endpoint",
        method="GET",
        params={},
        user=mock_user,
        vary_by_user=True
    )
    
    assert "test-service" in key
    assert "test-endpoint" in key
    assert "GET" in key
    assert f"user:{mock_user.user_id}" in key

@pytest.mark.asyncio
async def test_generate_cache_key_with_role(cache_service, mock_user):
    """Test cache key generation with role variation"""
    key = cache_service.generate_cache_key(
        service="test-service",
        endpoint="test-endpoint",
        method="GET",
        params={},
        user=mock_user,
        vary_by_role=True
    )
    
    assert "test-service" in key
    assert "test-endpoint" in key
    assert "GET" in key
    assert f"role:{mock_user.roles[0].value}" in key

# Test cache operations
@pytest.mark.asyncio
async def test_get_cached_response_hit(cache_service, mock_service_response):
    """Test getting a cached response (cache hit)"""
    # Setup mock
    cache_service._cache.get.return_value = mock_service_response
    
    # Test
    result = await cache_service.get_cached_response("test-key")
    
    # Verify
    assert result == mock_service_response
    assert cache_service._stats["hits"] == 1
    cache_service._cache.get.assert_called_once_with("test-key")

@pytest.mark.asyncio
async def test_get_cached_response_miss(cache_service):
    """Test getting a cached response (cache miss)"""
    # Setup mock
    cache_service._cache.get.return_value = None
    
    # Test
    result = await cache_service.get_cached_response("test-key")
    
    # Verify
    assert result is None
    assert cache_service._stats["misses"] == 1
    cache_service._cache.get.assert_called_once_with("test-key")

@pytest.mark.asyncio
async def test_cache_response(cache_service, mock_service_response):
    """Test caching a response"""
    # Setup
    cache_service.settings.cache_enabled = True
    
    # Test
    await cache_service.cache_response("test-key", mock_service_response, ttl=60)
    
    # Verify
    assert cache_service._stats["stored"] == 1
    cache_service._cache.set.assert_called_once()
    # Check that the first argument to set() is the key
    assert cache_service._cache.set.call_args[0][0] == "test-key"
    # Check that the second argument to set() is the response
    assert cache_service._cache.set.call_args[0][1] == mock_service_response
    # Check that ttl was passed as a keyword argument
    assert cache_service._cache.set.call_args[1]["ttl"] == 60

@pytest.mark.asyncio
async def test_cache_disabled(cache_service, mock_service_response):
    """Test caching when cache is disabled"""
    # Setup
    cache_service.settings.cache_enabled = False
    
    # Test
    await cache_service.cache_response("test-key", mock_service_response)
    
    # Verify
    assert cache_service._stats["stored"] == 0
    cache_service._cache.set.assert_not_called()

@pytest.mark.asyncio
async def test_invalidate_cache(cache_service):
    """Test invalidating cache entries"""
    # Setup mocks
    cache_service._redis.keys.return_value = ["key1", "key2", "key3"]
    cache_service._redis.delete.return_value = 3
    
    # Test
    count = await cache_service.invalidate_cache(pattern="test*")
    
    # Verify
    assert count == 3
    assert cache_service._stats["invalidations"] == 3
    cache_service._redis.keys.assert_called_once()
    cache_service._redis.delete.assert_called_once_with("key1", "key2", "key3")

@pytest.mark.asyncio
async def test_invalidate_cache_by_service(cache_service):
    """Test invalidating cache entries by service"""
    # Setup mocks
    cache_service._redis.keys.return_value = ["key1", "key2"]
    cache_service._redis.delete.return_value = 2
    
    # Test
    count = await cache_service.invalidate_cache(service="test-service")
    
    # Verify
    assert count == 2
    assert cache_service._stats["invalidations"] == 2
    cache_service._redis.keys.assert_called_once()
    cache_service._redis.delete.assert_called_once_with("key1", "key2")

@pytest.mark.asyncio
async def test_invalidate_cache_by_service_and_endpoint(cache_service):
    """Test invalidating cache entries by service and endpoint"""
    # Setup mocks
    cache_service._redis.keys.return_value = ["key1"]
    cache_service._redis.delete.return_value = 1
    
    # Test
    count = await cache_service.invalidate_cache(
        service="test-service",
        endpoint="test-endpoint"
    )
    
    # Verify
    assert count == 1
    assert cache_service._stats["invalidations"] == 1
    cache_service._redis.keys.assert_called_once()
    cache_service._redis.delete.assert_called_once_with("key1")

@pytest.mark.asyncio
async def test_invalidate_cache_no_keys(cache_service):
    """Test invalidating cache when no keys match"""
    # Setup mocks
    cache_service._redis.keys.return_value = []
    
    # Test
    count = await cache_service.invalidate_cache(pattern="test*")
    
    # Verify
    assert count == 0
    assert cache_service._stats["invalidations"] == 0
    cache_service._redis.keys.assert_called_once()
    cache_service._redis.delete.assert_not_called()

# Test cache decision logic
@pytest.mark.asyncio
async def test_should_cache_response_true(cache_service, mock_request, mock_service_response):
    """Test should_cache_response returns True for cacheable responses"""
    # Setup
    cache_service.settings.cache_enabled = True
    mock_request.method = "GET"
    mock_service_response.status_code = 200
    
    # Test
    result = await cache_service.should_cache_response(
        mock_request,
        mock_service_response
    )
    
    # Verify
    assert result is True

@pytest.mark.asyncio
async def test_should_cache_response_false_disabled(cache_service, mock_request, mock_service_response):
    """Test should_cache_response returns False when cache is disabled"""
    # Setup
    cache_service.settings.cache_enabled = False
    
    # Test
    result = await cache_service.should_cache_response(
        mock_request,
        mock_service_response
    )
    
    # Verify
    assert result is False

@pytest.mark.asyncio
async def test_should_cache_response_false_non_get(cache_service, mock_request, mock_service_response):
    """Test should_cache_response returns False for non-GET requests"""
    # Setup
    cache_service.settings.cache_enabled = True
    mock_request.method = "POST"
    
    # Test
    result = await cache_service.should_cache_response(
        mock_request,
        mock_service_response
    )
    
    # Verify
    assert result is False

@pytest.mark.asyncio
async def test_should_cache_response_false_error(cache_service, mock_request, mock_service_response):
    """Test should_cache_response returns False for error responses"""
    # Setup
    cache_service.settings.cache_enabled = True
    mock_request.method = "GET"
    mock_service_response.status_code = 500
    
    # Test
    result = await cache_service.should_cache_response(
        mock_request,
        mock_service_response
    )
    
    # Verify
    assert result is False

@pytest.mark.asyncio
async def test_should_cache_response_false_no_cache_header(cache_service, mock_request, mock_service_response):
    """Test should_cache_response returns False when Cache-Control: no-cache is set"""
    # Setup
    cache_service.settings.cache_enabled = True
    mock_request.method = "GET"
    mock_service_response.status_code = 200
    mock_service_response.headers = {"Cache-Control": "no-cache"}
    
    # Test
    result = await cache_service.should_cache_response(
        mock_request,
        mock_service_response
    )
    
    # Verify
    assert result is False

@pytest.mark.asyncio
async def test_should_cache_response_false_too_large(cache_service, mock_request, mock_service_response):
    """Test should_cache_response returns False for large responses"""
    # Setup
    cache_service.settings.cache_enabled = True
    mock_request.method = "GET"
    mock_service_response.status_code = 200
    
    # Create a large response body
    mock_service_response.body = {"data": "x" * (1000 * 1024 + 1)}  # Just over 1000 KB
    
    # Test
    result = await cache_service.should_cache_response(
        mock_request,
        mock_service_response
    )
    
    # Verify
    assert result is False

# Test cache headers
@pytest.mark.asyncio
async def test_apply_cache_headers_hit(cache_service):
    """Test applying cache headers for a cache hit"""
    # Setup
    response = MagicMock()
    response.headers = {}
    
    # Test
    await cache_service.apply_cache_headers(
        response,
        {"ttl": 300},
        is_cached=True
    )
    
    # Verify
    assert response.headers["X-Cache"] == "HIT"
    assert "Cache-Control" in response.headers
    assert "max-age=300" in response.headers["Cache-Control"]
    assert "Expires" in response.headers
    assert "Vary" in response.headers

@pytest.mark.asyncio
async def test_apply_cache_headers_miss(cache_service):
    """Test applying cache headers for a cache miss"""
    # Setup
    response = MagicMock()
    response.headers = {}
    
    # Test
    await cache_service.apply_cache_headers(
        response,
        {"ttl": 300},
        is_cached=False
    )
    
    # Verify
    assert response.headers["X-Cache"] == "MISS"
    assert "Cache-Control" in response.headers
    assert "max-age=300" in response.headers["Cache-Control"]
    assert "Expires" in response.headers
    assert "Vary" in response.headers

@pytest.mark.asyncio
async def test_apply_cache_headers_no_cache(cache_service):
    """Test applying cache headers with no caching"""
    # Setup
    response = MagicMock()
    response.headers = {}
    
    # Test
    await cache_service.apply_cache_headers(
        response,
        {"ttl": 0},
        is_cached=False
    )
    
    # Verify
    assert response.headers["X-Cache"] == "MISS"
    assert "Cache-Control" in response.headers
    assert "no-store" in response.headers["Cache-Control"]
    assert "Expires" in response.headers
    assert response.headers["Expires"] == "0"
    assert "Vary" in response.headers

# Test cache statistics
@pytest.mark.asyncio
async def test_get_cache_stats(cache_service):
    """Test getting cache statistics"""
    # Setup
    cache_service._stats = {
        "hits": 10,
        "misses": 5,
        "invalidations": 2,
        "stored": 15
    }
    
    # Mock Redis info
    cache_service._redis.info.return_value = {
        "used_memory_human": "1.5M",
        "used_memory_peak_human": "2M"
    }
    
    # Test
    stats = await cache_service.get_cache_stats()
    
    # Verify
    assert stats["hits"] == 10
    assert stats["misses"] == 5
    assert stats["invalidations"] == 2
    assert stats["stored"] == 15
    assert stats["hit_ratio"] == 10 / 15  # 0.6667
    assert stats["memory_used"] == "1.5M"
    assert stats["memory_peak"] == "2M"

@pytest.mark.asyncio
async def test_cleanup(cache_service):
    """Test cleanup method"""
    # Setup
    cache_service._cleanup_task = MagicMock()
    cache_service._cleanup_task.cancel = MagicMock()
    cache_service._init_task = MagicMock()
    cache_service._init_task.cancel = MagicMock()
    
    # Test
    await cache_service.cleanup()
    
    # Verify
    cache_service._cleanup_task.cancel.assert_called_once()
    cache_service._init_task.cancel.assert_called_once()
    cache_service._redis.close.assert_called_once()
