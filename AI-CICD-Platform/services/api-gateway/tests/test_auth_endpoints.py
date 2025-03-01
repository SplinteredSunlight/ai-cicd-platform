import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
from datetime import timedelta

from ..main import app
from ..models.gateway_models import UserInfo, UserRole, MFAMethod, TokenType, AuthToken

# Test client
@pytest.fixture
def client():
    return TestClient(app)

# Mock user data
@pytest.fixture
def mock_user_data():
    return UserInfo(
        user_id="test_user_id",
        username="testuser",
        email="test@example.com",
        roles=[UserRole.DEVELOPER],
        permissions=["read:all", "write:own"],
        metadata={}
    )

@pytest.fixture
def mock_mfa_user_data():
    return UserInfo(
        user_id="mfa_user_id",
        username="mfauser",
        email="mfa@example.com",
        roles=[UserRole.DEVELOPER],
        permissions=["read:all", "write:own"],
        metadata={
            "mfa_enabled": True,
            "mfa_methods": [MFAMethod.TOTP]
        }
    )

# Test login endpoint
def test_login_success(client):
    """Test successful login without MFA"""
    # Mock the authenticate_user and create_access_token methods
    with patch('app.gateway_service.auth_service.authenticate_user') as mock_auth, \
         patch('app.gateway_service.auth_service.create_access_token') as mock_token:
        
        # Setup mocks
        mock_user = UserInfo(
            user_id="test_user_id",
            username="testuser",
            email="test@example.com",
            roles=[UserRole.DEVELOPER],
            permissions=["read:all"],
            metadata={}
        )
        mock_auth.return_value = mock_user
        
        mock_token.return_value = AuthToken(
            access_token="test_access_token",
            token_type=TokenType.BEARER,
            expires_in=1800,
            refresh_token="test_refresh_token"
        )
        
        # Make request
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "testuser", "password": "password"}
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "test_access_token"
        assert data["token_type"] == TokenType.BEARER
        assert data["expires_in"] == 1800
        assert data["refresh_token"] == "test_refresh_token"
        
        # Verify mocks were called correctly
        mock_auth.assert_called_once()
        mock_token.assert_called_once()

def test_login_with_mfa(client):
    """Test login with MFA required"""
    # Mock the authenticate_user and create_access_token methods
    with patch('app.gateway_service.auth_service.authenticate_user') as mock_auth, \
         patch('app.gateway_service.auth_service.create_access_token') as mock_token:
        
        # Setup mocks
        mock_user = UserInfo(
            user_id="mfa_user_id",
            username="mfauser",
            email="mfa@example.com",
            roles=[UserRole.DEVELOPER],
            permissions=["read:all"],
            metadata={
                "mfa_enabled": True,
                "mfa_methods": [MFAMethod.TOTP]
            }
        )
        mock_auth.return_value = mock_user
        
        mock_token.return_value = AuthToken(
            access_token="partial_token",
            token_type=TokenType.BEARER,
            expires_in=300,  # 5 minutes
            refresh_token=None
        )
        
        # Make request
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "mfauser", "password": "password"}
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "mfa_required"
        assert data["token"] == "partial_token"
        assert MFAMethod.TOTP in data["mfa_methods"]
        
        # Verify mocks were called correctly
        mock_auth.assert_called_once()
        mock_token.assert_called_once_with(
            mock_user,
            expires_delta=timedelta(minutes=5),
            include_refresh_token=False
        )

def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    # Mock the authenticate_user method to return None (invalid credentials)
    with patch('app.gateway_service.auth_service.authenticate_user', return_value=None):
        # Make request
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "invalid", "password": "wrong"}
        )
        
        # Check response
        assert response.status_code == 401
        data = response.json()
        assert "Invalid credentials" in data["detail"]

