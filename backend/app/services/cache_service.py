"""
Caching service for storing and retrieving results.
Uses in-memory cache with TTL and disk-based persistent cache.
"""

import time
import os
import json
import pickle
from typing import Dict, Any, Optional, Callable
from functools import wraps
import hashlib

from app.config.settings import get_settings

# In-memory cache
_cache = {}

def hash_args(*args, **kwargs) -> str:
    """
    Generate a hash from function arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        str: Hash of the arguments
    """
    # Convert args and kwargs to a string and hash it
    args_str = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(args_str.encode()).hexdigest()

def get_cache_key(func_name: str, *args, **kwargs) -> str:
    """
    Generate a cache key for a function call.
    
    Args:
        func_name: Name of the function
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        str: Cache key
    """
    args_hash = hash_args(*args, **kwargs)
    return f"{func_name}:{args_hash}"

def memory_cache_get(key: str) -> Optional[Any]:
    """
    Get a value from the in-memory cache.
    
    Args:
        key: Cache key
        
    Returns:
        Any: Cached value, or None if not found or expired
    """
    settings = get_settings()
    
    if not settings.ENABLE_CACHE:
        return None
    
    cache_entry = _cache.get(key)
    if cache_entry is None:
        return None
    
    # Check if the entry has expired
    if cache_entry["expires"] < time.time():
        del _cache[key]
        return None
    
    return cache_entry["value"]

def memory_cache_set(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """
    Set a value in the in-memory cache.
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds, or None for default
    """
    settings = get_settings()
    
    if not settings.ENABLE_CACHE:
        return
    
    if ttl is None:
        ttl = settings.CACHE_EXPIRY
    
    _cache[key] = {
        "value": value,
        "expires": time.time() + ttl
    }

def clear_memory_cache() -> None:
    """Clear the in-memory cache."""
    global _cache
    _cache = {}

def disk_cache_get(key: str) -> Optional[Any]:
    """
    Get a value from the disk-based cache.
    
    Args:
        key: Cache key
        
    Returns:
        Any: Cached value, or None if not found or expired
    """
    settings = get_settings()
    
    if not settings.ENABLE_CACHE or not settings.ENABLE_STORAGE:
        return None
    
    # Create cache directory if it doesn't exist
    cache_dir = os.path.join(settings.STORAGE_PATH, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    cache_file = os.path.join(cache_dir, f"{key}.pickle")
    if not os.path.exists(cache_file):
        return None
    
    try:
        with open(cache_file, "rb") as f:
            cache_entry = pickle.load(f)
        
        # Check if the entry has expired
        if cache_entry["expires"] < time.time():
            os.remove(cache_file)
            return None
        
        return cache_entry["value"]
    except Exception as e:
        # If there's an error reading the cache, log and continue
        print(f"Error reading disk cache: {e}")
        return None

def disk_cache_set(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """
    Set a value in the disk-based cache.
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds, or None for default
    """
    settings = get_settings()
    
    if not settings.ENABLE_CACHE or not settings.ENABLE_STORAGE:
        return
    
    if ttl is None:
        ttl = settings.CACHE_EXPIRY
    
    # Create cache directory if it doesn't exist
    cache_dir = os.path.join(settings.STORAGE_PATH, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    cache_entry = {
        "value": value,
        "expires": time.time() + ttl
    }
    
    try:
        with open(os.path.join(cache_dir, f"{key}.pickle"), "wb") as f:
            pickle.dump(cache_entry, f)
    except Exception as e:
        # If there's an error writing the cache, log and continue
        print(f"Error writing disk cache: {e}")

def cache_result(ttl: Optional[int] = None):
    """
    Decorator that caches the result of a function.
    Uses both in-memory and disk-based caching.
    
    Args:
        ttl: Time to live in seconds, or None for default
        
    Returns:
        Function: Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Skip caching if explicitly disabled for this call
            skip_cache = kwargs.pop("skip_cache", False)
            if skip_cache:
                return await func(*args, **kwargs)
            
            # Generate cache key
            cache_key = get_cache_key(func.__name__, *args, **kwargs)
            
            # Check memory cache first (faster)
            cached_result = memory_cache_get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Check disk cache if not in memory
            cached_result = disk_cache_get(cache_key)
            if cached_result is not None:
                # Also store in memory for faster future access
                memory_cache_set(cache_key, cached_result, ttl)
                return cached_result
            
            # Call the function if not cached
            result = await func(*args, **kwargs)
            
            # Cache the result
            memory_cache_set(cache_key, result, ttl)
            disk_cache_set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator

def cache_get(key: str) -> Optional[Any]:
    """
    Get a value from the cache.
    Checks both memory and disk cache.
    
    Args:
        key: Cache key
        
    Returns:
        Any: Cached value, or None if not found or expired
    """
    # Check memory cache first
    result = memory_cache_get(key)
    if result is not None:
        return result
    
    # Check disk cache if not in memory
    return disk_cache_get(key)

def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """
    Set a value in the cache.
    Stores in both memory and disk cache.
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds, or None for default
    """
    memory_cache_set(key, value, ttl)
    disk_cache_set(key, value, ttl)

def clear_cache() -> None:
    """Clear both memory and disk cache."""
    settings = get_settings()
    
    # Clear memory cache
    clear_memory_cache()
    
    # Clear disk cache
    if settings.ENABLE_STORAGE:
        cache_dir = os.path.join(settings.STORAGE_PATH, "cache")
        if os.path.exists(cache_dir):
            for file_name in os.listdir(cache_dir):
                file_path = os.path.join(cache_dir, file_name)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error removing cache file {file_path}: {e}")