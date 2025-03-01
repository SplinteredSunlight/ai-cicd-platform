from typing import Dict, List, Optional, Tuple, Any
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
import uuid
import structlog
from fastapi import HTTPException, Request

from ..config import get_settings
from ..models.gateway_models import ApiKey, UserInfo

# Configure structured logging
logger = structlog.get_logger()

class ApiKeyService:
    def __init__(self):
        self.settings = get_settings()
        
        # In-memory storage for API keys (in production, use a database)
        self._api_keys: Dict[str, ApiKey] = {}
        
        # Mapping of key prefixes to full keys for quick lookups
        self._prefix_map: Dict[str, str] = {}
    
    async def create_api_key(
        self,
        user_id: str,
        name: str,
        permissions: Optional[List[str]] = None,
        allowed_versions: Optional[List[str]] = None,
        allowed_services: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, ApiKey]:
        """
        Create a new API key for a user
        Returns the raw API key (to be shown to the user once) and the API key record
        """
        # Generate a secure random API key
        raw_key = f"ak_{secrets.token_urlsafe(32)}"
        key_prefix = raw_key[:8]  # First 8 chars as prefix
        
        # Hash the key for storage
        key_hash = self._hash_key(raw_key)
        
        # Set expiration if provided
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Create API key record
        api_key = ApiKey(
            key_id=str(uuid.uuid4()),
            key_prefix=key_prefix,
            key_hash=key_hash,
            user_id=user_id,
            name=name,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            enabled=True,
            permissions=permissions or [],
            allowed_versions=allowed_versions,
            allowed_services=allowed_services,
            metadata=metadata or {}
        )
        
        # Store the API key
        self._api_keys[api_key.key_id] = api_key
        self._prefix_map[key_prefix] = api_key.key_id
        
        logger.info(
            "API key created",
            key_id=api_key.key_id,
            user_id=user_id,
            name=name
        )
        
        return raw_key, api_key
    
    async def validate_api_key(
        self,
        api_key: str,
        service: Optional[str] = None,
        api_version: Optional[str] = None
    ) -> Optional[Tuple[ApiKey, UserInfo]]:
        """
        Validate an API key and return the associated API key record and user
        Returns None if the key is invalid
        """
        # Extract prefix for lookup
        if len(api_key) < 8:
            return None
        
        key_prefix = api_key[:8]
        
        # Look up the key ID from the prefix
        key_id = self._prefix_map.get(key_prefix)
        if not key_id:
            logger.warning("API key prefix not found", key_prefix=key_prefix)
            return None
        
        # Get the API key record
        api_key_record = self._api_keys.get(key_id)
        if not api_key_record:
            logger.warning("API key record not found", key_id=key_id)
            return None
        
        # Verify the key hash
        if not self._verify_key(api_key, api_key_record.key_hash):
            logger.warning("API key hash verification failed", key_id=key_id)
            return None
        
        # Check if the key is enabled
        if not api_key_record.enabled:
            logger.warning("API key is disabled", key_id=key_id)
            return None
        
        # Check if the key has expired
        if api_key_record.expires_at and datetime.utcnow() > api_key_record.expires_at:
            logger.warning("API key has expired", key_id=key_id)
            return None
        
        # Check if the service is allowed
        if service and api_key_record.allowed_services:
            if service not in api_key_record.allowed_services:
                logger.warning(
                    "API key not authorized for service",
                    key_id=key_id,
                    service=service
                )
                return None
        
        # Check if the API version is allowed
        if api_version and api_key_record.allowed_versions:
            if api_version not in api_key_record.allowed_versions:
                logger.warning(
                    "API key not authorized for API version",
                    key_id=key_id,
                    api_version=api_version
                )
                return None
        
        # Update last used timestamp
        api_key_record.last_used = datetime.utcnow()
        
        # In a real implementation, fetch the user from a database
        # This is a mock implementation
        user = UserInfo(
            user_id=api_key_record.user_id,
            username=f"user_{api_key_record.user_id}",
            email=f"user_{api_key_record.user_id}@example.com",
            roles=["developer"],
            permissions=api_key_record.permissions,
            api_keys=[api_key_record.key_id],
            allowed_versions=api_key_record.allowed_versions
        )
        
        return api_key_record, user
    
    async def revoke_api_key(self, key_id: str, user_id: Optional[str] = None) -> bool:
        """
        Revoke an API key
        If user_id is provided, only revoke if the key belongs to that user
        """
        api_key = self._api_keys.get(key_id)
        if not api_key:
            return False
        
        # Check if the key belongs to the user
        if user_id and api_key.user_id != user_id:
            logger.warning(
                "Unauthorized API key revocation attempt",
                key_id=key_id,
                user_id=user_id,
                key_owner=api_key.user_id
            )
            return False
        
        # Disable the key
        api_key.enabled = False
        
        logger.info(
            "API key revoked",
            key_id=key_id,
            user_id=api_key.user_id
        )
        
        return True
    
    async def get_user_api_keys(self, user_id: str) -> List[ApiKey]:
        """
        Get all API keys for a user
        """
        return [
            key for key in self._api_keys.values()
            if key.user_id == user_id and key.enabled
        ]
    
    async def get_api_key(self, key_id: str, user_id: Optional[str] = None) -> Optional[ApiKey]:
        """
        Get an API key by ID
        If user_id is provided, only return if the key belongs to that user
        """
        api_key = self._api_keys.get(key_id)
        if not api_key:
            return None
        
        # Check if the key belongs to the user
        if user_id and api_key.user_id != user_id:
            return None
        
        return api_key
    
    async def update_api_key(
        self,
        key_id: str,
        user_id: Optional[str] = None,
        name: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        allowed_versions: Optional[List[str]] = None,
        allowed_services: Optional[List[str]] = None,
        enabled: Optional[bool] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ApiKey]:
        """
        Update an API key
        If user_id is provided, only update if the key belongs to that user
        """
        api_key = self._api_keys.get(key_id)
        if not api_key:
            return None
        
        # Check if the key belongs to the user
        if user_id and api_key.user_id != user_id:
            logger.warning(
                "Unauthorized API key update attempt",
                key_id=key_id,
                user_id=user_id,
                key_owner=api_key.user_id
            )
            return None
        
        # Update fields if provided
        if name is not None:
            api_key.name = name
        
        if permissions is not None:
            api_key.permissions = permissions
        
        if allowed_versions is not None:
            api_key.allowed_versions = allowed_versions
        
        if allowed_services is not None:
            api_key.allowed_services = allowed_services
        
        if enabled is not None:
            api_key.enabled = enabled
        
        if expires_at is not None:
            api_key.expires_at = expires_at
        
        if metadata is not None:
            api_key.metadata = metadata
        
        logger.info(
            "API key updated",
            key_id=key_id,
            user_id=api_key.user_id
        )
        
        return api_key
    
    def _hash_key(self, key: str) -> str:
        """
        Hash an API key for secure storage
        """
        # Use a secure hashing algorithm with a salt
        salt = secrets.token_bytes(16)
        key_hash = hashlib.pbkdf2_hmac(
            'sha256',
            key.encode(),
            salt,
            100000  # Number of iterations
        )
        
        # Combine salt and hash for storage
        storage = salt + key_hash
        return base64.b64encode(storage).decode()
    
    def _verify_key(self, key: str, stored_hash: str) -> bool:
        """
        Verify an API key against a stored hash
        """
        try:
            # Decode the stored hash
            decoded = base64.b64decode(stored_hash)
            
            # Extract salt (first 16 bytes) and hash
            salt = decoded[:16]
            stored_key_hash = decoded[16:]
            
            # Hash the provided key with the same salt
            key_hash = hashlib.pbkdf2_hmac(
                'sha256',
                key.encode(),
                salt,
                100000  # Same number of iterations
            )
            
            # Compare the hashes
            return secrets.compare_digest(key_hash, stored_key_hash)
        except Exception as e:
            logger.error("API key verification error", error=str(e))
            return False
