import pytest
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from unittest.mock import MagicMock, patch

from ..services.auth_service import AuthService
from ..models.gateway_models import UserInfo, UserRole, MFAMethod, TokenType, RateLimitState

# Test fixtures
@pytest.fixture
def auth_service():
    """Create an instance of AuthService for testing"""
    return AuthService()

@pytest.fixture
def mock_user():
    """Create a mock user for testing"""
    return UserInfo(
        user_id="test_user_id",
        username="testuser",
        email="test@example.com",
        roles=[UserRole.DEVELOPER],
        permissions=["read:all", "write:own"],
        metadata={"mfa_enabled": False}
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
        metadata={"mfa_enabled": True, "mfa_methods": [MFAMethod.TOTP]}
    )

@pytest.fixture
def mock_request():
    """Create a mock request for testing"""
    mock_req = MagicMock()
    mock_req.client.host = "127.0.0.1"
    return mock_req

# Test authentication
@pytest.mark.asyncio
async def test_authenticate_user_success(auth_service, mock_request):
    """Test successful user authentication"""
    # Mock the verify_password method
    auth_service.verify_password = lambda plain, hashed: plain == "password" and hashed == "hashed_admin_pwd"
    
    user = await auth_service.authenticate_user("admin", "password", mock_request)
    
    assert user is not None
    assert user.username == "admin"
    assert user.roles == [UserRole.ADMIN]
    assert user.permissions == ["*"]
    assert user.metadata.get("mfa_enabled") is True

@pytest.mark.asyncio
async def test_authenticate_user_failure(auth_service, mock_request):
    """Test failed user authentication"""
    # Mock the verify_password method
    auth_service.verify_password = lambda plain, hashed: False
    
    user = await auth_service.authenticate_user("admin", "wrong_password", mock_request)
    
    assert user is None

@pytest.mark.asyncio
async def test_authenticate_user_rate_limit(auth_service, mock_request):
    """Test authentication rate limiting"""
    # Enable rate limiting
    auth_service.settings.auth_rate_limit_enabled = True
    auth_service.settings.auth_rate_limit_max_attempts = 3
    auth_service.settings.auth_rate_limit_window = 15
    auth_service.settings.auth_rate_limit_track_by_ip = True
    auth_service.settings.auth_rate_limit_track_by_username = False
    
    # Create a rate limit state with exceeded requests
    client_ip = mock_request.client.host
    now = datetime.utcnow()
    auth_service.auth_attempts[client_ip] = RateLimitState(
        key=client_ip,
        window_start=now,
        request_count=3,  # At the limit
        window_size=60,
        limit=3,
        failed_count=3,
        successful_count=0,
        consecutive_failures=3,
        last_attempt_time=now,
        lockout_until=None
    )
    
    # This should exceed the rate limit
    with pytest.raises(HTTPException) as excinfo:
        await auth_service.authenticate_user("admin", "password", mock_request)
    
    assert excinfo.value.status_code == 429
    assert "Rate limit exceeded" in excinfo.value.detail

@pytest.mark.asyncio
async def test_authenticate_user_lockout(auth_service, mock_request):
    """Test authentication lockout"""
    # Enable rate limiting with lockout
    auth_service.settings.auth_rate_limit_enabled = True
    auth_service.settings.auth_rate_limit_track_by_ip = True
    auth_service.settings.auth_rate_limit_progressive_lockout = True
    
    # Create a rate limit state with lockout
    client_ip = mock_request.client.host
    now = datetime.utcnow()
    lockout_until = now + timedelta(minutes=15)
    auth_service.auth_attempts[client_ip] = RateLimitState(
        key=client_ip,
        window_start=now,
        request_count=5,
        window_size=60,
        limit=3,
        failed_count=5,
        successful_count=0,
        consecutive_failures=5,
        last_attempt_time=now,
        lockout_until=lockout_until
    )
    
    # This should be locked out
    with pytest.raises(HTTPException) as excinfo:
        await auth_service.authenticate_user("admin", "password", mock_request)
    
    assert excinfo.value.status_code == 429
    assert "locked" in excinfo.value.detail.lower()

# Test token creation and verification
@pytest.mark.asyncio
async def test_create_access_token(auth_service, mock_user):
    """Test creating an access token"""
    token = await auth_service.create_access_token(mock_user)
    
    assert token.access_token is not None
    assert token.token_type == TokenType.BEARER
    assert token.expires_in > 0
    assert token.refresh_token is not None

@pytest.mark.asyncio
async def test_verify_token_success(auth_service, mock_user):
    """Test successful token verification"""
    token = await auth_service.create_access_token(mock_user)
    
    user = await auth_service.verify_token(token.access_token)
    
    assert user is not None
    assert user.user_id == mock_user.user_id
    assert user.username == mock_user.username
    assert user.roles == mock_user.roles

@pytest.mark.asyncio
async def test_verify_token_expired(auth_service, mock_user):
    """Test expired token verification"""
    # Create a token that expires immediately
    token = await auth_service.create_access_token(
        mock_user,
        expires_delta=timedelta(seconds=-1)
    )
    
    with pytest.raises(HTTPException) as excinfo:
        await auth_service.verify_token(token.access_token)
    
    assert excinfo.value.status_code == 401
    assert "Token has expired" in excinfo.value.detail

