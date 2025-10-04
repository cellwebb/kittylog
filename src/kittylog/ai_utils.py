"""AI utilities for changelog generation.

This module contains retry logic and other AI utilities.
"""

import logging
import time

from kittylog.errors import AIError

logger = logging.getLogger(__name__)


def generate_with_retries(
    provider_funcs: dict,
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
    supported_providers = ["anthropic", "openai", "groq", "cerebras", "ollama", "openrouter", "zai", "zai-coding"]
    if provider not in supported_providers:
        raise AIError.generation_error(f"Unsupported provider: {provider}. Supported providers: {supported_providers}")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    last_exception = None

    for attempt in range(max_retries):
        try:
            if not quiet and attempt > 0:
                logger.info(f"Retry attempt {attempt + 1}/{max_retries}")

            # Call the appropriate provider function
            provider_func = provider_funcs.get(provider)
            if not provider_func:
                raise AIError.generation_error(f"Provider function not found for: {provider}")

            content = provider_func(model=model_name, messages=messages, temperature=temperature, max_tokens=max_tokens)

            if content:
                return content.strip()
            else:
                raise AIError.generation_error("Empty response from AI model")

        except Exception as e:
            last_exception = e
            # Import classify_error function from ai module for compatibility
            from kittylog.ai import classify_error

            error_type = classify_error(e)

            if error_type in ["authentication", "model_not_found", "context_length"]:
                # Don't retry these errors
                raise AIError.generation_error(f"AI generation failed: {str(e)}") from e

            if attempt < max_retries - 1:
                # Exponential backoff
                wait_time = 2**attempt
                if not quiet:
                    logger.warning(f"AI generation failed (attempt {attempt + 1}), retrying in {wait_time}s: {str(e)}")
                time.sleep(wait_time)
            else:
                logger.error(f"AI generation failed after {max_retries} attempts: {str(e)}")

    # If we get here, all retries failed
    raise AIError.generation_error(
        f"AI generation failed after {max_retries} attempts: {str(last_exception)}"
    ) from last_exception