# Test MFA verification endpoint
def test_verify_mfa_success(client):
    """Test successful MFA verification"""
    # Mock the verify_token, verify_mfa, and create_access_token methods
    with patch('app.gateway_service.auth_service.verify_token') as mock_verify_token, \
         patch('app.gateway_service.auth_service.verify_mfa') as mock_verify_mfa, \
         patch('app.gateway_service.auth_service.create_access_token') as mock_token:
        
        # Setup mocks
        mock_user = UserInfo(
            user_id="mfa_user_id",
            username="mfauser",
            email="mfa@example.com",
            roles=[UserRole.DEVELOPER],
            permissions=["read:all"],
            metadata={"mfa_enabled": True}
        )
        mock_verify_token.return_value = mock_user
        mock_verify_mfa.return_value = True
        
        mock_token.return_value = AuthToken(
            access_token="full_access_token",
            token_type=TokenType.BEARER,
            expires_in=1800,
            refresh_token="refresh_token"
        )
        
        # Make request
        response = client.post(
            "/api/v1/auth/mfa/verify",
            data={"code": "123456", "token": "partial_token"}
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "full_access_token"
        assert data["token_type"] == TokenType.BEARER
        assert data["expires_in"] == 1800
        assert data["refresh_token"] == "refresh_token"
        
        # Verify mocks were called correctly
        mock_verify_token.assert_called_once_with("partial_token")
        mock_verify_mfa.assert_called_once_with("mfa_user_id", "123456")
        mock_token.assert_called_once_with(mock_user)

def test_verify_mfa_invalid_code(client):
    """Test MFA verification with invalid code"""
    # Mock the verify_token and verify_mfa methods
    with patch('app.gateway_service.auth_service.verify_token') as mock_verify_token, \
         patch('app.gateway_service.auth_service.verify_mfa') as mock_verify_mfa:
        
        # Setup mocks
        mock_user = UserInfo(
            user_id="mfa_user_id",
            username="mfauser",
            email="mfa@example.com",
            roles=[UserRole.DEVELOPER],
            permissions=["read:all"],
            metadata={"mfa_enabled": True}
        )
        mock_verify_token.return_value = mock_user
        mock_verify_mfa.return_value = False  # Invalid MFA code
        
        # Make request
        response = client.post(
            "/api/v1/auth/mfa/verify",
            data={"code": "wrong", "token": "partial_token"}
        )
        
        # Check response
        assert response.status_code == 401
        data = response.json()
        assert "Invalid MFA code" in data["detail"]
        
        # Verify mocks were called correctly
        mock_verify_token.assert_called_once_with("partial_token")
        mock_verify_mfa.assert_called_once_with("mfa_user_id", "wrong")

def test_verify_mfa_invalid_token(client):
    """Test MFA verification with invalid token"""
    # Mock the verify_token method to raise an exception
    with patch('app.gateway_service.auth_service.verify_token') as mock_verify_token:
        mock_verify_token.side_effect = Exception("Invalid token")
        
        # Make request
        response = client.post(
            "/api/v1/auth/mfa/verify",
            data={"code": "123456", "token": "invalid_token"}
        )
        
        # Check response
        assert response.status_code == 401
        data = response.json()
        assert "Invalid token" in data["detail"]
        
        # Verify mock was called correctly
        mock_verify_token.assert_called_once_with("invalid_token")

# Test MFA setup endpoint
def test_setup_mfa(client):
    """Test setting up MFA"""
    # Mock the get_current_user and setup_mfa methods
    with patch('app.get_current_user') as mock_get_user, \
         patch('app.gateway_service.auth_service.setup_mfa') as mock_setup_mfa:
        
        # Setup mocks
        mock_user = UserInfo(
            user_id="test_user_id",
            username="testuser",
            email="test@example.com",
            roles=[UserRole.DEVELOPER],
            permissions=["read:all"],
            metadata={}
        )
        mock_get_user.return_value = mock_user
        
        mock_setup_mfa.return_value = {
            "secret": "ABCDEFGHIJKLMNOP",
            "provisioning_uri": "otpauth://totp/AI-CICD-Platform:testuser?secret=ABCDEFGHIJKLMNOP&issuer=AI-CICD-Platform"
        }
        
        # Make request
        response = client.post(
            "/api/v1/auth/mfa/setup",
            json={"method": MFAMethod.TOTP}
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["method"] == MFAMethod.TOTP
        assert "secret" in data["data"]
        assert "provisioning_uri" in data["data"]
        
        # Verify mocks were called correctly
        mock_get_user.assert_called_once()
        mock_setup_mfa.assert_called_once_with("test_user_id", MFAMethod.TOTP)

def test_setup_mfa_unauthenticated(client):
    """Test setting up MFA without authentication"""
    # Mock the get_current_user method to return None (unauthenticated)
    with patch('app.get_current_user', return_value=None):
        # Make request
        response = client.post(
            "/api/v1/auth/mfa/setup",
            json={"method": MFAMethod.TOTP}
        )
        
        # Check response
        assert response.status_code == 401
        data = response.json()
        assert "Authentication required" in data["detail"]

# Test refresh token endpoint
def test_refresh_token_success(client):
    """Test successful token refresh"""
    # Mock the refresh_access_token method
    with patch('app.gateway_service.auth_service.refresh_access_token') as mock_refresh:
        # Setup mock
        mock_refresh.return_value = AuthToken(
            access_token="new_access_token",
            token_type=TokenType.BEARER,
            expires_in=1800,
            refresh_token=None
        )
        
        # Make request
        response = client.post(
            "/api/v1/auth/refresh",
            data={"refresh_token": "valid_refresh_token"}
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "new_access_token"
        assert data["token_type"] == TokenType.BEARER
        assert data["expires_in"] == 1800
        
        # Verify mock was called correctly
        mock_refresh.assert_called_once_with("valid_refresh_token")

def test_refresh_token_invalid(client):
    """Test token refresh with invalid refresh token"""
    # Mock the refresh_access_token method to raise an exception
    with patch('app.gateway_service.auth_service.refresh_access_token') as mock_refresh:
        mock_refresh.side_effect = Exception("Invalid refresh token")
        
        # Make request
        response = client.post(
            "/api/v1/auth/refresh",
            data={"refresh_token": "invalid_refresh_token"}
        )
        
        # Check response
        assert response.status_code == 401
        data = response.json()
        assert "Invalid refresh token" in data["detail"]
        
        # Verify mock was called correctly
        mock_refresh.assert_called_once_with("invalid_refresh_token")

# Test logout endpoint
def test_logout(client):
    """Test logout (token revocation)"""
    # Mock the revoke_token method
    with patch('app.gateway_service.auth_service.revoke_token') as mock_revoke:
        # Make request
        response = client.post(
            "/api/v1/auth/logout",
            data={"token": "access_token_to_revoke"}
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Token revoked successfully" in data["message"]
        
        # Verify mock was called correctly
        mock_revoke.assert_called_once_with("access_token_to_revoke")
