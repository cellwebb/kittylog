"""Unified cache management for kittylog.

This module provides centralized cache management with the ability
to clear all caches at once, useful for testing and configuration changes.
"""

import logging
from collections.abc import Callable
from functools import lru_cache
from typing import Any, Protocol, TypeVar, cast

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class CachedFunction(Protocol[F]):
    """Protocol for cached functions that have cache_clear method."""

    cache_clear: Callable[[], None]
    cache_info: Callable[[], Any]
    __call__: F
    __name__: str


class CacheManager:
    """Centralized cache manager that tracks all registered caches."""

    _caches: list[CachedFunction] = []

    @classmethod
    def register(cls, func: Callable) -> Callable:  # Changed return type to match usage
        """Register a cached function with the manager."""
        cls._caches.append(func)  # type: ignore[arg-type]
        logger.debug(f"Registered cache function: {func.__name__}")
        return func

    @classmethod
    def clear_all(cls) -> None:
        """Clear all registered caches."""
        cleared_count = 0
        for cache_func in cls._caches:
            try:
                # Both @lru_cache and @cache have cache_clear method
                cache_func.cache_clear()
                cleared_count += 1
                logger.debug(f"Cleared cache: {cache_func.__name__}")
            except AttributeError:
                logger.warning(f"Function {cache_func.__name__} does not have cache_clear method")

        logger.info(f"Cleared {cleared_count} caches")

    @classmethod
    def list_caches(cls) -> list[str]:
        """List all registered cache functions."""
        return [func.__name__ for func in cls._caches]

    @classmethod
    def get_cache_stats(cls) -> dict[str, dict]:
        """Get statistics for all registered caches."""
        stats = {}
        for cache_func in cls._caches:
            try:
                if hasattr(cache_func, "cache_info"):
                    # @lru_cache has cache_info()
                    info = cache_func.cache_info()
                    stats[cache_func.__name__] = {
                        "hits": info.hits,
                        "misses": info.misses,
                        "maxsize": info.maxsize,
                        "currsize": info.currsize,
                        "hit_rate": info.hits / (info.hits + info.misses) if (info.hits + info.misses) > 0 else 0,
                    }
                else:
                    # @cache doesn't have detailed stats
                    stats[cache_func.__name__] = {"type": "cache", "details": "unavailable"}
            except Exception as e:
                stats[cache_func.__name__] = {"error": str(e)}

        return stats


def cached(func: F) -> CachedFunction[F]:
    """Decorator that creates a cached function and registers it with CacheManager.

    Replaces @lru_cache usage with automatic registration.

    Args:
        func: Function to cache

    Returns:
        Cached function registered with CacheManager
    """
    # Use lru_cache with reasonable maxsize for git operations
    wrapped = cast("CachedFunction[F]", lru_cache(maxsize=128)(func))
    return CacheManager.register(wrapped)  # type: ignore[return-value]


def cached_maxsize(maxsize: int) -> Callable[[F], CachedFunction[F]]:
    """Decorator factory for cached functions with custom maxsize.

    Args:
        maxsize: Maximum cache size

    Returns:
        Decorator function
    """

    def decorator(func: F) -> CachedFunction[F]:
        wrapped = cast("CachedFunction[F]", lru_cache(maxsize=maxsize)(func))
        return CacheManager.register(wrapped)  # type: ignore[return-value]

    return decorator


# Convenience function to clear caches from anywhere
def clear_all_caches() -> None:
    """Clear all registered caches."""
    CacheManager.clear_all()


def get_cache_info() -> dict[str, dict]:
    """Get cache statistics."""
    return CacheManager.get_cache_stats()


def list_registered_caches() -> list[str]:
    """List all registered cache functions."""
    return CacheManager.list_caches()
