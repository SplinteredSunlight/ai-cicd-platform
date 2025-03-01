import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
import jwt
import json

from ..services.token_service import TokenService
from ..models.gateway_models import (
    UserInfo,
    UserRole,
    AuthToken,
    TokenType
)

# Test fixtures
@pytest.fixture
def token_service():
    """Create an instance of TokenService for testing"""
    service = TokenService()
    # Mock the Redis connection
    service._redis = AsyncMock()
    # Initialize in-memory fallbacks
    service._blacklist = set()
    service._refresh_tokens = {}
    service._user_tokens = {}
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
def mock_request():
    """Create a mock request for testing"""
    mock_req = MagicMock()
    mock_req.client.host = "127.0.0.1"
    return mock_req

# Test token creation
@pytest.mark.asyncio
async def test_create_access_token(token_service, mock_user):
    """Test creating an access token"""
    # Test
    token = await token_service.create_access_token(mock_user)
    
    # Verify
    assert token.access_token is not None
    assert token.token_type == TokenType.BEARER
    assert token.expires_in > 0
    assert token.refresh_token is not None
    
    # Verify token contents
    payload = jwt.decode(
        token.access_token,
        options={"verify_signature": False}
    )
    assert payload["sub"] == mock_user.user_id
    assert payload["username"] == mock_user.username
    assert payload["email"] == mock_user.email
    assert "jti" in payload
    assert payload["type"] == "access"
    
    # Verify Redis storage
    if token_service._redis:
        token_service._redis.hset.assert_called_once()
        token_service._redis.expire.assert_called_once()

@pytest.mark.asyncio
async def test_create_access_token_without_refresh(token_service, mock_user):
    """Test creating an access token without a refresh token"""
    # Test
    token = await token_service.create_access_token(
        mock_user,
        include_refresh_token=False
    )
    
    # Verify
    assert token.access_token is not None
    assert token.token_type == TokenType.BEARER
    assert token.expires_in > 0
    assert token.refresh_token is None

@pytest.mark.asyncio
async def test_create_access_token_with_custom_expiry(token_service, mock_user):
    """Test creating an access token with custom expiration"""
    # Test
    custom_expiry = timedelta(minutes=5)
    token = await token_service.create_access_token(
        mock_user,
        expires_delta=custom_expiry
    )
    
    # Verify
    assert token.access_token is not None
    assert token.expires_in == 300  # 5 minutes in seconds
    
    # Verify token expiration
    payload = jwt.decode(
        token.access_token,
        options={"verify_signature": False}
    )
    exp_time = datetime.fromtimestamp(payload["exp"])
    iat_time = datetime.fromtimestamp(payload["iat"])
    assert (exp_time - iat_time).total_seconds() == pytest.approx(300, abs=2)  # Allow 2 seconds tolerance

@pytest.mark.asyncio
async def test_create_access_token_with_additional_claims(token_service, mock_user):
    """Test creating an access token with additional claims"""
    # Test
    additional_claims = {
        "custom_claim": "custom_value",
        "user_agent": "test_agent"
    }
    token = await token_service.create_access_token(
        mock_user,
        additional_claims=additional_claims
    )
    
    # Verify additional claims in token
    payload = jwt.decode(
        token.access_token,
        options={"verify_signature": False}
    )
    assert payload["custom_claim"] == "custom_value"
    assert payload["user_agent"] == "test_agent"

# Test token verification
@pytest.mark.asyncio
async def test_verify_token_success(token_service, mock_user):
    """Test successful token verification"""
    # Create a token
    token = await token_service.create_access_token(mock_user)
    
    # Test
    user = await token_service.verify_token(token.access_token)
    
    # Verify
    assert user is not None
    assert user.user_id == mock_user.user_id
    assert user.username == mock_user.username
    assert user.email == mock_user.email
    assert user.roles == mock_user.roles
    assert user.permissions == mock_user.permissions

