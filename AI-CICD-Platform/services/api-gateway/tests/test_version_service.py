import pytest
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from fastapi import Request, Header

# Add the parent directory to sys.path to allow imports from the main application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.version_service import VersionService
from models.gateway_models import ApiVersion, VersionNegotiationStrategy

@pytest.fixture
def version_service():
    """Create a VersionService instance for testing"""
    return VersionService()

@pytest.mark.asyncio
async def test_get_version(version_service):
    """Test getting a specific API version"""
    # Test getting an existing version
    version = await version_service.get_version("1")
    assert version is not None
    assert version.version == "1"
    
    # Test getting a non-existent version
    version = await version_service.get_version("999")
    assert version is None

@pytest.mark.asyncio
async def test_get_latest_version(version_service):
    """Test getting the latest API version"""
    latest = await version_service.get_latest_version()
    assert latest is not None
    assert latest.version == "2"  # Assuming v2 is the latest in our test setup

@pytest.mark.asyncio
async def test_is_version_supported(version_service):
    """Test checking if a version is supported"""
    # Test supported version
    is_supported = await version_service.is_version_supported("1")
    assert is_supported is True
    
    # Test non-existent version
    is_supported = await version_service.is_version_supported("999")
    assert is_supported is False
    
    # Test deprecated version
    # First, mark a version as deprecated
    version_service._versions["1"].deprecated = True
    is_supported = await version_service.is_version_supported("1")
    assert is_supported is False
    
    # Reset for other tests
    version_service._versions["1"].deprecated = False
    
    # Test sunset version
    # First, set a sunset date in the past
    version_service._versions["1"].sunset_date = datetime.utcnow() - timedelta(days=1)
    is_supported = await version_service.is_version_supported("1")
    assert is_supported is False
    
    # Reset for other tests
    version_service._versions["1"].sunset_date = None

@pytest.mark.asyncio
async def test_negotiate_version_header_first():
    """Test version negotiation with header-first strategy"""
    version_service = VersionService()
    
    # Mock request with no version information
    mock_request = MagicMock()
    mock_request.url.path = "/api/service/endpoint"
    mock_request.query_params = {}
    
    # Test with no version specified (should return latest)
    version, is_explicit = await version_service.negotiate_version(
        mock_request,
        accept_version=None,
        strategy=VersionNegotiationStrategy.HEADER_FIRST
    )
    assert version == "2"  # Latest version
    assert is_explicit is False
    
    # Test with header version
    version, is_explicit = await version_service.negotiate_version(
        mock_request,
        accept_version="1",
        strategy=VersionNegotiationStrategy.HEADER_FIRST
    )
    assert version == "1"
    assert is_explicit is True
    
    # Test with path version
    mock_request.url.path = "/api/v1/service/endpoint"
    version, is_explicit = await version_service.negotiate_version(
        mock_request,
        accept_version=None,
        strategy=VersionNegotiationStrategy.HEADER_FIRST
    )
    assert version == "1"
    assert is_explicit is True
    
    # Test with query version
    mock_request.url.path = "/api/service/endpoint"
    mock_request.query_params = {"version": "1"}
    version, is_explicit = await version_service.negotiate_version(
        mock_request,
        accept_version=None,
        strategy=VersionNegotiationStrategy.HEADER_FIRST
    )
    assert version == "1"
    assert is_explicit is True
    
    # Test precedence: header > path > query
    mock_request.url.path = "/api/v1/service/endpoint"
    mock_request.query_params = {"version": "1"}
    version, is_explicit = await version_service.negotiate_version(
        mock_request,
        accept_version="2",
        strategy=VersionNegotiationStrategy.HEADER_FIRST
    )
    assert version == "2"  # Header takes precedence
    assert is_explicit is True

@pytest.mark.asyncio
async def test_negotiate_version_path_first():
    """Test version negotiation with path-first strategy"""
    version_service = VersionService()
    
    # Mock request with multiple version information
    mock_request = MagicMock()
    mock_request.url.path = "/api/v1/service/endpoint"
    mock_request.query_params = {"version": "2"}
    
    # Test precedence: path > header > query
    version, is_explicit = await version_service.negotiate_version(
        mock_request,
        accept_version="2",
        strategy=VersionNegotiationStrategy.PATH_FIRST
    )
    assert version == "1"  # Path takes precedence
    assert is_explicit is True

