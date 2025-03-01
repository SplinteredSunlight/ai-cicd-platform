import pytest
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import base64
import hashlib
import secrets

# Add the parent directory to sys.path to allow imports from the main application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.api_key_service import ApiKeyService
from models.gateway_models import ApiKey, UserInfo

@pytest.fixture
def api_key_service():
    """Create an ApiKeyService instance for testing"""
    return ApiKeyService()

@pytest.mark.asyncio
async def test_create_api_key(api_key_service):
    """Test creating a new API key"""
    # Create a new API key
    user_id = "test_user_id"
    name = "Test API Key"
    permissions = ["read:all", "write:own"]
    allowed_versions = ["1", "2"]
    allowed_services = ["pipeline-generator", "security-enforcement"]
    expires_in_days = 30
    metadata = {"created_by": "test", "purpose": "testing"}
    
    raw_key, api_key = await api_key_service.create_api_key(
        user_id=user_id,
        name=name,
        permissions=permissions,
        allowed_versions=allowed_versions,
        allowed_services=allowed_services,
        expires_in_days=expires_in_days,
        metadata=metadata
    )
    
    # Verify the raw key format
    assert raw_key.startswith("ak_")
    assert len(raw_key) > 10
    
    # Verify the API key record
    assert api_key.user_id == user_id
    assert api_key.name == name
    assert api_key.permissions == permissions
    assert api_key.allowed_versions == allowed_versions
    assert api_key.allowed_services == allowed_services
    assert api_key.enabled is True
    assert api_key.metadata == metadata
    
    # Verify expiration date
    assert api_key.expires_at is not None
    expected_expiry = datetime.utcnow() + timedelta(days=expires_in_days)
    # Allow for a small time difference due to test execution
    assert abs((api_key.expires_at - expected_expiry).total_seconds()) < 5
    
    # Verify the key is stored in the service
    assert api_key.key_id in api_key_service._api_keys
    assert api_key.key_prefix in api_key_service._prefix_map
    assert api_key_service._prefix_map[api_key.key_prefix] == api_key.key_id

@pytest.mark.asyncio
async def test_validate_api_key(api_key_service):
    """Test validating an API key"""
    # Create a new API key
    user_id = "test_user_id"
    name = "Test API Key"
    permissions = ["read:all"]
    allowed_versions = ["1", "2"]
    allowed_services = ["pipeline-generator"]
    
    raw_key, api_key = await api_key_service.create_api_key(
        user_id=user_id,
        name=name,
        permissions=permissions,
        allowed_versions=allowed_versions,
        allowed_services=allowed_services
    )
    
    # Validate the key
    result = await api_key_service.validate_api_key(raw_key)
    assert result is not None
    
    validated_key, user = result
    assert validated_key.key_id == api_key.key_id
    assert validated_key.user_id == user_id
    assert user.user_id == user_id
    assert user.permissions == permissions
    
    # Test with service restriction
    result = await api_key_service.validate_api_key(raw_key, service="pipeline-generator")
    assert result is not None
    
    result = await api_key_service.validate_api_key(raw_key, service="unknown-service")
    assert result is None
    
    # Test with version restriction
    result = await api_key_service.validate_api_key(raw_key, api_version="1")
    assert result is not None
    
    result = await api_key_service.validate_api_key(raw_key, api_version="3")
    assert result is None
    
    # Test with invalid key
    result = await api_key_service.validate_api_key("invalid-key")
    assert result is None
    
    # Test with too short key
    result = await api_key_service.validate_api_key("short")
    assert result is None

@pytest.mark.asyncio
async def test_revoke_api_key(api_key_service):
    """Test revoking an API key"""
    # Create a new API key
    user_id = "test_user_id"
    name = "Test API Key"
    
    raw_key, api_key = await api_key_service.create_api_key(
        user_id=user_id,
        name=name
    )
    
    # Verify the key is valid
    result = await api_key_service.validate_api_key(raw_key)
    assert result is not None
    
    # Revoke the key
    success = await api_key_service.revoke_api_key(api_key.key_id)
    assert success is True
    
    # Verify the key is no longer valid
    result = await api_key_service.validate_api_key(raw_key)
    assert result is None
    
    # Verify the key is still in storage but disabled
    assert api_key.key_id in api_key_service._api_keys
    assert api_key_service._api_keys[api_key.key_id].enabled is False
    
    # Test revoking with user_id restriction
    raw_key2, api_key2 = await api_key_service.create_api_key(
        user_id="another_user",
        name="Another Key"
    )
    
    # Try to revoke with wrong user_id
    success = await api_key_service.revoke_api_key(api_key2.key_id, user_id="wrong_user")
    assert success is False
    
    # Verify the key is still valid
    result = await api_key_service.validate_api_key(raw_key2)
    assert result is not None
    
    # Revoke with correct user_id
    success = await api_key_service.revoke_api_key(api_key2.key_id, user_id="another_user")
    assert success is True
    
    # Verify the key is no longer valid
    result = await api_key_service.validate_api_key(raw_key2)
    assert result is None

