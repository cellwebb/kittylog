"""Test suite for cache module."""

from unittest import mock

from kittylog.cache import (
    CacheManager,
    cached,
    cached_maxsize,
    clear_all_caches,
    get_cache_info,
    list_registered_caches,
)


class TestCacheManager:
    """Test the CacheManager class."""

    def test_register_function(self):
        """Test registering a cached function."""
        # Clear any existing caches
        CacheManager._caches.clear()

        @cached
        def test_func():
            return "cached_result"

        # Should be registered
        assert len(CacheManager._caches) == 1
        assert CacheManager._caches[0].__name__ == "test_func"

    def test_clear_all_caches_success(self):
        """Test clearing all caches successfully."""
        # Clear any existing caches
        CacheManager._caches.clear()

        # Create mock cached functions with cache_clear method
        mock_cache1 = mock.Mock()
        mock_cache1.__name__ = "cache1"
        mock_cache1.cache_clear = mock.Mock()

        mock_cache2 = mock.Mock()
        mock_cache2.__name__ = "cache2"
        mock_cache2.cache_clear = mock.Mock()

        CacheManager._caches.extend([mock_cache1, mock_cache2])

        with mock.patch("kittylog.cache.logger") as mock_logger:
            CacheManager.clear_all()

            # Both cache_clear methods should be called
            mock_cache1.cache_clear.assert_called_once()
            mock_cache2.cache_clear.assert_called_once()

            # Should log info about cleared caches
            mock_logger.info.assert_called_once_with("Cleared 2 caches")

    def test_clear_all_caches_with_attribute_error(self):
        """Test clearing caches when some functions don't have cache_clear."""
        # Clear any existing caches
        CacheManager._caches.clear()

        # Create mock cached functions
        mock_cache1 = mock.Mock()
        mock_cache1.__name__ = "cache1"
        mock_cache1.cache_clear = mock.Mock()

        # Create a mock that will raise AttributeError when accessing cache_clear
        mock_cache2 = mock.Mock(spec=["__name__"])
        mock_cache2.__name__ = "cache2"
        # Don't include cache_clear in spec - this will cause AttributeError

        CacheManager._caches.extend([mock_cache1, mock_cache2])

        with mock.patch("kittylog.cache.logger") as mock_logger:
            CacheManager.clear_all()

            # Only first cache_clear should be called
            mock_cache1.cache_clear.assert_called_once()

            # Should log warning for missing method
            mock_logger.warning.assert_called_once()
            assert "does not have cache_clear method" in mock_logger.warning.call_args[0][0]

    def test_list_caches(self):
        """Test listing registered cache functions."""
        # Clear any existing caches
        CacheManager._caches.clear()

        # Add mock cached functions
        mock_cache1 = mock.Mock()
        mock_cache1.__name__ = "cache1"

        mock_cache2 = mock.Mock()
        mock_cache2.__name__ = "cache2"

        CacheManager._caches.extend([mock_cache1, mock_cache2])

        cache_names = CacheManager.list_caches()
        assert cache_names == ["cache1", "cache2"]

    def test_get_cache_stats_lru_cache(self):
        """Test getting cache stats for lru_cache functions."""
        # Clear any existing caches
        CacheManager._caches.clear()

        # Create mock lru_cache function
        mock_cache = mock.Mock()
        mock_cache.__name__ = "lru_cache_func"

        # Mock cache_info return
        mock_info = mock.Mock()
        mock_info.hits = 10
        mock_info.misses = 2
        mock_info.maxsize = 128
        mock_info.currsize = 5

        mock_cache.cache_info.return_value = mock_info
        CacheManager._caches.append(mock_cache)

        stats = CacheManager.get_cache_stats()

        assert "lru_cache_func" in stats
        assert stats["lru_cache_func"]["hits"] == 10
        assert stats["lru_cache_func"]["misses"] == 2
        assert stats["lru_cache_func"]["maxsize"] == 128
        assert stats["lru_cache_func"]["currsize"] == 5
        assert stats["lru_cache_func"]["hit_rate"] == 10 / 12

    def test_get_cache_stats_regular_cache(self):
        """Test getting cache stats for regular cache functions."""
        # Clear any existing caches
        CacheManager._caches.clear()

        # Create mock cache function without cache_info
        mock_cache = mock.Mock()
        mock_cache.__name__ = "cache_func"
        del mock_cache.cache_info  # Remove cache_info method

        CacheManager._caches.append(mock_cache)

        stats = CacheManager.get_cache_stats()

        assert "cache_func" in stats
        assert stats["cache_func"]["type"] == "cache"
        assert stats["cache_func"]["details"] == "unavailable"

    def test_get_cache_stats_exception(self):
        """Test getting cache stats when an exception occurs."""
        # Clear any existing caches
        CacheManager._caches.clear()

        # Create mock cache function that raises exception
        mock_cache = mock.Mock()
        mock_cache.__name__ = "error_cache"
        mock_cache.cache_info.side_effect = Exception("Test error")

        CacheManager._caches.append(mock_cache)

        stats = CacheManager.get_cache_stats()

        assert "error_cache" in stats
        assert "error" in stats["error_cache"]
        assert "Test error" in stats["error_cache"]["error"]

    def test_get_cache_stats_division_by_zero(self):
        """Test getting cache stats when hits + misses = 0."""
        # Clear any existing caches
        CacheManager._caches.clear()

        # Create mock lru_cache function with no hits/misses
        mock_cache = mock.Mock()
        mock_cache.__name__ = "empty_cache"

        mock_info = mock.Mock()
        mock_info.hits = 0
        mock_info.misses = 0
        mock_info.maxsize = 128
        mock_info.currsize = 0

        mock_cache.cache_info.return_value = mock_info
        CacheManager._caches.append(mock_cache)

        stats = CacheManager.get_cache_stats()

        assert "empty_cache" in stats
        assert stats["empty_cache"]["hit_rate"] == 0