@pytest.mark.asyncio
async def test_verify_token_revoked(auth_service, mock_user):
    """Test revoked token verification"""
    token = await auth_service.create_access_token(mock_user)
    
    # Revoke the token
    await auth_service.revoke_token(token.access_token)
    
    with pytest.raises(HTTPException) as excinfo:
        await auth_service.verify_token(token.access_token)
    
    assert excinfo.value.status_code == 401
    assert "Token has been revoked" in excinfo.value.detail

# Test refresh token functionality
@pytest.mark.asyncio
async def test_refresh_access_token(auth_service, mock_user, mock_request):
    """Test refreshing an access token"""
    token = await auth_service.create_access_token(mock_user)
    
    # Mock the user lookup for refresh token
    auth_service.refresh_tokens[mock_user.user_id] = token.refresh_token
    
    # Create a new token using the refresh token
    new_token = await auth_service.refresh_access_token(token.refresh_token, mock_request)
    
    assert new_token.access_token is not None
    assert new_token.access_token != token.access_token
    assert new_token.token_type == TokenType.BEARER
    assert new_token.expires_in > 0

@pytest.mark.asyncio
async def test_refresh_access_token_invalid(auth_service, mock_request):
    """Test refreshing with an invalid refresh token"""
    with pytest.raises(HTTPException) as excinfo:
        await auth_service.refresh_access_token("invalid_refresh_token", mock_request)
    
    assert excinfo.value.status_code == 401
    assert "Invalid refresh token" in excinfo.value.detail

@pytest.mark.asyncio
async def test_refresh_access_token_rate_limit(auth_service, mock_request):
    """Test refresh token rate limiting"""
    # Enable rate limiting
    auth_service.settings.auth_rate_limit_enabled = True
    auth_service.settings.auth_rate_limit_track_by_ip = True
    
    # Create a rate limit state with exceeded requests
    client_ip = mock_request.client.host
    now = datetime.utcnow()
    auth_service.auth_attempts[client_ip] = RateLimitState(
        key=client_ip,
        window_start=now,
        request_count=10,  # Exceeded
        window_size=60,
        limit=3,
        failed_count=10,
        successful_count=0,
        consecutive_failures=5,
        last_attempt_time=now,
        lockout_until=None
    )
    
    # This should exceed the rate limit
    with pytest.raises(HTTPException) as excinfo:
        await auth_service.refresh_access_token("any_token", mock_request)
    
    assert excinfo.value.status_code == 429
    assert "Rate limit exceeded" in excinfo.value.detail

# Test MFA functionality
@pytest.mark.asyncio
async def test_setup_mfa(auth_service):
    """Test setting up MFA"""
    user_id = "test_user_id"
    
    mfa_data = await auth_service.setup_mfa(user_id, MFAMethod.TOTP)
    
    assert "secret" in mfa_data
    assert "provisioning_uri" in mfa_data
    assert user_id in auth_service.mfa_secrets
    assert auth_service.mfa_secrets[user_id]["method"] == MFAMethod.TOTP.value
    assert auth_service.mfa_secrets[user_id]["verified"] is False

@pytest.mark.asyncio
async def test_verify_mfa_success(auth_service, mock_request):
    """Test successful MFA verification"""
    user_id = "test_user_id"
    
    # Setup MFA
    await auth_service.setup_mfa(user_id, MFAMethod.TOTP)
    
    # Mock the TOTP verification
    with patch('pyotp.TOTP.verify', return_value=True):
        result = await auth_service.verify_mfa(user_id, "123456", mock_request)
        
        assert result is True
        assert auth_service.mfa_secrets[user_id]["verified"] is True

@pytest.mark.asyncio
async def test_verify_mfa_failure(auth_service, mock_request):
    """Test failed MFA verification"""
    user_id = "test_user_id"
    
    # Setup MFA
    await auth_service.setup_mfa(user_id, MFAMethod.TOTP)
    
    # Mock the TOTP verification
    with patch('pyotp.TOTP.verify', return_value=False):
        result = await auth_service.verify_mfa(user_id, "wrong_code", mock_request)
        
        assert result is False
        assert auth_service.mfa_secrets[user_id]["verified"] is False

@pytest.mark.asyncio
async def test_verify_mfa_rate_limit(auth_service, mock_request):
    """Test MFA verification rate limiting"""
    # Enable rate limiting
    auth_service.settings.auth_rate_limit_enabled = True
    auth_service.settings.auth_rate_limit_track_by_ip = True
    
    # Create a rate limit state with exceeded requests
    client_ip = mock_request.client.host
    now = datetime.utcnow()
    auth_service.auth_attempts[client_ip] = RateLimitState(
        key=client_ip,
        window_start=now,
        request_count=10,  # Exceeded
        window_size=60,
        limit=3,
        failed_count=10,
        successful_count=0,
        consecutive_failures=5,
        last_attempt_time=now,
        lockout_until=None
    )
    
    # This should silently fail due to rate limiting
    result = await auth_service.verify_mfa("any_user_id", "123456", mock_request)
    assert result is False