@pytest.mark.asyncio
async def test_get_user_api_keys(api_key_service):
    """Test getting all API keys for a user"""
    # Create multiple keys for the same user
    user_id = "test_user_id"
    
    # Create first key
    raw_key1, api_key1 = await api_key_service.create_api_key(
        user_id=user_id,
        name="Key 1"
    )
    
    # Create second key
    raw_key2, api_key2 = await api_key_service.create_api_key(
        user_id=user_id,
        name="Key 2"
    )
    
    # Create key for another user
    raw_key3, api_key3 = await api_key_service.create_api_key(
        user_id="another_user",
        name="Another Key"
    )
    
    # Get keys for the user
    keys = await api_key_service.get_user_api_keys(user_id)
    
    # Verify we got both keys for the user
    assert len(keys) == 2
    key_ids = [key.key_id for key in keys]
    assert api_key1.key_id in key_ids
    assert api_key2.key_id in key_ids
    assert api_key3.key_id not in key_ids
    
    # Revoke one key
    await api_key_service.revoke_api_key(api_key1.key_id)
    
    # Get keys again
    keys = await api_key_service.get_user_api_keys(user_id)
    
    # Verify we only get the enabled key
    assert len(keys) == 1
    assert keys[0].key_id == api_key2.key_id

@pytest.mark.asyncio
async def test_get_api_key(api_key_service):
    """Test getting an API key by ID"""
    # Create a new API key
    user_id = "test_user_id"
    name = "Test API Key"
    
    raw_key, api_key = await api_key_service.create_api_key(
        user_id=user_id,
        name=name
    )
    
    # Get the key by ID
    retrieved_key = await api_key_service.get_api_key(api_key.key_id)
    assert retrieved_key is not None
    assert retrieved_key.key_id == api_key.key_id
    
    # Get with user_id restriction
    retrieved_key = await api_key_service.get_api_key(api_key.key_id, user_id=user_id)
    assert retrieved_key is not None
    
    # Get with wrong user_id
    retrieved_key = await api_key_service.get_api_key(api_key.key_id, user_id="wrong_user")
    assert retrieved_key is None
    
    # Get non-existent key
    retrieved_key = await api_key_service.get_api_key("non-existent-id")
    assert retrieved_key is None

@pytest.mark.asyncio
async def test_update_api_key(api_key_service):
    """Test updating an API key"""
    # Create a new API key
    user_id = "test_user_id"
    name = "Test API Key"
    permissions = ["read:all"]
    
    raw_key, api_key = await api_key_service.create_api_key(
        user_id=user_id,
        name=name,
        permissions=permissions
    )
    
    # Update the key
    new_name = "Updated Key Name"
    new_permissions = ["read:all", "write:own"]
    new_allowed_versions = ["1", "2"]
    new_metadata = {"updated": True}
    
    updated_key = await api_key_service.update_api_key(
        key_id=api_key.key_id,
        name=new_name,
        permissions=new_permissions,
        allowed_versions=new_allowed_versions,
        metadata=new_metadata
    )
    
    # Verify the update
    assert updated_key is not None
    assert updated_key.name == new_name
    assert updated_key.permissions == new_permissions
    assert updated_key.allowed_versions == new_allowed_versions
    assert updated_key.metadata == new_metadata
    
    # Verify the key in storage was updated
    stored_key = api_key_service._api_keys[api_key.key_id]
    assert stored_key.name == new_name
    assert stored_key.permissions == new_permissions
    
    # Test update with user_id restriction
    raw_key2, api_key2 = await api_key_service.create_api_key(
        user_id="another_user",
        name="Another Key"
    )
    
    # Try to update with wrong user_id
    updated_key = await api_key_service.update_api_key(
        key_id=api_key2.key_id,
        user_id="wrong_user",
        name="Should Not Update"
    )
    assert updated_key is None
    
    # Verify the key was not updated
    stored_key = api_key_service._api_keys[api_key2.key_id]
    assert stored_key.name == "Another Key"
    
    # Update with correct user_id
    updated_key = await api_key_service.update_api_key(
        key_id=api_key2.key_id,
        user_id="another_user",
        name="Successfully Updated"
    )
    assert updated_key is not None
    assert updated_key.name == "Successfully Updated"

@pytest.mark.asyncio
async def test_key_expiration(api_key_service):
    """Test API key expiration"""
    # Create a key that expires in the past
    user_id = "test_user_id"
    name = "Expired Key"
    
    raw_key, api_key = await api_key_service.create_api_key(
        user_id=user_id,
        name=name
    )
    
    # Set expiration to the past
    api_key.expires_at = datetime.utcnow() - timedelta(days=1)
    
    # Verify the key is not valid
    result = await api_key_service.validate_api_key(raw_key)
    assert result is None
    
    # Create a key that expires in the future
    raw_key2, api_key2 = await api_key_service.create_api_key(
        user_id=user_id,
        name="Valid Key",
        expires_in_days=30
    )
    
    # Verify the key is valid
    result = await api_key_service.validate_api_key(raw_key2)
    assert result is not None

@pytest.mark.asyncio
async def test_hash_and_verify_key(api_key_service):
    """Test hashing and verifying API keys"""
    # Test key hashing
    test_key = "ak_test_key"
    key_hash = api_key_service._hash_key(test_key)
    
    # Verify the hash is not the original key
    assert key_hash != test_key
    
    # Verify the key against the hash
    is_valid = api_key_service._verify_key(test_key, key_hash)
    assert is_valid is True
    
    # Verify a different key fails
    is_valid = api_key_service._verify_key("wrong_key", key_hash)
    assert is_valid is False
