"""Provider registry for AI providers."""

from collections.abc import Callable, Generator
from functools import wraps
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kittylog.providers.base import BaseConfiguredProvider

# Global registry for provider functions
PROVIDER_REGISTRY: dict[str, Callable[..., str]] = {}
STREAMING_PROVIDER_REGISTRY: dict[str, Callable[..., Generator[tuple[str, dict | None], None, None]]] = {}


def create_provider_func(provider_class: type["BaseConfiguredProvider"]) -> Callable[..., str]:
    """Create a provider function from a provider class.

    This function creates a callable that:
    1. Instantiates the provider class
    2. Calls generate() with the provided arguments
    3. Is wrapped with @handle_provider_errors for consistent error handling

    Args:
        provider_class: A provider class with a `config` class attribute

    Returns:
        A callable function that can be used to generate text
    """
    from kittylog.providers.error_handler import handle_provider_errors

    provider_name = provider_class.config.name

    @handle_provider_errors(provider_name)
    @wraps(provider_class.generate)
    def provider_func(model: str, messages: list[dict[str, Any]], temperature: float, max_tokens: int, **kwargs) -> str:
        provider = provider_class(provider_class.config)
        return provider.generate(
            model=model, messages=messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        )

    # Add metadata for introspection
    provider_func.__name__ = f"call_{provider_name.lower().replace(' ', '_').replace('.', '_')}_api"
    provider_func.__doc__ = f"Call {provider_name} API to generate text."

    return provider_func


def create_streaming_provider_func(
    provider_class: type["BaseConfiguredProvider"],
) -> Callable[..., Generator[tuple[str, dict | None], None, None]]:
    """Create a streaming provider function from a provider class.

    This function creates a callable that:
    1. Instantiates the provider class
    2. Calls generate_stream() with the provided arguments
    3. Yields chunks as they're received
    4. Is wrapped with @handle_provider_errors for consistent error handling

    Args:
        provider_class: A provider class with a `config` class attribute

    Returns:
        A callable generator function that can be used to stream text
    """
    from kittylog.providers.error_handler import handle_provider_errors

    provider_name = provider_class.config.name

    @handle_provider_errors(provider_name)
    @wraps(provider_class.generate_stream)
    def streaming_provider_func(
        model: str, messages: list[dict[str, Any]], temperature: float, max_tokens: int, **kwargs
    ) -> Generator[tuple[str, dict | None], None, None]:
        provider = provider_class(provider_class.config)
        yield from provider.generate_stream(
            model=model, messages=messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        )

    # Add metadata for introspection
    streaming_provider_func.__name__ = f"stream_{provider_name.lower().replace(' ', '_').replace('.', '_')}_api"
    streaming_provider_func.__doc__ = f"Stream text from {provider_name} API."

    return streaming_provider_func


def register_provider(name: str, provider_class: type["BaseConfiguredProvider"]) -> None:
    """Register a provider class and auto-generate its function.

    Args:
        name: Provider name (e.g., "openai", "anthropic")
        provider_class: The provider class to register
    """
    PROVIDER_REGISTRY[name] = create_provider_func(provider_class)
    STREAMING_PROVIDER_REGISTRY[name] = create_streaming_provider_func(provider_class)


__all__ = [
    "PROVIDER_REGISTRY",
    "STREAMING_PROVIDER_REGISTRY",
    "register_provider",
]
