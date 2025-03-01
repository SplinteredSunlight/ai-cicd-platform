from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any
import jwt
import secrets
import pyotp
import uuid
import structlog
from fastapi import HTTPException, Security, Request, Depends
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from passlib.context import CryptContext
from ..config import get_settings, AuthProvider, RATE_LIMIT_CONFIGS
from ..models.gateway_models import AuthToken, UserInfo, UserRole, TokenType, MFAMethod, RateLimitState
from .token_service import TokenService
from .cache_service import CacheService

# Configure structured logging
logger = structlog.get_logger()

class AuthService:
    def __init__(self):
        self.settings = get_settings()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Initialize services
        self.token_service = TokenService()
        self.cache_service = CacheService()
        
        # OAuth2 configuration
        if self.settings.auth_provider == AuthProvider.OAUTH2:
            self.oauth2_scheme = OAuth2PasswordBearer(
                tokenUrl="token",
                scopes={
                    "read": "Read access",
                    "write": "Write access",
                    "admin": "Admin access"
                }
            )
        
        # API Key configuration
        self.api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
        
        # API keys (still in-memory for simplicity)
        self.api_keys: Dict[str, UserInfo] = {}
        
        # In-memory cache for MFA secrets
        # In production, use a secure database
        self.mfa_secrets: Dict[str, Dict[str, Any]] = {}  # user_id -> MFA data
        
        # In-memory rate limiting for auth endpoints
        # In production, use Redis or similar
        self.auth_attempts: Dict[str, RateLimitState] = {}  # ip or username -> rate limit state

    async def authenticate_user(
        self,
        username: str,
        password: str,
        request: Optional[Request] = None
    ) -> Optional[UserInfo]:
        """
        Authenticate user with username and password
        """
        # Check cache first
        if self.settings.cache_enabled:
            cache_key = f"auth:user:{username}"
            cached_auth_result = await self.cache_service.get_cached_response(cache_key)
            if cached_auth_result:
                # Only use cache for negative results (failed attempts)
                # For security, successful authentications should always be verified
                if not cached_auth_result.body.get("authenticated", False):
                    logger.info("Using cached authentication result", username=username, result="failed")
                    
                    # Record the attempt from cache
                    if request and self.settings.auth_rate_limit_enabled:
                        client_ip = request.client.host if request else "unknown"
                        username_key = f"username:{username}" if self.settings.auth_rate_limit_track_by_username else None
                        
                        # Record IP-based attempt
                        if self.settings.auth_rate_limit_track_by_ip:
                            self._record_auth_attempt(client_ip, success=False, limit_type="auth_login")
                        
                        # Record username-based attempt
                        if username_key and self.settings.auth_rate_limit_track_by_username:
                            self._record_auth_attempt(username_key, success=False, limit_type="auth_login")
                    
                    return None
        
        # Rate limiting for authentication attempts
        if request and self.settings.auth_rate_limit_enabled:
            client_ip = request.client.host if request else "unknown"
            username_key = f"username:{username}" if self.settings.auth_rate_limit_track_by_username else None
            
            # Check IP-based rate limit
            if self.settings.auth_rate_limit_track_by_ip:
                is_allowed, retry_after = await self._check_rate_limit_for_action(client_ip, "login")
                if not is_allowed:
                    # Check if locked out
                    state = self.auth_attempts.get(client_ip)
                    if state and state.is_locked_out:
                        lockout_minutes = int((state.lockout_until - datetime.utcnow()).total_seconds() / 60)
                        raise HTTPException(
                            status_code=429,
                            detail=f"Too many failed authentication attempts. Your account has been temporarily locked. Please try again in {lockout_minutes} minutes.",
                            headers={"Retry-After": str(retry_after)}
                        )
                    else:
                        raise HTTPException(
                            status_code=429,
                            detail="Rate limit exceeded. Please try again later.",
                            headers={"Retry-After": str(retry_after)}
                        )
            
            # Check username-based rate limit if enabled
            if username_key and self.settings.auth_rate_limit_track_by_username:
                is_allowed, retry_after = await self._check_rate_limit_for_action(username_key, "login")
                if not is_allowed:
                    # Check if locked out
                    state = self.auth_attempts.get(username_key)
                    if state and state.is_locked_out:
                        lockout_minutes = int((state.lockout_until - datetime.utcnow()).total_seconds() / 60)
                        raise HTTPException(
                            status_code=429,
                            detail=f"Too many failed authentication attempts for this username. Your account has been temporarily locked. Please try again in {lockout_minutes} minutes.",
                            headers={"Retry-After": str(retry_after)}
                        )
                    else:
                        raise HTTPException(
                            status_code=429,
                            detail="Rate limit exceeded for this username. Please try again later.",
                            headers={"Retry-After": str(retry_after)}
                        )
        
        # TODO: Implement user lookup from database
        # This is a mock implementation
        authenticated = username == "admin" and self.verify_password(password, "hashed_admin_pwd")
        
        if authenticated:
            user = UserInfo(
                user_id="admin_id",
                username="admin",
                email="admin@example.com",
                roles=[UserRole.ADMIN],
                permissions=["*"],
                metadata={
                    "mfa_enabled": True,
                    "mfa_methods": [MFAMethod.TOTP]
                }
            )
            
            # Record successful authentication
            if request and self.settings.auth_rate_limit_enabled:
                client_ip = request.client.host if request else "unknown"
                username_key = f"username:{username}" if self.settings.auth_rate_limit_track_by_username else None
                
                # Record IP-based attempt
                if self.settings.auth_rate_limit_track_by_ip:
                    self._record_auth_attempt(client_ip, success=True, limit_type="auth_login")
                
                # Record username-based attempt
                if username_key and self.settings.auth_rate_limit_track_by_username:
                    self._record_auth_attempt(username_key, success=True, limit_type="auth_login")
            
            return user
        else:
            # Record failed authentication
            if request and self.settings.auth_rate_limit_enabled:
                client_ip = request.client.host if request else "unknown"
                username_key = f"username:{username}" if self.settings.auth_rate_limit_track_by_username else None
                
                # Record IP-based attempt
                if self.settings.auth_rate_limit_track_by_ip:
                    self._record_auth_attempt(client_ip, success=False, limit_type="auth_login")
                
                # Record username-based attempt
                if username_key and self.settings.auth_rate_limit_track_by_username:
                    self._record_auth_attempt(username_key, success=False, limit_type="auth_login")
            
            # Cache failed authentication attempts to prevent brute force attacks
            if self.settings.cache_enabled:
                cache_key = f"auth:user:{username}"
                from ..models.gateway_models import ServiceResponse
                cache_data = ServiceResponse(
                    status_code=401,
                    headers={},
                    body={"authenticated": False, "username": username},
                    duration_ms=0,
                    cached=False
                )
                # Cache failed attempts for a short time (30 seconds)
                await self.cache_service.cache_response(cache_key, cache_data, ttl=30)
            
            return None

    async def create_access_token(
        self,
        user: UserInfo,
        expires_delta: Optional[timedelta] = None,
        include_refresh_token: bool = True,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> AuthToken:
        """
        Create JWT access token
        """
        # Delegate to token service
        return await self.token_service.create_access_token(
            user=user,
            expires_delta=expires_delta,
            include_refresh_token=include_refresh_token,
            additional_claims=additional_claims
        )

    async def verify_token(self, token: str, token_type: str = "access") -> Optional[UserInfo]:
        """
        Verify JWT token and return user info
        """
        # Delegate to token service
        return await self.token_service.verify_token(token, token_type)

    async def refresh_access_token(self, refresh_token: str, request: Optional[Request] = None) -> AuthToken:
        """
        Create a new access token using a refresh token
        """
        # Apply rate limiting for token refresh
        if request and self.settings.auth_rate_limit_enabled:
            client_ip = request.client.host if request else "unknown"
            
            # Check IP-based rate limit
            if self.settings.auth_rate_limit_track_by_ip:
                is_allowed, retry_after = await self._check_rate_limit_for_action(client_ip, "refresh")
                if not is_allowed:
                    # Check if locked out
                    state = self.auth_attempts.get(client_ip)
                    if state and state.is_locked_out:
                        lockout_minutes = int((state.lockout_until - datetime.utcnow()).total_seconds() / 60)
                        raise HTTPException(
                            status_code=429,
                            detail=f"Too many token refresh attempts. Please try again in {lockout_minutes} minutes.",
                            headers={"Retry-After": str(retry_after)}
                        )
                    else:
                        raise HTTPException(
                            status_code=429,
                            detail="Rate limit exceeded for token refresh. Please try again later.",
                            headers={"Retry-After": str(retry_after)}
                        )
        
        try:
            # Delegate to token service
            return await self.token_service.refresh_access_token(refresh_token, request)
        except HTTPException as e:
            # Record failed refresh attempt
            if request and self.settings.auth_rate_limit_enabled and self.settings.auth_rate_limit_track_by_ip:
                client_ip = request.client.host if request else "unknown"
                self._record_auth_attempt(client_ip, success=False, limit_type="auth_refresh")
            raise e

    async def verify_api_key(self, api_key: str) -> Optional[UserInfo]:
        """
        Verify API key and return user info
        """
        # Check cache first
        if self.settings.cache_enabled:
            cache_key = f"auth:api_key:{api_key}"
            cached_result = await self.cache_service.get_cached_response(cache_key)
            if cached_result:
                # For API keys, we can safely cache both positive and negative results
                # since they don't change frequently
                if cached_result.body.get("valid", False):
                    return UserInfo(**cached_result.body.get("user", {}))
                return None
        
        # Check API key
        user = self.api_keys.get(api_key)
        
        # Cache result
        if self.settings.cache_enabled:
            cache_key = f"auth:api_key:{api_key}"
            from ..models.gateway_models import ServiceResponse
            cache_data = ServiceResponse(
                status_code=200 if user else 401,
                headers={},
                body={
                    "valid": user is not None,
                    "user": user.dict() if user else None
                },
                duration_ms=0,
                cached=False
            )
            # Cache API key results for longer (5 minutes)
            await self.cache_service.cache_response(cache_key, cache_data, ttl=300)
        
        return user

    async def revoke_token(self, token: str):
        """
        Revoke a JWT token
        """
        # Delegate to token service
        await self.token_service.revoke_token(token)

    async def revoke_all_user_tokens(self, user_id: str):
        """
        Revoke all tokens for a specific user
        """
        # Delegate to token service
        await self.token_service.revoke_all_user_tokens(user_id)

    async def create_api_key(self, user: UserInfo) -> str:
        """
        Create API key for a user
        """
        api_key = f"ak_{secrets.token_urlsafe(32)}"
        self.api_keys[api_key] = user
        
        # Invalidate cache for this user's API keys
        if self.settings.cache_enabled:
            await self.cache_service.invalidate_cache(pattern=f"auth:api_key:*")
        
        return api_key

    async def revoke_api_key(self, api_key: str):
        """
        Revoke an API key
        """
        if api_key in self.api_keys:
            del self.api_keys[api_key]
            
            # Invalidate cache for this API key
            if self.settings.cache_enabled:
                cache_key = f"auth:api_key:{api_key}"
                await self.cache_service.invalidate_cache(pattern=cache_key)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Hash password
        """
        return self.pwd_context.hash(password)

    async def check_permissions(
        self,
        user: UserInfo,
        required_roles: List[UserRole],
        required_permissions: List[str]
    ) -> bool:
        """
        Check if user has required roles and permissions
        """
        # Admin role has all permissions
        if UserRole.ADMIN in user.roles:
            return True
        
        # Check roles
        if required_roles and not any(role in user.roles for role in required_roles):
            return False
        
        # Check permissions
        if required_permissions:
            user_permissions = set(user.permissions)
            if "*" not in user_permissions:  # Wildcard permission
                required = set(required_permissions)
                if not required.issubset(user_permissions):
                    return False
        
        return True

    # Multi-factor authentication methods
    
    async def setup_mfa(self, user_id: str, method: MFAMethod) -> Dict[str, Any]:
        """
        Set up multi-factor authentication for a user
        """
        if method == MFAMethod.TOTP:
            # Generate TOTP secret
            totp_secret = pyotp.random_base32()
            totp = pyotp.TOTP(totp_secret)
            
            # Store MFA data
            self.mfa_secrets[user_id] = {
                "method": method.value,
                "secret": totp_secret,
                "verified": False
            }
            
            # Generate provisioning URI for QR code
            # In a real app, you'd use the actual app name and user's email
            provisioning_uri = totp.provisioning_uri(
                name=f"user:{user_id}",
                issuer_name="AI-CICD-Platform"
            )
            
            return {
                "secret": totp_secret,
                "provisioning_uri": provisioning_uri
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported MFA method: {method}"
            )
    
    async def verify_mfa(self, user_id: str, code: str, request: Optional[Request] = None) -> bool:
        """
        Verify MFA code
        """
        # Apply rate limiting for MFA verification
        if request and self.settings.auth_rate_limit_enabled:
            client_ip = request.client.host if request else "unknown"
            user_key = f"user:{user_id}" if user_id else "unknown"
            
            # Check IP-based rate limit
            if self.settings.auth_rate_limit_track_by_ip:
                is_allowed, _ = await self._check_rate_limit_for_action(client_ip, "mfa")
                if not is_allowed:
                    # We don't raise an exception here to avoid revealing if the user exists
                    # Just return False as if the code was invalid
                    return False
            
            # Check user-based rate limit
            is_allowed, _ = await self._check_rate_limit_for_action(user_key, "mfa")
            if not is_allowed:
                # We don't raise an exception here to avoid revealing if the user exists
                # Just return False as if the code was invalid
                return False
        
        if user_id not in self.mfa_secrets:
            return False
        
        mfa_data = self.mfa_secrets[user_id]
        
        if mfa_data["method"] == MFAMethod.TOTP.value:
            totp = pyotp.TOTP(mfa_data["secret"])
            is_valid = totp.verify(code)
            
            # Record the verification attempt
            if request and self.settings.auth_rate_limit_enabled:
                client_ip = request.client.host if request else "unknown"
                user_key = f"user:{user_id}"
                
                # Record IP-based attempt
                if self.settings.auth_rate_limit_track_by_ip:
                    self._record_auth_attempt(client_ip, success=is_valid, limit_type="auth_mfa")
                
                # Record user-based attempt
                self._record_auth_attempt(user_key, success=is_valid, limit_type="auth_mfa")
            
            # Mark as verified if this is the first successful verification
            if is_valid and not mfa_data["verified"]:
                mfa_data["verified"] = True
                self.mfa_secrets[user_id] = mfa_data
            
            return is_valid
        
        return False
    
    async def disable_mfa(self, user_id: str) -> bool:
        """
        Disable MFA for a user
        """
        if user_id in self.mfa_secrets:
            del self.mfa_secrets[user_id]
            return True
        return False
    
    async def is_mfa_enabled(self, user_id: str) -> bool:
        """
        Check if MFA is enabled for a user
        """
        return user_id in self.mfa_secrets and self.mfa_secrets[user_id]["verified"]
    
    # Helper methods
    
    def _create_refresh_token(self, user_id: str) -> str:
        """
        Create a refresh token for a user
        """
        refresh_token = f"rt_{secrets.token_urlsafe(64)}"
        self.refresh_tokens[user_id] = refresh_token
        return refresh_token
    
    async def _check_auth_rate_limit(self, key: str, limit_type: str = "auth_login") -> bool:
        """
        Check if authentication rate limit is exceeded
        Returns True if request is allowed, False if rate limited
        """
        now = datetime.utcnow()
        config = RATE_LIMIT_CONFIGS.get(limit_type, RATE_LIMIT_CONFIGS["auth"])
        
        # Initialize if not exists
        if key not in self.auth_attempts:
            self.auth_attempts[key] = RateLimitState(
                key=key,
                window_start=now,
                request_count=0,
                window_size=config["window"],
                limit=config["requests"],
                failed_count=0,
                successful_count=0,
                consecutive_failures=0,
                last_attempt_time=None,
                lockout_until=None
            )
        
        state = self.auth_attempts[key]
        
        # Check if locked out
        if state.is_locked_out:
            return False
        
        # Check if window expired, reset if needed
        window_end = state.window_start + timedelta(seconds=state.window_size)
        if now > window_end:
            # Keep track of consecutive failures across windows
            consecutive_failures = state.consecutive_failures
            
            # Reset state for new window
            state.window_start = now
            state.request_count = 0
            state.failed_count = 0
            state.successful_count = 0
            
            # Maintain consecutive failures
            state.consecutive_failures = consecutive_failures
        
        # Check if limit exceeded
        if state.is_exceeded:
            # Apply lockout if threshold reached
            if "lockout_threshold" in config and state.failed_count >= config["lockout_threshold"]:
                lockout_minutes = config["lockout_duration"]
                
                # Apply progressive lockout if enabled
                if self.settings.auth_rate_limit_progressive_lockout:
                    # Increase lockout duration based on consecutive failures
                    lockout_minutes = min(lockout_minutes * (state.consecutive_failures + 1), 
                                         self.settings.auth_rate_limit_lockout_duration * 4)
                
                state.lockout_until = now + timedelta(minutes=lockout_minutes)
            
            return False
        
        # Increment request count
        state.request_count += 1
        return True
    
    def _record_auth_attempt(self, key: str, success: bool, limit_type: str = "auth_login"):
        """
        Record an authentication attempt
        """
        now = datetime.utcnow()
        config = RATE_LIMIT_CONFIGS.get(limit_type, RATE_LIMIT_CONFIGS["auth"])
        
        # Initialize if not exists
        if key not in self.auth_attempts:
            self.auth_attempts[key] = RateLimitState(
                key=key,
                window_start=now,
                request_count=1,  # Count this attempt
                window_size=config["window"],
                limit=config["requests"],
                failed_count=0,
                successful_count=0,
                consecutive_failures=0,
                last_attempt_time=now,
                lockout_until=None
            )
        
        state = self.auth_attempts[key]
        state.last_attempt_time = now
        
        if success:
            state.successful_count += 1
            state.consecutive_failures = 0  # Reset consecutive failures on success
        else:
            state.failed_count += 1
            state.consecutive_failures += 1
            
            # Apply lockout if threshold reached
            if "lockout_threshold" in config and state.failed_count >= config["lockout_threshold"]:
                lockout_minutes = config["lockout_duration"]
                
                # Apply progressive lockout if enabled
                if self.settings.auth_rate_limit_progressive_lockout:
                    # Increase lockout duration based on consecutive failures
                    lockout_minutes = min(lockout_minutes * state.consecutive_failures, 
                                         self.settings.auth_rate_limit_lockout_duration * 4)
                
                state.lockout_until = now + timedelta(minutes=lockout_minutes)
    
    async def _check_rate_limit_for_action(self, key: str, action_type: str) -> Tuple[bool, Optional[int]]:
        """
        Check rate limit for a specific authentication action
        Returns (is_allowed, retry_after_seconds)
        """
        # Map action types to rate limit configs
        limit_type = {
            "login": "auth_login",
            "mfa": "auth_mfa",
            "refresh": "auth_refresh"
        }.get(action_type, "auth")
        
        # Check rate limit
        is_allowed = await self._check_auth_rate_limit(key, limit_type)
        
        if not is_allowed:
            state = self.auth_attempts.get(key)
            if state and state.is_locked_out and state.lockout_until:
                # Calculate retry after in seconds
                retry_after = int((state.lockout_until - datetime.utcnow()).total_seconds())
                return False, retry_after
            
            # Default retry after (window size)
            config = RATE_LIMIT_CONFIGS.get(limit_type, RATE_LIMIT_CONFIGS["auth"])
            return False, config["window"]
        
        return True, None
    
    async def cleanup(self):
        """
        Cleanup resources
        """
        # Clear expired tokens from revoked tokens set
        current_time = datetime.utcnow()
        
        # Clean up revoked tokens
        try:
            self.revoked_tokens = {
                token for token in self.revoked_tokens
                if datetime.fromtimestamp(
                    jwt.decode(
                        token,
                        self.settings.jwt_secret_key,
                        algorithms=[self.settings.jwt_algorithm],
                        options={"verify_signature": True, "verify_exp": False}
                    )["exp"]
                ) > current_time
            }
        except Exception:
            # If there's an error decoding tokens, just keep them in the set
            pass
        
        # Clean up auth attempts
        for key in list(self.auth_attempts.keys()):
            state = self.auth_attempts[key]
            
            # Check if window has expired and no lockout is active
            window_end = state.window_start + timedelta(seconds=state.window_size)
            if current_time > window_end and (not state.lockout_until or current_time > state.lockout_until):
                # If no activity in the last window and no consecutive failures, remove the state
                if state.request_count == 0 and state.consecutive_failures == 0:
                    del self.auth_attempts[key]
                else:
                    # Reset window but keep consecutive failures
                    consecutive_failures = state.consecutive_failures
                    state.window_start = current_time
                    state.request_count = 0
                    state.failed_count = 0
                    state.successful_count = 0
                    state.consecutive_failures = consecutive_failures