@pytest.mark.asyncio
async def test_verify_token_blacklisted(token_service, mock_user):
    """Test verification of a blacklisted token"""
    # Create a token
    token = await token_service.create_access_token(mock_user)
    
    # Extract token ID
    payload = jwt.decode(
        token.access_token,
        options={"verify_signature": False}
    )
    token_id = payload["jti"]
    
    # Blacklist the token
    await token_service._blacklist_token(token_id, 3600)
    
    # Test
    with pytest.raises(Exception) as excinfo:
        await token_service.verify_token(token.access_token)
    
    # Verify
    assert "revoked" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_verify_token_expired(token_service, mock_user):
    """Test verification of an expired token"""
    # Create a token that expires immediately
    token = await token_service.create_access_token(
        mock_user,
        expires_delta=timedelta(seconds=-1)
    )
    
    # Test
    with pytest.raises(Exception) as excinfo:
        await token_service.verify_token(token.access_token)
    
    # Verify
    assert "expired" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_verify_token_invalid_type(token_service, mock_user):
    """Test verification with incorrect token type"""
    # Create a token
    token = await token_service.create_access_token(mock_user)
    
    # Test with wrong token type
    with pytest.raises(Exception) as excinfo:
        await token_service.verify_token(token.access_token, token_type="refresh")
    
    # Verify
    assert "token type" in str(excinfo.value).lower()

# Test refresh token functionality
@pytest.mark.asyncio
async def test_refresh_access_token(token_service, mock_user, mock_request):
    """Test refreshing an access token"""
    # Create a token with refresh token
    token = await token_service.create_access_token(mock_user)
    refresh_token = token.refresh_token
    
    # Mock the token verification
    with patch.object(token_service, '_validate_refresh_token', return_value=True):
        with patch.object(token_service, 'verify_token', return_value=mock_user):
            # Test
            new_token = await token_service.refresh_access_token(refresh_token, mock_request)
            
            # Verify
            assert new_token.access_token is not None
            assert new_token.access_token != token.access_token
            assert new_token.token_type == TokenType.BEARER
            assert new_token.expires_in > 0
            assert new_token.refresh_token is not None
            assert new_token.refresh_token != refresh_token  # Token rotation

@pytest.mark.asyncio
async def test_refresh_access_token_invalid(token_service, mock_request):
    """Test refreshing with an invalid refresh token"""
    # Test with invalid token
    with pytest.raises(Exception) as excinfo:
        await token_service.refresh_access_token("invalid_refresh_token", mock_request)
    
    # Verify
    assert "invalid" in str(excinfo.value).lower()

@pytest.mark.asyncio
async def test_refresh_access_token_expired(token_service, mock_user, mock_request):
    """Test refreshing with an expired refresh token"""
    # Create a token with refresh token that expires immediately
    with patch.object(token_service, '_create_refresh_token') as mock_create_refresh:
        # Create a refresh token that's already expired
        expired_token = jwt.encode(
            {
                "sub": mock_user.user_id,
                "exp": datetime.utcnow() - timedelta(days=1),
                "iat": datetime.utcnow() - timedelta(days=2),
                "jti": "test_jti",
                "type": "refresh",
                "parent_jti": "parent_jti"
            },
            token_service.settings.jwt_secret_key,
            algorithm=token_service.settings.jwt_algorithm
        )
        mock_create_refresh.return_value = expired_token
        
        token = await token_service.create_access_token(mock_user)
        
        # Test with expired token
        with pytest.raises(Exception) as excinfo:
            await token_service.refresh_access_token(token.refresh_token, mock_request)
        
        # Verify
        assert "expired" in str(excinfo.value).lower()

# Test token revocation
@pytest.mark.asyncio
async def test_revoke_token(token_service, mock_user):
    """Test revoking a token"""
    # Create a token
    token = await token_service.create_access_token(mock_user)
    
    # Test
    await token_service.revoke_token(token.access_token)
    
    # Verify token is blacklisted
    payload = jwt.decode(
        token.access_token,
        options={"verify_signature": False}
    )
    token_id = payload["jti"]
    
    is_blacklisted = await token_service._is_token_blacklisted(token_id)
    assert is_blacklisted is True
    
    # Verify refresh token is also revoked
    if token_service._redis:
        token_service._redis.keys.assert_called_once()
        token_service._redis.delete.assert_called_once()

@pytest.mark.asyncio
async def test_revoke_all_user_tokens(token_service, mock_user):
    """Test revoking all tokens for a user"""
    # Create multiple tokens for the user
    token1 = await token_service.create_access_token(mock_user)
    token2 = await token_service.create_access_token(mock_user)
    
    # Test
    await token_service.revoke_all_user_tokens(mock_user.user_id)
    
    # Verify all tokens are blacklisted
    if token_service._redis:
        # Check that Redis operations were called
        token_service._redis.hgetall.assert_called_once()
        token_service._redis.keys.assert_called_once()
        token_service._redis.delete.assert_called()
    else:
        # For in-memory fallback, check that tokens are in blacklist
        payload1 = jwt.decode(
            token1.access_token,
            options={"verify_signature": False}
        )
        payload2 = jwt.decode(
            token2.access_token,
            options={"verify_signature": False}
        )
        
        # Check if user's tokens are removed from user_tokens
        assert mock_user.user_id not in token_service._user_tokens