@pytest.mark.asyncio
async def test_negotiate_version_query_first():
    """Test version negotiation with query-first strategy"""
    version_service = VersionService()
    
    # Mock request with multiple version information
    mock_request = MagicMock()
    mock_request.url.path = "/api/v1/service/endpoint"
    mock_request.query_params = {"version": "2"}
    
    # Test precedence: query > header > path
    version, is_explicit = await version_service.negotiate_version(
        mock_request,
        accept_version="1",
        strategy=VersionNegotiationStrategy.QUERY_FIRST
    )
    assert version == "2"  # Query takes precedence
    assert is_explicit is True

@pytest.mark.asyncio
async def test_extract_version_from_header():
    """Test extracting version from header"""
    version_service = VersionService()
    
    # Test simple version number
    version = version_service._extract_version_from_header("1")
    assert version == "1"
    
    # Test v-prefixed version
    version = version_service._extract_version_from_header("v1")
    assert version == "1"
    
    # Test semver format
    version = version_service._extract_version_from_header("1.2.3")
    assert version == "1"
    
    # Test invalid format
    version = version_service._extract_version_from_header("invalid")
    assert version is None

@pytest.mark.asyncio
async def test_extract_version_from_path():
    """Test extracting version from path"""
    version_service = VersionService()
    
    # Test /api/v1/... format
    version = version_service._extract_version_from_path("/api/v1/service/endpoint")
    assert version == "1"
    
    # Test /v1/... format
    version = version_service._extract_version_from_path("/v1/service/endpoint")
    assert version == "1"
    
    # Test invalid format
    version = version_service._extract_version_from_path("/api/service/endpoint")
    assert version is None

@pytest.mark.asyncio
async def test_extract_version_from_query():
    """Test extracting version from query parameters"""
    version_service = VersionService()
    
    # Test version parameter
    version = version_service._extract_version_from_query({"version": "1"})
    assert version == "1"
    
    # Test v parameter
    version = version_service._extract_version_from_query({"v": "1"})
    assert version == "1"
    
    # Test v-prefixed version
    version = version_service._extract_version_from_query({"version": "v1"})
    assert version == "1"
    
    # Test invalid format
    version = version_service._extract_version_from_query({"version": "invalid"})
    assert version is None
    
    # Test empty query
    version = version_service._extract_version_from_query({})
    assert version is None

@pytest.mark.asyncio
async def test_add_version_headers():
    """Test adding version headers to response"""
    version_service = VersionService()
    
    # Mock response
    mock_response = MagicMock()
    mock_response.headers = {}
    
    # Test adding headers for current version
    await version_service.add_version_headers(mock_response, "1")
    assert mock_response.headers["X-API-Version"] == "1"
    
    # Test adding headers for deprecated version
    version_service._versions["1"].deprecated = True
    await version_service.add_version_headers(mock_response, "1")
    assert "Warning" in mock_response.headers
    assert "Deprecated API Version" in mock_response.headers["Warning"]
    
    # Test adding sunset date
    version_service._versions["1"].sunset_date = datetime.utcnow() + timedelta(days=30)
    await version_service.add_version_headers(mock_response, "1")
    assert "Sunset" in mock_response.headers
    
    # Test adding documentation link
    version_service._versions["1"].documentation_url = "/docs/v1"
    await version_service.add_version_headers(mock_response, "1")
    assert "Link" in mock_response.headers
    assert "/docs/v1" in mock_response.headers["Link"]
    
    # Test adding latest version info
    await version_service.add_version_headers(mock_response, "1")
    assert "X-API-Latest-Version" in mock_response.headers
    assert mock_response.headers["X-API-Latest-Version"] == "2"
    
    # Reset for other tests
    version_service._versions["1"].deprecated = False
    version_service._versions["1"].sunset_date = None

@pytest.mark.asyncio
async def test_transform_request_for_version():
    """Test transforming request data between versions"""
    version_service = VersionService()
    
    # Test simple pass-through
    request_data = {"key": "value"}
    transformed = await version_service.transform_request_for_version(
        request_data, "1", "2"
    )
    assert transformed == request_data

@pytest.mark.asyncio
async def test_transform_response_for_version():
    """Test transforming response data between versions"""
    version_service = VersionService()
    
    # Test simple pass-through
    response_data = {"key": "value"}
    transformed = await version_service.transform_response_for_version(
        response_data, "1", "2"
    )
    assert transformed == response_data
