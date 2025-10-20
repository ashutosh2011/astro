"""Redis cache service for calculation caching."""

import json
import gzip
from typing import Optional, Any
import redis
from redis.connection import ConnectionPool
from app.config import settings
from app.utils.errors import ValidationError


class CacheService:
    """Redis cache service for calculation caching."""
    
    def __init__(self):
        """Initialize Redis cache service."""
        self.redis_client = None
        self.pool = None
        self._connected = False
        
        try:
            # Create connection pool
            self.pool = ConnectionPool.from_url(
                settings.redis_url,
                max_connections=20,
                retry_on_timeout=True
            )
            
            # Create Redis client
            self.redis_client = redis.Redis(connection_pool=self.pool)
            
            # Test connection
            self.redis_client.ping()
            self._connected = True
            
        except Exception as e:
            # Log warning but don't fail - allow app to start without Redis
            print(f"Warning: Failed to connect to Redis: {str(e)}")
            print("Cache service will be disabled. App will continue to work without caching.")
            self._connected = False
    
    def _compress_data(self, data: Any) -> bytes:
        """Compress data using gzip."""
        json_str = json.dumps(data, default=str)
        return gzip.compress(json_str.encode('utf-8'))
    
    def _decompress_data(self, compressed_data: bytes) -> Any:
        """Decompress data using gzip."""
        json_str = gzip.decompress(compressed_data).decode('utf-8')
        return json.loads(json_str)
    
    def get(self, key: str) -> Optional[Any]:
        """Get data from cache."""
        if not self._connected:
            return None
            
        try:
            compressed_data = self.redis_client.get(key)
            if compressed_data is None:
                return None
            
            return self._decompress_data(compressed_data)
        except Exception as e:
            # Log error but don't fail the request
            print(f"Cache get error for key {key}: {str(e)}")
            return None
    
    def set(self, key: str, data: Any, ttl_seconds: int = None) -> bool:
        """Set data in cache with TTL."""
        if not self._connected:
            return False
            
        try:
            if ttl_seconds is None:
                ttl_seconds = settings.cache_ttl_hours * 3600  # Convert hours to seconds
            
            compressed_data = self._compress_data(data)
            return self.redis_client.setex(key, ttl_seconds, compressed_data)
        except Exception as e:
            # Log error but don't fail the request
            print(f"Cache set error for key {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete data from cache."""
        if not self._connected:
            return False
            
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            print(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._connected:
            return False
            
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            print(f"Cache exists error for key {key}: {str(e)}")
            return False
    
    def get_calc_snapshot(self, input_hash: str) -> Optional[dict]:
        """Get calculation snapshot from cache."""
        cache_key = f"calc_snapshot:{input_hash}"
        return self.get(cache_key)
    
    def set_calc_snapshot(self, input_hash: str, calc_data: dict) -> bool:
        """Set calculation snapshot in cache."""
        cache_key = f"calc_snapshot:{input_hash}"
        return self.set(cache_key, calc_data)
    
    def delete_calc_snapshot(self, input_hash: str) -> bool:
        """Delete calculation snapshot from cache."""
        cache_key = f"calc_snapshot:{input_hash}"
        return self.delete(cache_key)
    
    def get_user_cache_keys(self, user_id: int) -> list:
        """Get all cache keys for a user (for cache invalidation)."""
        try:
            pattern = f"calc_snapshot:*"
            keys = self.redis_client.keys(pattern)
            
            # Filter keys that belong to this user's profiles
            # This is a simplified approach - in production, you might want to store
            # user_id in the cache key or maintain a separate index
            user_keys = []
            for key in keys:
                # For now, we'll return all calc_snapshot keys
                # In a more sophisticated implementation, you'd track user->profile->calc relationships
                user_keys.append(key.decode('utf-8'))
            
            return user_keys
        except Exception as e:
            print(f"Error getting user cache keys: {str(e)}")
            return []
    
    def clear_user_cache(self, user_id: int) -> int:
        """Clear all cache entries for a user."""
        keys = self.get_user_cache_keys(user_id)
        if not keys:
            return 0
        
        try:
            return self.redis_client.delete(*keys)
        except Exception as e:
            print(f"Error clearing user cache: {str(e)}")
            return 0
    
    def health_check(self) -> bool:
        """Check Redis connection health."""
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False


# Global cache service instance
cache_service = CacheService()