# Test token blacklisting
@pytest.mark.asyncio
async def test_blacklist_token(token_service):
    """Test blacklisting a token"""
    # Test
    await token_service._blacklist_token("test_token_id", 3600)
    
    # Verify
    if token_service._redis:
        token_service._redis.set.assert_called_once_with(
            f"{token_service.BLACKLIST_PREFIX}test_token_id",
            "1",
            ex=3600
        )
    else:
        assert "test_token_id" in token_service._blacklist

@pytest.mark.asyncio
async def test_is_token_blacklisted(token_service):
    """Test checking if a token is blacklisted"""
    # Setup
    await token_service._blacklist_token("test_token_id", 3600)
    
    # Test
    is_blacklisted = await token_service._is_token_blacklisted("test_token_id")
    
    # Verify
    assert is_blacklisted is True
    
    # Test non-blacklisted token
    is_blacklisted = await token_service._is_token_blacklisted("non_blacklisted_token")
    assert is_blacklisted is False

# Test refresh token validation
@pytest.mark.asyncio
async def test_validate_refresh_token(token_service):
    """Test validating a refresh token"""
    # Setup - store a refresh token
    user_id = "test_user_id"
    refresh_token_id = "test_refresh_token_id"
    access_token_id = "test_access_token_id"
    
    if token_service._redis:
        # Mock Redis get to return valid data
        token_service._redis.get.return_value = json.dumps({
            "access_token_id": access_token_id,
            "exp": (datetime.utcnow() + timedelta(days=7)).timestamp()
        })
    else:
        # Set up in-memory data
        key = f"{user_id}:{refresh_token_id}"
        token_service._refresh_tokens[key] = {
            "access_token_id": access_token_id,
            "exp": (datetime.utcnow() + timedelta(days=7)).timestamp()
        }
    
    # Test
    is_valid = await token_service._validate_refresh_token(
        user_id,
        refresh_token_id,
        access_token_id
    )
    
    # Verify
    assert is_valid is True
    
    # Test with mismatched access token ID
    is_valid = await token_service._validate_refresh_token(
        user_id,
        refresh_token_id,
        "wrong_access_token_id"
    )
    assert is_valid is False
    
    # Test with non-existent refresh token
    is_valid = await token_service._validate_refresh_token(
        user_id,
        "non_existent_refresh_token_id",
        access_token_id
    )
    assert is_valid is False

@pytest.mark.asyncio
async def test_invalidate_refresh_token(token_service):
    """Test invalidating a refresh token"""
    # Setup - store a refresh token
    user_id = "test_user_id"
    refresh_token_id = "test_refresh_token_id"
    
    if token_service._redis:
        # Set up for Redis test
        refresh_key = f"{token_service.REFRESH_PREFIX}{user_id}:{refresh_token_id}"
    else:
        # Set up in-memory data
        key = f"{user_id}:{refresh_token_id}"
        token_service._refresh_tokens[key] = {
            "access_token_id": "test_access_token_id",
            "exp": (datetime.utcnow() + timedelta(days=7)).timestamp()
        }
    
    # Test
    await token_service._invalidate_refresh_token(user_id, refresh_token_id)
    
    # Verify
    if token_service._redis:
        refresh_key = f"{token_service.REFRESH_PREFIX}{user_id}:{refresh_token_id}"
        token_service._redis.delete.assert_called_once_with(refresh_key)
    else:
        key = f"{user_id}:{refresh_token_id}"
        assert key not in token_service._refresh_tokens

# Test cleanup
@pytest.mark.asyncio
async def test_cleanup(token_service):
    """Test cleanup method"""
    # Setup
    token_service._cleanup_task = MagicMock()
    token_service._cleanup_task.cancel = MagicMock()
    token_service._init_task = MagicMock()
    token_service._init_task.cancel = MagicMock()
    
    # Test
    await token_service.cleanup()
    
    # Verify
    token_service._cleanup_task.cancel.assert_called_once()
    token_service._init_task.cancel.assert_called_once()
    if token_service._redis:
        token_service._redis.close.assert_called_once()
