from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import asyncio
import time
from ..config import get_settings, RATE_LIMIT_CONFIGS, CIRCUIT_BREAKER_CONFIGS
from ..models.gateway_models import (
    RateLimitState,
    CircuitBreakerState,
    CircuitState,
    ServiceStatus
)

class ResilienceService:
    def __init__(self):
        self.settings = get_settings()
        
        # In-memory storage for rate limiting
        # In production, use Redis or similar
        self._rate_limits: Dict[str, RateLimitState] = {}
        
        # Circuit breaker state
        self._circuit_states: Dict[str, CircuitBreakerState] = {}
        
        # Start background tasks
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def check_rate_limit(
        self,
        key: str,
        limit_type: str = "default"
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if request should be rate limited
        Returns (is_allowed, retry_after)
        """
        try:
            config = RATE_LIMIT_CONFIGS.get(limit_type, RATE_LIMIT_CONFIGS["default"])
            current_time = datetime.utcnow()
            
            # Get or create rate limit state
            state = self._rate_limits.get(key)
            if not state or self._is_window_expired(state, current_time):
                state = RateLimitState(
                    key=key,
                    window_start=current_time,
                    request_count=0,
                    window_size=config["window"],
                    limit=config["requests"]
                )
                self._rate_limits[key] = state
            
            # Check if limit is exceeded
            if state.is_exceeded:
                retry_after = self._calculate_retry_after(state)
                return False, retry_after
            
            # Increment request count
            state.request_count += 1
            return True, None

        except Exception as e:
            # Log error but allow request
            print(f"Rate limit check failed: {str(e)}")
            return True, None

    async def check_circuit_breaker(
        self,
        service_id: str,
        config_type: str = "default"
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if circuit breaker should allow request
        Returns (is_allowed, retry_after)
        """
        try:
            config = CIRCUIT_BREAKER_CONFIGS.get(
                config_type,
                CIRCUIT_BREAKER_CONFIGS["default"]
            )
            
            # Get or create circuit state
            state = self._circuit_states.get(service_id)
            if not state:
                state = CircuitBreakerState(
                    service_id=service_id,
                    state=CircuitState.CLOSED,
                    failure_count=0
                )
                self._circuit_states[service_id] = state
            
            current_time = datetime.utcnow()
            
            # Handle different circuit states
            if state.state == CircuitState.OPEN:
                # Check if recovery timeout has elapsed
                if state.recovery_time and current_time >= state.recovery_time:
                    state.state = CircuitState.HALF_OPEN
                    state.failure_count = 0
                else:
                    retry_after = self._calculate_recovery_time(state)
                    return False, retry_after
            
            elif state.state == CircuitState.HALF_OPEN:
                # Allow limited traffic in half-open state
                if state.failure_count >= config["max_failures"]:
                    state.state = CircuitState.OPEN
                    state.recovery_time = current_time + timedelta(
                        seconds=config["recovery_timeout"]
                    )
                    return False, config["recovery_timeout"]
            
            return True, None

        except Exception as e:
            # Log error but allow request
            print(f"Circuit breaker check failed: {str(e)}")
            return True, None

    async def record_success(self, service_id: str):
        """
        Record successful request
        """
        state = self._circuit_states.get(service_id)
        if state:
            if state.state == CircuitState.HALF_OPEN:
                state.state = CircuitState.CLOSED
            state.failure_count = 0
            state.last_failure = None
            state.recovery_time = None

    async def record_failure(
        self,
        service_id: str,
        config_type: str = "default"
    ):
        """
        Record failed request
        """
        config = CIRCUIT_BREAKER_CONFIGS.get(
            config_type,
            CIRCUIT_BREAKER_CONFIGS["default"]
        )
        
        state = self._circuit_states.get(service_id)
        if not state:
            state = CircuitBreakerState(
                service_id=service_id,
                state=CircuitState.CLOSED,
                failure_count=0
            )
            self._circuit_states[service_id] = state
        
        state.failure_count += 1
        state.last_failure = datetime.utcnow()
        
        # Check if should open circuit
        if state.failure_count >= config["failure_threshold"]:
            state.state = CircuitState.OPEN
            state.recovery_time = datetime.utcnow() + timedelta(
                seconds=config["recovery_timeout"]
            )

    def get_service_status(self, service_id: str) -> ServiceStatus:
        """
        Get current service status based on circuit state
        """
        state = self._circuit_states.get(service_id)
        if not state:
            return ServiceStatus.HEALTHY
        
        if state.state == CircuitState.CLOSED:
            return ServiceStatus.HEALTHY
        elif state.state == CircuitState.HALF_OPEN:
            return ServiceStatus.DEGRADED
        else:
            return ServiceStatus.DOWN

    async def _cleanup_loop(self):
        """
        Background task to clean up expired rate limits and circuit states
        """
        while True:
            try:
                current_time = datetime.utcnow()
                
                # Clean up rate limits
                expired_keys = [
                    key for key, state in self._rate_limits.items()
                    if self._is_window_expired(state, current_time)
                ]
                for key in expired_keys:
                    del self._rate_limits[key]
                
                # Clean up circuit states
                closed_circuits = [
                    service_id for service_id, state in self._circuit_states.items()
                    if state.state == CircuitState.CLOSED and not state.failure_count
                ]
                for service_id in closed_circuits:
                    del self._circuit_states[service_id]
                
                await asyncio.sleep(60)  # Run cleanup every minute
                
            except Exception as e:
                print(f"Cleanup task error: {str(e)}")
                await asyncio.sleep(60)

    def _is_window_expired(
        self,
        state: RateLimitState,
        current_time: datetime
    ) -> bool:
        """
        Check if rate limit window has expired
        """
        window_end = state.window_start + timedelta(seconds=state.window_size)
        return current_time >= window_end

    def _calculate_retry_after(self, state: RateLimitState) -> int:
        """
        Calculate seconds until rate limit resets
        """
        window_end = state.window_start + timedelta(seconds=state.window_size)
        return int((window_end - datetime.utcnow()).total_seconds())

    def _calculate_recovery_time(self, state: CircuitBreakerState) -> int:
        """
        Calculate seconds until circuit breaker recovery
        """
        if not state.recovery_time:
            return 0
        return int((state.recovery_time - datetime.utcnow()).total_seconds())

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
