from typing import Dict, Optional, Any, List, Union
import asyncio
from datetime import datetime, timedelta
import json
import hashlib
import aioredis
import aiocache
from aiocache.serializers import StringSerializer, PickleSerializer
from aiocache.backends.redis import RedisCache
import structlog
from fastapi import Request, Response
from starlette.datastructures import MutableHeaders

from ..config import get_settings, CACHE_CONFIGS
from ..models.gateway_models import (
    CacheEntry,
    ServiceResponse,
    UserInfo,
    UserRole
)

# Configure structured logging
logger = structlog.get_logger()

class CacheService:
    def __init__(self):
        self.settings = get_settings()
        self._redis = None
        self._cache = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
            "stored": 0
        }
        
        # Start background tasks
        self._init_task = asyncio.create_task(self._initialize())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _initialize(self):
        """Initialize Redis connection and cache"""
        try:
            # Connect to Redis
            self._redis = await aioredis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Initialize cache with Redis backend
            self._cache = aiocache.Cache(
                aiocache.Cache.REDIS,
                endpoint=self.settings.redis_url,
                namespace="api_gateway_cache",
                serializer=PickleSerializer(),
                pool_size=self.settings.redis_pool_size
            )
            
            logger.info("Cache service initialized with Redis backend")
        except Exception as e:
            logger.error("Failed to initialize Redis cache", error=str(e))
            # Fallback to in-memory cache
            self._cache = aiocache.Cache(
                aiocache.Cache.MEMORY,
                namespace="api_gateway_cache",
                serializer=PickleSerializer()
            )
            logger.warning("Using in-memory cache as fallback")

    async def get_cached_response(
        self,
        cache_key: str,
        cache_config: Optional[Dict] = None
    ) -> Optional[ServiceResponse]:
        """
        Get cached response if available
        """
        if not self.settings.cache_enabled or not self._cache:
            return None
        
        try:
            # Get from cache
            cached_data = await self._cache.get(cache_key)
            if not cached_data:
                self._stats["misses"] += 1
                return None
            
            self._stats["hits"] += 1
            return cached_data
        except Exception as e:
            logger.error("Cache get error", error=str(e), key=cache_key)
            return None

    async def cache_response(
        self,
        cache_key: str,
        response: ServiceResponse,
        ttl: Optional[int] = None,
        cache_config: Optional[Dict] = None
    ):
        """
        Cache response for future use
        """
        if not self.settings.cache_enabled or not self._cache:
            return
        
        try:
            # Use provided TTL or get from config
            config = cache_config or CACHE_CONFIGS.get("default")
            ttl = ttl or config["ttl"]
            
            # Store in cache
            await self._cache.set(cache_key, response, ttl=ttl)
            self._stats["stored"] += 1
            
            # Log cache operation
            logger.debug(
                "Response cached",
                key=cache_key,
                ttl=ttl,
                status_code=response.status_code
            )
        except Exception as e:
            logger.error("Cache set error", error=str(e), key=cache_key)

    async def invalidate_cache(
        self,
        pattern: str = "*",
        service: Optional[str] = None,
        endpoint: Optional[str] = None
    ):
        """
        Invalidate cache entries matching pattern
        """
        if not self.settings.cache_enabled or not self._redis:
            return 0
        
        try:
            # Build pattern
            if service and endpoint:
                pattern = f"api_gateway_cache:{service}:{endpoint}:*"
            elif service:
                pattern = f"api_gateway_cache:{service}:*"
            else:
                pattern = f"api_gateway_cache:{pattern}"
            
            # Find keys matching pattern
            keys = await self._redis.keys(pattern)
            
            # Delete keys
            if keys:
                count = await self._redis.delete(*keys)
                self._stats["invalidations"] += count
                
                # Log invalidation
                logger.info(
                    "Cache invalidated",
                    pattern=pattern,
                    keys_count=len(keys),
                    deleted_count=count
                )
                
                return count
            return 0
        except Exception as e:
            logger.error("Cache invalidation error", error=str(e), pattern=pattern)
            return 0

    def generate_cache_key(
        self,
        service: str,
        endpoint: str,
        method: str,
        params: Dict,
        user: Optional[UserInfo] = None,
        vary_by_user: bool = False,
        vary_by_role: bool = False
    ) -> str:
        """
        Generate cache key from request parameters with optional user variation
        """
        # Start with base components
        key_parts = [
            service,
            endpoint,
            method
        ]
        
        # Add user variation if requested
        if user and vary_by_user:
            key_parts.append(f"user:{user.user_id}")
        elif user and vary_by_role and user.roles:
            # Vary by highest role (assuming roles are ordered by privilege)
            key_parts.append(f"role:{user.roles[0].value}")
        
        # Add sorted query parameters
        if params:
            # Convert params to a stable string representation
            params_str = json.dumps(params, sort_keys=True)
            # Use a hash for potentially long parameter strings
            params_hash = hashlib.md5(params_str.encode()).hexdigest()
            key_parts.append(f"params:{params_hash}")
        
        # Join parts with colons
        return ":".join(key_parts)

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        """
        stats = dict(self._stats)
        
        # Add hit ratio
        total_requests = stats["hits"] + stats["misses"]
        stats["hit_ratio"] = stats["hits"] / total_requests if total_requests > 0 else 0
        
        # Add memory usage if using Redis
        if self._redis:
            try:
                info = await self._redis.info("memory")
                stats["memory_used"] = info.get("used_memory_human", "unknown")
                stats["memory_peak"] = info.get("used_memory_peak_human", "unknown")
            except:
                pass
        
        return stats

    async def apply_cache_headers(
        self,
        response: Response,
        cache_config: Optional[Dict] = None,
        is_cached: bool = False
    ):
        """
        Apply cache control headers to response
        """
        config = cache_config or CACHE_CONFIGS.get("default")
        ttl = config["ttl"]
        
        # Set cache control headers
        headers = MutableHeaders(response.headers)
        
        if is_cached:
            headers["X-Cache"] = "HIT"
        else:
            headers["X-Cache"] = "MISS"
        
        # Set Cache-Control header
        if ttl > 0:
            headers["Cache-Control"] = f"public, max-age={ttl}"
        else:
            headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        
        # Set Expires header
        if ttl > 0:
            expires = datetime.utcnow() + timedelta(seconds=ttl)
            headers["Expires"] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
        else:
            headers["Expires"] = "0"
        
        # Set Vary header if needed
        headers["Vary"] = "Accept-Encoding, Authorization"
        
        return response

    async def should_cache_response(
        self,
        request: Request,
        response: ServiceResponse,
        cache_config: Optional[Dict] = None
    ) -> bool:
        """
        Determine if a response should be cached
        """
        # Don't cache if disabled
        if not self.settings.cache_enabled:
            return False
        
        # Only cache GET requests
        if request.method != "GET":
            return False
        
        # Only cache successful responses
        if response.status_code >= 400:
            return False
        
        # Check response headers for cache control
        if "Cache-Control" in response.headers:
            cache_control = response.headers["Cache-Control"].lower()
            if "no-store" in cache_control or "no-cache" in cache_control:
                return False
        
        # Check response size
        config = cache_config or CACHE_CONFIGS.get("default")
        max_size = config.get("max_size", 1000)
        
        # Don't cache large responses
        response_size = len(json.dumps(response.body)) if isinstance(response.body, (dict, list)) else len(str(response.body))
        if response_size > max_size * 1024:  # Convert KB to bytes
            return False
        
        return True

    async def prefetch_cache(
        self,
        service: str,
        endpoint: str,
        params_list: List[Dict],
        ttl: Optional[int] = None
    ):
        """
        Prefetch and cache responses for common queries
        """
        if not self.settings.cache_enabled or not self._cache:
            return
        
        # This would be implemented to proactively cache common queries
        # For example, caching the most popular items, dashboard data, etc.
        # The implementation would depend on the specific use case
        pass

    async def _cleanup_loop(self):
        """
        Background task to clean up expired cache entries
        """
        while True:
            try:
                # Redis automatically handles TTL expiration
                # This is just for additional maintenance if needed
                
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error("Cache cleanup error", error=str(e))
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