@pytest.mark.asyncio
async def test_disable_mfa(auth_service):
    """Test disabling MFA"""
    user_id = "test_user_id"
    
    # Setup MFA
    await auth_service.setup_mfa(user_id, MFAMethod.TOTP)
    
    # Disable MFA
    result = await auth_service.disable_mfa(user_id)
    
    assert result is True
    assert user_id not in auth_service.mfa_secrets

# Test permission checking
@pytest.mark.asyncio
async def test_check_permissions_admin(auth_service, mock_admin_user):
    """Test permission checking for admin user"""
    # Admin should have all permissions
    result = await auth_service.check_permissions(
        mock_admin_user,
        [UserRole.DEVELOPER],
        ["read:all", "write:all", "delete:all"]
    )
    
    assert result is True

@pytest.mark.asyncio
async def test_check_permissions_role_match(auth_service, mock_user):
    """Test permission checking with matching role"""
    result = await auth_service.check_permissions(
        mock_user,
        [UserRole.DEVELOPER],
        ["read:all"]
    )
    
    assert result is True

@pytest.mark.asyncio
async def test_check_permissions_role_mismatch(auth_service, mock_user):
    """Test permission checking with mismatched role"""
    result = await auth_service.check_permissions(
        mock_user,
        [UserRole.ADMIN],
        ["read:all"]
    )
    
    assert result is False

@pytest.mark.asyncio
async def test_check_permissions_permission_match(auth_service, mock_user):
    """Test permission checking with matching permissions"""
    result = await auth_service.check_permissions(
        mock_user,
        [],
        ["read:all", "write:own"]
    )
    
    assert result is True

@pytest.mark.asyncio
async def test_check_permissions_permission_mismatch(auth_service, mock_user):
    """Test permission checking with mismatched permissions"""
    result = await auth_service.check_permissions(
        mock_user,
        [],
        ["read:all", "write:own", "delete:all"]
    )
    
    assert result is False

# Test API key functionality
@pytest.mark.asyncio
async def test_create_and_verify_api_key(auth_service, mock_user):
    """Test creating and verifying an API key"""
    api_key = await auth_service.create_api_key(mock_user)
    
    assert api_key.startswith("ak_")
    assert len(api_key) > 20
    
    user = await auth_service.verify_api_key(api_key)
    
    assert user is not None
    assert user.user_id == mock_user.user_id
    assert user.username == mock_user.username

@pytest.mark.asyncio
async def test_revoke_api_key(auth_service, mock_user):
    """Test revoking an API key"""
    api_key = await auth_service.create_api_key(mock_user)
    
    # Verify the API key works
    user = await auth_service.verify_api_key(api_key)
    assert user is not None
    
    # Revoke the API key
    await auth_service.revoke_api_key(api_key)
    
    # Verify the API key no longer works
    user = await auth_service.verify_api_key(api_key)
    assert user is None

# Test cleanup functionality
@pytest.mark.asyncio
async def test_cleanup(auth_service, mock_user):
    """Test cleanup of expired tokens and auth attempts"""
    # Add some expired tokens
    token = await auth_service.create_access_token(
        mock_user,
        expires_delta=timedelta(seconds=-1)
    )
    auth_service.revoked_tokens.add(token.access_token)
    
    # Add some old auth attempts with no activity
    old_time = datetime.utcnow() - timedelta(minutes=30)
    auth_service.auth_attempts["127.0.0.1"] = RateLimitState(
        key="127.0.0.1",
        window_start=old_time,
        request_count=0,
        window_size=60,
        limit=3,
        failed_count=0,
        successful_count=0,
        consecutive_failures=0,
        last_attempt_time=old_time,
        lockout_until=None
    )
    
    # Run cleanup
    await auth_service.cleanup()
    
    # Check that expired tokens and old auth attempts are removed
    assert len(auth_service.revoked_tokens) == 0
    assert "127.0.0.1" not in auth_service.auth_attempts

@pytest.mark.asyncio
async def test_cleanup_with_consecutive_failures(auth_service):
    """Test cleanup preserves consecutive failures"""
    # Add auth attempts with consecutive failures
    now = datetime.utcnow()
    old_time = now - timedelta(minutes=30)
    auth_service.auth_attempts["127.0.0.1"] = RateLimitState(
        key="127.0.0.1",
        window_start=old_time,
        request_count=5,
        window_size=60,
        limit=3,
        failed_count=5,
        successful_count=0,
        consecutive_failures=3,  # Has consecutive failures
        last_attempt_time=old_time,
        lockout_until=None
    )
    
    # Run cleanup
    await auth_service.cleanup()
    
    # Check that the state is reset but consecutive failures are preserved
    assert "127.0.0.1" in auth_service.auth_attempts
    assert auth_service.auth_attempts["127.0.0.1"].consecutive_failures == 3
    assert auth_service.auth_attempts["127.0.0.1"].request_count == 0
    assert auth_service.auth_attempts["127.0.0.1"].failed_count == 0
    assert auth_service.auth_attempts["127.0.0.1"].successful_count == 0
