from typing import Dict, List, Optional, Tuple, Any
import re
import semver
from enum import Enum
from datetime import datetime
from fastapi import Request, Response, Header
import structlog

from ..config import get_settings
from ..models.gateway_models import ApiVersion, VersionNegotiationStrategy

# Configure structured logging
logger = structlog.get_logger()

class VersionService:
    def __init__(self):
        self.settings = get_settings()
        
        # Available API versions
        self._versions: Dict[str, ApiVersion] = {}
        
        # Initialize with default versions
        self._initialize_versions()
    
    def _initialize_versions(self):
        """Initialize available API versions"""
        # Add v1 (current version)
        self._versions["1"] = ApiVersion(
            version="1",
            release_date=datetime(2024, 1, 1),
            sunset_date=None,
            deprecated=False,
            supported_features=["basic_auth", "mfa", "token_refresh"],
            changes_from_previous=None,
            documentation_url="/docs/v1"
        )
        
        # Add v2 (new version with enhanced features)
        self._versions["2"] = ApiVersion(
            version="2",
            release_date=datetime(2025, 2, 1),
            sunset_date=None,
            deprecated=False,
            supported_features=[
                "basic_auth", "mfa", "token_refresh", 
                "enhanced_auth", "api_keys", "version_negotiation"
            ],
            changes_from_previous=[
                "Added version negotiation through headers",
                "Enhanced authentication with API keys",
                "Improved token security with version-specific scopes"
            ],
            documentation_url="/docs/v2"
        )
    
    async def get_version(self, version_str: str) -> Optional[ApiVersion]:
        """Get API version details"""
        return self._versions.get(version_str)
    
    async def get_latest_version(self) -> ApiVersion:
        """Get the latest API version"""
        # Sort versions using semver and return the latest
        versions = sorted(self._versions.keys(), key=lambda v: semver.VersionInfo.parse(f"{v}.0.0"))
        return self._versions[versions[-1]]
    
    async def is_version_supported(self, version_str: str) -> bool:
        """Check if a version is supported"""
        version = self._versions.get(version_str)
        if not version:
            return False
        
        # Check if version is deprecated or sunset
        if version.deprecated:
            return False
        
        if version.sunset_date and datetime.utcnow() > version.sunset_date:
            return False
        
        return True
    
    async def negotiate_version(
        self, 
        request: Request,
        accept_version: Optional[str] = Header(None),
        strategy: VersionNegotiationStrategy = VersionNegotiationStrategy.HEADER_FIRST
    ) -> Tuple[str, bool]:
        """
        Negotiate API version based on request
        Returns (version, is_explicit)
        - version: The negotiated version string
        - is_explicit: Whether the version was explicitly specified
        """
        version = None
        is_explicit = True
        
        # Extract version from different sources based on strategy
        if strategy == VersionNegotiationStrategy.HEADER_FIRST:
            # Try header first
            if accept_version:
                version = self._extract_version_from_header(accept_version)
            
            # Then try URL path
            if not version:
                version = self._extract_version_from_path(request.url.path)
            
            # Then try query parameter
            if not version:
                version = self._extract_version_from_query(request.query_params)
        
        elif strategy == VersionNegotiationStrategy.PATH_FIRST:
            # Try URL path first
            version = self._extract_version_from_path(request.url.path)
            
            # Then try header
            if not version and accept_version:
                version = self._extract_version_from_header(accept_version)
            
            # Then try query parameter
            if not version:
                version = self._extract_version_from_query(request.query_params)
        
        elif strategy == VersionNegotiationStrategy.QUERY_FIRST:
            # Try query parameter first
            version = self._extract_version_from_query(request.query_params)
            
            # Then try header
            if not version and accept_version:
                version = self._extract_version_from_header(accept_version)
            
            # Then try URL path
            if not version:
                version = self._extract_version_from_path(request.url.path)
        
        # If no version specified, use default
        if not version:
            latest = await self.get_latest_version()
            version = latest.version
            is_explicit = False
        
        # Validate version is supported
        if not await self.is_version_supported(version):
            # Fall back to latest supported version
            latest = await self.get_latest_version()
            version = latest.version
            is_explicit = False
        
        return version, is_explicit
    
    def _extract_version_from_header(self, header_value: str) -> Optional[str]:
        """Extract version from Accept-Version header"""
        # Handle simple version number
        if re.match(r'^\d+$', header_value):
            return header_value
        
        # Handle semver format
        match = re.match(r'^v?(\d+)(\.\d+)?(\.\d+)?', header_value)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_version_from_path(self, path: str) -> Optional[str]:
        """Extract version from URL path"""
        # Match /api/v1/... or /v1/... patterns
        match = re.search(r'/api/v(\d+)/', path) or re.search(r'/v(\d+)/', path)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_version_from_query(self, query_params: Dict[str, str]) -> Optional[str]:
        """Extract version from query parameters"""
        version = query_params.get('version') or query_params.get('v')
        if version:
            # Handle 'v1' format
            match = re.match(r'^v?(\d+)$', version)
            if match:
                return match.group(1)
        
        return None
    
    async def add_version_headers(self, response: Response, version: str):
        """Add version headers to response"""
        response.headers["X-API-Version"] = version
        
        # Add deprecation warning if applicable
        api_version = self._versions.get(version)
        if api_version and api_version.deprecated:
            response.headers["Warning"] = f'299 - "Deprecated API Version {version}"'
            
            # Add sunset date if available
            if api_version.sunset_date:
                sunset_date = api_version.sunset_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
                response.headers["Sunset"] = sunset_date
        
        # Add link to documentation
        if api_version and api_version.documentation_url:
            response.headers["Link"] = f'<{api_version.documentation_url}>; rel="documentation"'
        
        # Add latest version info
        latest = await self.get_latest_version()
        if latest.version != version:
            response.headers["X-API-Latest-Version"] = latest.version
    
    async def transform_request_for_version(
        self,
        request: Dict[str, Any],
        from_version: str,
        to_version: str
    ) -> Dict[str, Any]:
        """
        Transform request data between versions
        Used for backward compatibility
        """
        # This is a simplified implementation
        # In a real system, you would have more complex transformation logic
        
        # For now, just pass through the request
        return request
    
    async def transform_response_for_version(
        self,
        response: Dict[str, Any],
        from_version: str,
        to_version: str
    ) -> Dict[str, Any]:
        """
        Transform response data between versions
        Used for backward compatibility
        """
        # This is a simplified implementation
        # In a real system, you would have more complex transformation logic
        
        # For now, just pass through the response
        return response
