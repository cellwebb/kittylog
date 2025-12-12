"""AI utilities for changelog generation.

This module contains retry logic and other AI utilities.
"""

import logging
import time
from collections.abc import Callable, Generator

import httpx

from kittylog.errors import AIError
from kittylog.providers import SUPPORTED_PROVIDERS

logger = logging.getLogger(__name__)

# Type alias for provider functions (uses ... for flexible kwargs)
ProviderFunc = Callable[..., str]
StreamingProviderFunc = Callable[..., Generator[tuple[str, dict | None], None, None]]


def generate_with_retries(
    provider_funcs: dict[str, ProviderFunc],
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    max_retries: int,
    quiet: bool = False,
) -> str:
    """Generate content with retry logic using direct API calls."""
    # Parse model string to determine provider and actual model
    if ":" not in model:
        raise AIError.generation_error(f"Invalid model format. Expected 'provider:model', got '{model}'")

    provider, model_name = model.split(":", 1)

    # Validate provider
    if provider not in SUPPORTED_PROVIDERS:
        raise AIError.generation_error(f"Unsupported provider: {provider}. Supported providers: {SUPPORTED_PROVIDERS}")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    last_exception: Exception | None = None

    for attempt in range(max_retries):
        try:
            if not quiet and attempt > 0:
                logger.info(f"Retry attempt {attempt + 1}/{max_retries}")

            # Call the appropriate provider function
            provider_func = provider_funcs.get(provider)
            if not provider_func:
                raise AIError.generation_error(f"Provider function not found for: {provider}")

            # API keys are loaded into os.environ via load_dotenv in config/loader.py
            content = provider_func(model=model_name, messages=messages, temperature=temperature, max_tokens=max_tokens)

            if content:
                return content.strip()
            else:
                raise AIError.generation_error("Empty response from AI model")

        except (AIError, httpx.HTTPError, TimeoutError, ValueError, TypeError, RuntimeError) as e:
            last_exception = e
            # Import classify_error from errors module
            from kittylog.errors import classify_error

            error_type = classify_error(e)
        except Exception as e:
            # Re-raise system exceptions that should never be caught
            if isinstance(e, (KeyboardInterrupt, SystemExit, GeneratorExit)):
                raise
            # Use classify_error for unknown exceptions
            last_exception = e
            from kittylog.errors import classify_error

            error_type = classify_error(e)

            if error_type in ["authentication", "model_not_found", "context_length"]:
                # Don't retry these errors
                raise AIError.generation_error(f"AI generation failed: {e!s}") from e

            if attempt < max_retries - 1:
                # Exponential backoff
                wait_time = 2**attempt
                if not quiet:
                    logger.warning(f"AI generation failed (attempt {attempt + 1}), retrying in {wait_time}s: {e!s}")
                time.sleep(wait_time)
            else:
                logger.error(f"AI generation failed after {max_retries} attempts: {e!s}")

    # If we get here, all retries failed
    raise AIError.generation_error(
        f"AI generation failed after {max_retries} attempts: {last_exception!s}"
    ) from last_exception


def generate_with_retries_stream(
    streaming_provider_funcs: dict[str, StreamingProviderFunc],
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    max_retries: int,
    quiet: bool = False,
) -> Generator[tuple[str, dict | None], None, None]:
    """Generate content with streaming and retry logic.

    Args:
        streaming_provider_funcs: Dictionary of streaming provider functions
        model: Model string in format "provider:model"
        system_prompt: System prompt text
        user_prompt: User prompt text
        temperature: Temperature parameter
        max_tokens: Maximum output tokens
        max_retries: Maximum retry attempts
        quiet: Whether to suppress spinner/output

    Yields:
        Tuple[str, dict | None]:
        - (chunk_text, None) for content chunks
        - ("", usage_dict) for final yield with token usage

    Raises:
        AIError: If generation fails after all retries
    """
    # Parse model string to determine provider and actual model
    if ":" not in model:
        raise AIError.generation_error(f"Invalid model format. Expected 'provider:model', got '{model}'")

    provider, model_name = model.split(":", 1)

    # Validate provider
    if provider not in SUPPORTED_PROVIDERS:
        raise AIError.generation_error(f"Unsupported provider: {provider}. Supported providers: {SUPPORTED_PROVIDERS}")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    last_exception: Exception | None = None

    for attempt in range(max_retries):
        try:
            if not quiet and attempt > 0:
                logger.info(f"Retry attempt {attempt + 1}/{max_retries}")

            # Call the appropriate streaming provider function
            streaming_func = streaming_provider_funcs.get(provider)
            if not streaming_func:
                raise AIError.generation_error(f"Streaming provider function not found for: {provider}")

            # Stream chunks from the provider
            accumulated_chunks = []
            final_usage = None

            for chunk, usage in streaming_func(
                model=model_name, messages=messages, temperature=temperature, max_tokens=max_tokens
            ):
                if usage is None:
                    # Content chunk - yield it and accumulate
                    accumulated_chunks.append(chunk)
                    yield (chunk, None)
                else:
                    # Final yield with usage
                    final_usage = usage

            # Verify we got some content
            if not accumulated_chunks:
                raise AIError.generation_error("Empty response from AI model")

            # Yield final usage data
            if final_usage:
                yield ("", final_usage)
            else:
                # Estimate if not provided
                yield (
                    "",
                    {
                        "prompt_tokens": 0,
                        "completion_tokens": len("".join(accumulated_chunks)) // 4,
                        "total_tokens": 0,
                    },
                )

            # Success - exit the retry loop
            return

        except (AIError, httpx.HTTPError, TimeoutError, ValueError, TypeError, RuntimeError) as e:
            last_exception = e
            # Import classify_error from errors module
            from kittylog.errors import classify_error

            error_type = classify_error(e)

            if error_type in ["authentication", "model_not_found", "context_length"]:
                # Don't retry these errors
                raise AIError.generation_error(f"AI generation failed: {e!s}") from e

            if attempt < max_retries - 1:
                # Exponential backoff
                wait_time = 2**attempt
                if not quiet:
                    logger.warning(f"AI generation failed (attempt {attempt + 1}), retrying in {wait_time}s: {e!s}")
                time.sleep(wait_time)
            else:
                logger.error(f"AI generation failed after {max_retries} attempts: {e!s}")

        except Exception as e:
            # Re-raise system exceptions that should never be caught
            if isinstance(e, (KeyboardInterrupt, SystemExit, GeneratorExit)):
                raise
            # Use classify_error for unknown exceptions
            last_exception = e
            from kittylog.errors import classify_error

            error_type = classify_error(e)

            if error_type in ["authentication", "model_not_found", "context_length"]:
                # Don't retry these errors
                raise AIError.generation_error(f"AI generation failed: {e!s}") from e

            if attempt < max_retries - 1:
                # Exponential backoff
                wait_time = 2**attempt
                if not quiet:
                    logger.warning(f"AI generation failed (attempt {attempt + 1}), retrying in {wait_time}s: {e!s}")
                time.sleep(wait_time)
            else:
                logger.error(f"AI generation failed after {max_retries} attempts: {e!s}")

    # If we get here, all retries failed
    raise AIError.generation_error(
        f"AI streaming generation failed after {max_retries} attempts: {last_exception!s}"
    ) from last_exception
