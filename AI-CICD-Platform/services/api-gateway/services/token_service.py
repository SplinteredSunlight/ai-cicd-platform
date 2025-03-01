from typing import Dict, Optional, Any, List, Tuple
import asyncio
from datetime import datetime, timedelta
import json
import uuid
import jwt
import secrets
import aioredis
import structlog
from fastapi import HTTPException, Request

from ..config import get_settings
from ..models.gateway_models import (
    UserInfo,
    AuthToken,
    TokenType
)

# Configure structured logging
logger = structlog.get_logger()

class TokenService:
    def __init__(self):
        self.settings = get_settings()
        self._redis = None
        
        # Prefixes for Redis keys
        self.BLACKLIST_PREFIX = "token:blacklist:"
        self.REFRESH_PREFIX = "token:refresh:"
        self.USER_TOKENS_PREFIX = "user:tokens:"
        
        # Start background tasks
        self._init_task = asyncio.create_task(self._initialize())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _initialize(self):
        """Initialize Redis connection"""
        try:
            # Connect to Redis
            self._redis = await aioredis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            logger.info("Token service initialized with Redis backend")
        except Exception as e:
            logger.error("Failed to initialize Redis for token service", error=str(e))
            # Fallback to in-memory storage
            self._blacklist = set()
            self._refresh_tokens = {}
            self._user_tokens = {}
            logger.warning("Using in-memory storage for tokens as fallback")

    async def create_access_token(
        self,
        user: UserInfo,
        expires_delta: Optional[timedelta] = None,
        include_refresh_token: bool = True,
        token_type: str = "access",
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> AuthToken:
        """
        Create JWT access token with optional refresh token
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=self.settings.jwt_expiration_minutes)
        
        expires_at = datetime.utcnow() + expires_delta
        token_id = str(uuid.uuid4())
        
        # Base claims
        to_encode = {
            "sub": user.user_id,
            "exp": expires_at,
            "iat": datetime.utcnow(),
            "jti": token_id,
            "type": token_type,
            "roles": [role.value for role in user.roles],
            "permissions": user.permissions,
            "username": user.username,
            "email": user.email
        }
        
        # Add additional claims if provided
        if additional_claims:
            to_encode.update(additional_claims)
        
        # Encode token
        token = jwt.encode(
            to_encode,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm
        )
        
        # Store token in Redis for the user
        if self._redis:
            user_tokens_key = f"{self.USER_TOKENS_PREFIX}{user.user_id}"
            token_data = {
                "jti": token_id,
                "exp": expires_at.timestamp(),
                "type": token_type
            }
            await self._redis.hset(user_tokens_key, token_id, json.dumps(token_data))
            # Set expiration for the hash entry
            await self._redis.expire(user_tokens_key, int(expires_delta.total_seconds() * 1.1))
        
        # Create refresh token if requested
        refresh_token = None
        if include_refresh_token:
            refresh_token = await self._create_refresh_token(user.user_id, token_id)
        
        return AuthToken(
            access_token=token,
            token_type=TokenType.BEARER,
            expires_in=int(expires_delta.total_seconds()),
            refresh_token=refresh_token
        )

    async def verify_token(
        self,
        token: str,
        token_type: str = "access"
    ) -> Optional[UserInfo]:
        """
        Verify JWT token and return user info
        """
        try:
            # Decode token without verification first to get the token ID
            unverified_payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            
            token_id = unverified_payload.get("jti")
            if not token_id:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token format"
                )
            
            # Check if token is blacklisted
            is_blacklisted = await self._is_token_blacklisted(token_id)
            if is_blacklisted:
                raise HTTPException(
                    status_code=401,
                    detail="Token has been revoked"
                )
            
            # Verify token signature and claims
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
                options={"verify_signature": True, "verify_exp": True, "verify_iat": True}
            )
            
            # Verify token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=401,
                    detail=f"Invalid token type. Expected {token_type}"
                )
            
            # Extract user info from token
            user_info = UserInfo(
                user_id=payload["sub"],
                username=payload.get("username", ""),
                email=payload.get("email", ""),
                roles=[role for role in payload["roles"]],
                permissions=payload["permissions"],
                metadata=payload.get("metadata", {})
            )
            
            return user_info
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=401,
                detail="Could not validate token"
            )

    async def refresh_access_token(
        self,
        refresh_token: str,
        request: Optional[Request] = None
    ) -> AuthToken:
        """
        Create a new access token using a refresh token
        """
        try:
            # Decode refresh token to get user_id and parent token ID
            payload = jwt.decode(
                refresh_token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
                options={"verify_signature": True, "verify_exp": True}
            )
            
            # Verify token type
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token type"
                )
            
            user_id = payload.get("sub")
            parent_token_id = payload.get("parent_jti")
            token_id = payload.get("jti")
            
            if not user_id or not parent_token_id or not token_id:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid refresh token format"
                )
            
            # Check if refresh token is valid in Redis
            is_valid = await self._validate_refresh_token(user_id, token_id, parent_token_id)
            if not is_valid:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or expired refresh token"
                )
            
            # Get user info
            # In a real implementation, fetch from database
            # This is a mock implementation
            if user_id == "admin_id":
                user = UserInfo(
                    user_id="admin_id",
                    username="admin",
                    email="admin@example.com",
                    roles=["admin"],
                    permissions=["*"]
                )
            else:
                # Mock user for testing
                user = UserInfo(
                    user_id=user_id,
                    username=f"user_{user_id}",
                    email=f"user_{user_id}@example.com",
                    roles=["user"],
                    permissions=["read:own"]
                )
            
            # Revoke the old refresh token
            await self._invalidate_refresh_token(user_id, token_id)
            
            # Create new access token with new refresh token
            # Use token rotation for enhanced security
            return await self.create_access_token(user)
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Refresh token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=401,
                detail="Could not validate refresh token"
            )

    async def revoke_token(self, token: str):
        """
        Revoke a JWT token by adding it to the blacklist
        """
        try:
            # Decode token to get jti and expiration
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
                options={"verify_signature": True, "verify_exp": False}
            )
            
            token_id = payload.get("jti")
            user_id = payload.get("sub")
            exp = payload.get("exp")
            
            if not token_id or not user_id or not exp:
                logger.warning("Invalid token format for revocation")
                return
            
            # Calculate TTL (time until token expires)
            now = datetime.utcnow()
            token_exp = datetime.fromtimestamp(exp)
            ttl = max(0, int((token_exp - now).total_seconds()))
            
            # Add to blacklist with expiration
            await self._blacklist_token(token_id, ttl)
            
            # If it's an access token, also revoke its refresh token
            if payload.get("type") == "access":
                await self._revoke_refresh_tokens_for_access_token(user_id, token_id)
            
            logger.info("Token revoked", token_id=token_id, user_id=user_id)
            
        except Exception as e:
            logger.error("Token revocation failed", error=str(e))

    async def revoke_all_user_tokens(self, user_id: str):
        """
        Revoke all tokens for a specific user
        """
        try:
            if self._redis:
                # Get all tokens for the user
                user_tokens_key = f"{self.USER_TOKENS_PREFIX}{user_id}"
                tokens = await self._redis.hgetall(user_tokens_key)
                
                # Blacklist each token
                for token_id, token_data_json in tokens.items():
                    token_data = json.loads(token_data_json)
                    exp = token_data.get("exp")
                    
                    if exp:
                        # Calculate TTL
                        now = datetime.utcnow()
                        token_exp = datetime.fromtimestamp(exp)
                        ttl = max(0, int((token_exp - now).total_seconds()))
                        
                        # Add to blacklist
                        await self._blacklist_token(token_id, ttl)
                
                # Remove all refresh tokens for the user
                refresh_pattern = f"{self.REFRESH_PREFIX}{user_id}:*"
                refresh_keys = await self._redis.keys(refresh_pattern)
                if refresh_keys:
                    await self._redis.delete(*refresh_keys)
                
                # Clear the user's token hash
                await self._redis.delete(user_tokens_key)
                
                logger.info("All tokens revoked for user", user_id=user_id)
            else:
                # In-memory fallback
                # This is less efficient but works for testing
                tokens_to_remove = []
                for token_id in self._user_tokens.get(user_id, {}):
                    self._blacklist.add(token_id)
                    tokens_to_remove.append(token_id)
                
                for token_id in tokens_to_remove:
                    self._user_tokens[user_id].pop(token_id, None)
                
                # Remove refresh tokens
                refresh_to_remove = []
                for key in self._refresh_tokens:
                    if key.startswith(f"{user_id}:"):
                        refresh_to_remove.append(key)
                
                for key in refresh_to_remove:
                    self._refresh_tokens.pop(key, None)
        
        except Exception as e:
            logger.error("Failed to revoke all user tokens", error=str(e), user_id=user_id)

    async def _create_refresh_token(
        self,
        user_id: str,
        access_token_id: str
    ) -> str:
        """
        Create a refresh token for a user
        """
        # Create a unique ID for the refresh token
        refresh_token_id = str(uuid.uuid4())
        
        # Set expiration time
        expires_delta = timedelta(days=self.settings.jwt_refresh_expiration_days)
        expires_at = datetime.utcnow() + expires_delta
        
        # Create token payload
        to_encode = {
            "sub": user_id,
            "exp": expires_at,
            "iat": datetime.utcnow(),
            "jti": refresh_token_id,
            "type": "refresh",
            "parent_jti": access_token_id
        }
        
        # Encode token
        refresh_token = jwt.encode(
            to_encode,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm
        )
        
        # Store in Redis
        if self._redis:
            # Store mapping between refresh token and access token
            refresh_key = f"{self.REFRESH_PREFIX}{user_id}:{refresh_token_id}"
            refresh_data = {
                "access_token_id": access_token_id,
                "exp": expires_at.timestamp()
            }
            await self._redis.set(
                refresh_key,
                json.dumps(refresh_data),
                ex=int(expires_delta.total_seconds())
            )
        else:
            # In-memory fallback
            key = f"{user_id}:{refresh_token_id}"
            self._refresh_tokens[key] = {
                "access_token_id": access_token_id,
                "exp": expires_at.timestamp()
            }
        
        return refresh_token

    async def _blacklist_token(self, token_id: str, ttl: int):
        """
        Add a token to the blacklist with expiration
        """
        if self._redis:
            blacklist_key = f"{self.BLACKLIST_PREFIX}{token_id}"
            await self._redis.set(blacklist_key, "1", ex=ttl)
        else:
            # In-memory fallback
            self._blacklist.add(token_id)
            # We can't easily implement TTL for in-memory blacklist
            # In a real implementation, you'd use a proper data structure with expiration

    async def _is_token_blacklisted(self, token_id: str) -> bool:
        """
        Check if a token is blacklisted
        """
        if self._redis:
            blacklist_key = f"{self.BLACKLIST_PREFIX}{token_id}"
            return await self._redis.exists(blacklist_key) == 1
        else:
            # In-memory fallback
            return token_id in self._blacklist

    async def _validate_refresh_token(
        self,
        user_id: str,
        refresh_token_id: str,
        access_token_id: str
    ) -> bool:
        """
        Validate that a refresh token exists and matches the access token
        """
        if self._redis:
            refresh_key = f"{self.REFRESH_PREFIX}{user_id}:{refresh_token_id}"
            data = await self._redis.get(refresh_key)
            
            if not data:
                return False
            
            refresh_data = json.loads(data)
            return refresh_data.get("access_token_id") == access_token_id
        else:
            # In-memory fallback
            key = f"{user_id}:{refresh_token_id}"
            data = self._refresh_tokens.get(key)
            
            if not data:
                return False
            
            return data.get("access_token_id") == access_token_id

    async def _invalidate_refresh_token(self, user_id: str, refresh_token_id: str):
        """
        Invalidate a refresh token
        """
        if self._redis:
            refresh_key = f"{self.REFRESH_PREFIX}{user_id}:{refresh_token_id}"
            await self._redis.delete(refresh_key)
        else:
            # In-memory fallback
            key = f"{user_id}:{refresh_token_id}"
            if key in self._refresh_tokens:
                del self._refresh_tokens[key]

    async def _revoke_refresh_tokens_for_access_token(self, user_id: str, access_token_id: str):
        """
        Revoke all refresh tokens associated with an access token
        """
        if self._redis:
            # Get all refresh tokens for the user
            refresh_pattern = f"{self.REFRESH_PREFIX}{user_id}:*"
            refresh_keys = await self._redis.keys(refresh_pattern)
            
            for key in refresh_keys:
                data = await self._redis.get(key)
                if data:
                    refresh_data = json.loads(data)
                    if refresh_data.get("access_token_id") == access_token_id:
                        await self._redis.delete(key)
        else:
            # In-memory fallback
            keys_to_delete = []
            for key, data in self._refresh_tokens.items():
                if key.startswith(f"{user_id}:") and data.get("access_token_id") == access_token_id:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self._refresh_tokens[key]

    async def _cleanup_loop(self):
        """
        Background task to clean up expired tokens
        """
        while True:
            try:
                # Redis automatically handles TTL expiration
                # This is just for additional maintenance if needed
                
                # For in-memory fallback, we would clean up expired tokens here
                if not self._redis:
                    now = datetime.utcnow().timestamp()
                    
                    # Clean up expired refresh tokens
                    expired_keys = []
                    for key, data in self._refresh_tokens.items():
                        if data.get("exp", 0) < now:
                            expired_keys.append(key)
                    
                    for key in expired_keys:
                        del self._refresh_tokens[key]
                
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error("Token cleanup error", error=str(e))
                await asyncio.sleep(3600)

    async def cleanup(self):
        """
        Cleanup resources
        """
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self._init_task:
            self._init_task.cancel()
            try:
                await self._init_task
            except asyncio.CancelledError:
                pass
        
        if self._redis:
            await self._redis.close()
