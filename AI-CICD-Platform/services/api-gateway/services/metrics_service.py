from typing import Dict, Optional, List
import asyncio
from datetime import datetime, timedelta
import json
from prometheus_client import Counter, Histogram, Gauge
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import structlog

from ..config import get_settings, CACHE_CONFIGS
from ..models.gateway_models import (
    CacheEntry,
    MetricsSnapshot,
    ServiceResponse,
    RequestContext
)

# Configure structured logging
logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter(
    'gateway_requests_total',
    'Total requests processed',
    ['service', 'endpoint', 'method', 'status']
)

RESPONSE_TIME = Histogram(
    'gateway_response_time_seconds',
    'Request response time',
    ['service', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

CACHE_HITS = Counter(
    'gateway_cache_hits_total',
    'Total cache hits',
    ['service', 'endpoint']
)

RATE_LIMITS = Counter(
    'gateway_rate_limits_total',
    'Total rate limit hits',
    ['service', 'endpoint']
)

CIRCUIT_BREAKS = Counter(
    'gateway_circuit_breaks_total',
    'Total circuit breaker trips',
    ['service']
)

ACTIVE_CONNECTIONS = Gauge(
    'gateway_active_connections',
    'Number of active connections',
    ['service']
)

class MetricsService:
    def __init__(self):
        self.settings = get_settings()
        
        # Response cache
        # In production, use Redis or similar
        self._cache: Dict[str, CacheEntry] = {}
        
        # Metrics storage
        self._metrics: Dict[str, List[MetricsSnapshot]] = {}
        
        # Start background tasks
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        # Initialize tracer
        self.tracer = trace.get_tracer(__name__)

    async def get_cached_response(
        self,
        cache_key: str
    ) -> Optional[ServiceResponse]:
        """
        Get cached response if available
        """
        entry = self._cache.get(cache_key)
        if not entry:
            return None
        
        if datetime.utcnow() >= entry.expires_at:
            del self._cache[cache_key]
            return None
        
        return entry.value

    async def cache_response(
        self,
        cache_key: str,
        response: ServiceResponse,
        ttl: Optional[int] = None
    ):
        """
        Cache response for future use
        """
        if not self.settings.cache_enabled:
            return
        
        config = CACHE_CONFIGS.get("default")
        ttl = ttl or config["ttl"]
        
        entry = CacheEntry(
            key=cache_key,
            value=response,
            expires_at=datetime.utcnow() + timedelta(seconds=ttl)
        )
        
        self._cache[cache_key] = entry

    def generate_cache_key(
        self,
        service: str,
        endpoint: str,
        method: str,
        params: Dict
    ) -> str:
        """
        Generate cache key from request parameters
        """
        key_parts = [
            service,
            endpoint,
            method,
            json.dumps(params, sort_keys=True)
        ]
        return ":".join(key_parts)

    async def record_request_metrics(
        self,
        context: RequestContext,
        response: ServiceResponse,
        cache_hit: bool = False
    ):
        """
        Record metrics for a request
        """
        # Update Prometheus metrics
        REQUEST_COUNT.labels(
            service=context.service,
            endpoint=context.endpoint,
            method="GET",  # TODO: Get from context
            status=response.status_code
        ).inc()
        
        RESPONSE_TIME.labels(
            service=context.service,
            endpoint=context.endpoint
        ).observe(response.duration_ms / 1000.0)
        
        if cache_hit:
            CACHE_HITS.labels(
                service=context.service,
                endpoint=context.endpoint
            ).inc()
        
        # Store metrics snapshot
        snapshot = MetricsSnapshot(
            service_id=context.service,
            requests_total=1,
            requests_failed=1 if response.status_code >= 400 else 0,
            response_time_ms=response.duration_ms,
            cache_hits=1 if cache_hit else 0,
            cache_misses=0 if cache_hit else 1,
            rate_limit_hits=0,  # Updated separately
            circuit_breaker_trips=0,  # Updated separately
            active_connections=ACTIVE_CONNECTIONS.labels(
                service=context.service
            )._value.get()
        )
        
        service_metrics = self._metrics.setdefault(context.service, [])
        service_metrics.append(snapshot)
        
        # Log metrics
        logger.info(
            "request_metrics",
            service=context.service,
            endpoint=context.endpoint,
            duration_ms=response.duration_ms,
            status_code=response.status_code,
            cache_hit=cache_hit
        )

    async def record_rate_limit(self, service: str, endpoint: str):
        """
        Record rate limit hit
        """
        RATE_LIMITS.labels(
            service=service,
            endpoint=endpoint
        ).inc()

    async def record_circuit_break(self, service: str):
        """
        Record circuit breaker trip
        """
        CIRCUIT_BREAKS.labels(
            service=service
        ).inc()

    async def get_service_metrics(
        self,
        service_id: str,
        window: int = 3600  # 1 hour
    ) -> List[MetricsSnapshot]:
        """
        Get metrics for a service within time window
        """
        cutoff = datetime.utcnow() - timedelta(seconds=window)
        metrics = self._metrics.get(service_id, [])
        
        return [
            m for m in metrics
            if m.timestamp >= cutoff
        ]

    async def _cleanup_loop(self):
        """
        Background task to clean up expired cache entries and old metrics
        """
        while True:
            try:
                current_time = datetime.utcnow()
                
                # Clean up cache
                expired_keys = [
                    key for key, entry in self._cache.items()
                    if current_time >= entry.expires_at
                ]
                for key in expired_keys:
                    del self._cache[key]
                
                # Clean up metrics (keep last 24 hours)
                cutoff = current_time - timedelta(hours=24)
                for service_id in self._metrics:
                    self._metrics[service_id] = [
                        m for m in self._metrics[service_id]
                        if m.timestamp >= cutoff
                    ]
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error("metrics_cleanup_error", error=str(e))
                await asyncio.sleep(300)

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
