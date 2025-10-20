"""Rate limiting utilities."""

from functools import wraps
from typing import Callable, Any
from fastapi import Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import settings


def get_limiter() -> Limiter:
    """Get rate limiter instance."""
    if settings.rate_limit_enabled:
        try:
            # Test Redis connection
            import redis
            r = redis.Redis.from_url(settings.rate_limit_redis_url)
            r.ping()
            return Limiter(
                key_func=get_remote_address,
                storage_uri=settings.rate_limit_redis_url
            )
        except Exception:
            # Fall back to memory storage if Redis is not available
            return Limiter(
                key_func=get_remote_address,
                storage_uri="memory://"
            )
    else:
        # Return a no-op limiter for development
        return Limiter(
            key_func=get_remote_address,
            storage_uri="memory://"
        )


def rate_limit(limit: str, per: str = "minute") -> Callable:
    """Decorator for rate limiting endpoints."""
    limiter = get_limiter()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the Request object in the arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # If no Request found, try to get it from kwargs
                request = kwargs.get('request') or kwargs.get('http_request')
            
            if not request:
                # If still no request found, call the function without rate limiting
                return await func(*args, **kwargs)
            
            try:
                # Apply rate limit using the limiter directly
                limiter.limit(f"{limit} per {per}")(lambda req: None)(request)
                return await func(*args, **kwargs)
            except RateLimitExceeded:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded: {limit} per {per}"
                    }
                )
        
        return wrapper
    
    return decorator


# Predefined rate limits from the spec
def compute_rate_limit(func: Callable) -> Callable:
    """Rate limit for /compute endpoint: 10/min."""
    return rate_limit("10", "minute")(func)


def predict_rate_limit(func: Callable) -> Callable:
    """Rate limit for /predict/question endpoint: 5/min."""
    return rate_limit("5", "minute")(func)


def general_rate_limit(func: Callable) -> Callable:
    """Rate limit for other endpoints: 60/min."""
    return rate_limit("60", "minute")(func)


def burst_rate_limit(func: Callable) -> Callable:
    """Burst rate limit: 2x for 10s."""
    return rate_limit("2", "10 seconds")(func)

