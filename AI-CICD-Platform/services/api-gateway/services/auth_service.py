from datetime import datetime, timedelta
from typing import Optional, Dict, List
import jwt
from fastapi import HTTPException, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from passlib.context import CryptContext
from ..config import get_settings, AuthProvider
from ..models.gateway_models import AuthToken, UserInfo, UserRole, TokenType

class AuthService:
    def __init__(self):
        self.settings = get_settings()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
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
        
        # In-memory cache for revoked tokens and API keys
        # In production, use Redis or similar
        self.revoked_tokens = set()
        self.api_keys: Dict[str, UserInfo] = {}

    async def authenticate_user(
        self,
        username: str,
        password: str
    ) -> Optional[UserInfo]:
        """
        Authenticate user with username and password
        """
        # TODO: Implement user lookup from database
        # This is a mock implementation
        if username == "admin" and self.verify_password(password, "hashed_admin_pwd"):
            return UserInfo(
                user_id="admin_id",
                username="admin",
                email="admin@example.com",
                roles=[UserRole.ADMIN],
                permissions=["*"]
            )
        return None

    async def create_access_token(
        self,
        user: UserInfo,
        expires_delta: Optional[timedelta] = None
    ) -> AuthToken:
        """
        Create JWT access token
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=self.settings.jwt_expiration_minutes)
        
        expires_at = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": user.user_id,
            "exp": expires_at,
            "roles": [role.value for role in user.roles],
            "permissions": user.permissions
        }
        
        token = jwt.encode(
            to_encode,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm
        )
        
        return AuthToken(
            access_token=token,
            token_type=TokenType.BEARER,
            expires_in=int(expires_delta.total_seconds())
        )

    async def verify_token(self, token: str) -> Optional[UserInfo]:
        """
        Verify JWT token and return user info
        """
        try:
            if token in self.revoked_tokens:
                raise HTTPException(
                    status_code=401,
                    detail="Token has been revoked"
                )
            
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm]
            )
            
            if datetime.fromtimestamp(payload["exp"]) < datetime.utcnow():
                raise HTTPException(
                    status_code=401,
                    detail="Token has expired"
                )
            
            return UserInfo(
                user_id=payload["sub"],
                username=payload.get("username", ""),
                email=payload.get("email", ""),
                roles=[UserRole(role) for role in payload["roles"]],
                permissions=payload["permissions"]
            )
            
        except jwt.JWTError:
            raise HTTPException(
                status_code=401,
                detail="Could not validate token"
            )

    async def verify_api_key(self, api_key: str) -> Optional[UserInfo]:
        """
        Verify API key and return user info
        """
        return self.api_keys.get(api_key)

    async def revoke_token(self, token: str):
        """
        Revoke a JWT token
        """
        self.revoked_tokens.add(token)

    async def create_api_key(self, user: UserInfo) -> str:
        """
        Create API key for a user
        """
        import secrets
        api_key = f"ak_{secrets.token_urlsafe(32)}"
        self.api_keys[api_key] = user
        return api_key

    async def revoke_api_key(self, api_key: str):
        """
        Revoke an API key
        """
        if api_key in self.api_keys:
            del self.api_keys[api_key]

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

    async def cleanup(self):
        """
        Cleanup resources
        """
        # Clear expired tokens from revoked tokens set
        current_time = datetime.utcnow()
        self.revoked_tokens = {
            token for token in self.revoked_tokens
            if datetime.fromtimestamp(
                jwt.decode(
                    token,
                    self.settings.jwt_secret_key,
                    algorithms=[self.settings.jwt_algorithm]
                )["exp"]
            ) > current_time
        }