class TestCachedDecorators:
    """Test the cached decorator functions."""

    def test_cached_decorator(self):
        """Test the @cached decorator."""
        # Clear any existing caches
        CacheManager._caches.clear()

        call_count = 0

        @cached
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call should execute function
        result1 = test_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call should use cache
        result2 = test_function(5)
        assert result2 == 10
        assert call_count == 1  # Should still be 1 due to caching

        # Different argument should execute function
        result3 = test_function(6)
        assert result3 == 12
        assert call_count == 2

        # Should be registered with CacheManager
        assert len(CacheManager._caches) == 1
        assert CacheManager._caches[0].__name__ == "test_function"

    def test_cached_maxsize_decorator(self):
        """Test the @cached_maxsize decorator."""
        # Clear any existing caches
        CacheManager._caches.clear()

        call_count = 0

        @cached_maxsize(maxsize=3)
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return x * 3

        # First calls should execute function
        _result1 = test_function(1)
        _result2 = test_function(2)
        _result3 = test_function(3)
        assert call_count == 3

        # Cached calls should not increment count
        result1_cached = test_function(1)
        result2_cached = test_function(2)
        assert result1_cached == 3
        assert result2_cached == 6
        assert call_count == 3  # Should still be 3 due to caching

        # Should be registered with CacheManager
        assert len(CacheManager._caches) == 1
        assert CacheManager._caches[0].__name__ == "test_function"


class TestConvenienceFunctions:
    """Test the convenience functions."""

    def test_clear_all_caches_function(self):
        """Test the clear_all_caches convenience function."""
        # Clear any existing caches
        CacheManager._caches.clear()

        mock_cache = mock.Mock()
        mock_cache.__name__ = "test_cache"
        mock_cache.cache_clear = mock.Mock()
        CacheManager._caches.append(mock_cache)

        with mock.patch.object(CacheManager, "clear_all") as mock_clear:
            clear_all_caches()
            mock_clear.assert_called_once()

    def test_get_cache_info_function(self):
        """Test the get_cache_info convenience function."""
        with mock.patch.object(CacheManager, "get_cache_stats") as mock_stats:
            mock_stats.return_value = {"test": {"hits": 5}}

            result = get_cache_info()
            assert result == {"test": {"hits": 5}}
            mock_stats.assert_called_once()

    def test_list_registered_caches_function(self):
        """Test the list_registered_caches convenience function."""
        with mock.patch.object(CacheManager, "list_caches") as mock_list:
            mock_list.return_value = ["cache1", "cache2"]

            result = list_registered_caches()
            assert result == ["cache1", "cache2"]
            mock_list.assert_called_once()


class TestLoggingIntegration:
    """Test logging integration in cache operations."""

    @mock.patch("kittylog.cache.logger")
    def test_register_logs_debug(self, mock_logger):
        """Test that registering a function logs debug message."""
        # Clear any existing caches
        CacheManager._caches.clear()

        def test_func():
            return "result"

        CacheManager.register(test_func)

        mock_logger.debug.assert_called_once_with("Registered cache function: test_func")

    @mock.patch("kittylog.cache.logger")
    def test_clear_all_logs_success(self, mock_logger):
        """Test that clearing caches logs success message."""
        # Clear any existing caches
        CacheManager._caches.clear()

        mock_cache = mock.Mock()
        mock_cache.__name__ = "test_cache"
        mock_cache.cache_clear = mock.Mock()
        CacheManager._caches.append(mock_cache)

        CacheManager.clear_all()

        mock_logger.debug.assert_called_with("Cleared cache: test_cache")
        mock_logger.info.assert_called_once_with("Cleared 1 caches")

    @mock.patch("kittylog.cache.logger")
    def test_clear_all_logs_warning(self, mock_logger):
        """Test that clearing caches logs warning for missing method."""
        # Clear any existing caches
        CacheManager._caches.clear()

        # Create a mock that will raise AttributeError when accessing cache_clear
        mock_cache = mock.Mock(spec=["__name__"])
        mock_cache.__name__ = "broken_cache"
        # Don't include cache_clear in spec - this will cause AttributeError
        CacheManager._caches.append(mock_cache)

        CacheManager.clear_all()

        mock_logger.warning.assert_called_once_with("Function broken_cache does not have cache_clear method")
