"""AI integration for changelog generation.

This module handles AI model integration for generating changelog entries from commit data.
Based on gac's AI module but specialized for changelog generation.
"""

import logging
import time

import aisuite as ai
from rich.console import Console
from rich.panel import Panel

from clog.config import load_config
from clog.constants import EnvDefaults
from clog.errors import AIError
from clog.prompt import build_changelog_prompt, clean_changelog_content
from clog.utils import count_tokens

logger = logging.getLogger(__name__)
config = load_config()


def generate_changelog_entry(
    commits: list[dict],
    tag: str,
    from_tag: str | None = None,
    model: str | None = None,
    hint: str = "",
    show_prompt: bool = False,
    quiet: bool = False,
    temperature: float | None = None,
    max_tokens: int | None = None,
    max_retries: int | None = None,
    diff_content: str = "",
) -> str:
    """Generate a changelog entry using AI.

    Args:
        commits: List of commit dictionaries
        tag: The target tag/version
        from_tag: The previous tag (for context)
        model: AI model to use
        hint: Additional context hint
        show_prompt: Whether to display the prompt
        quiet: Whether to suppress spinner/output
        temperature: Model temperature
        max_tokens: Maximum output tokens
        max_retries: Maximum retry attempts

    Returns:
        Generated changelog content
    """
    if model is None:
        model_value = config["model"]
        if not model_value:
            raise AIError.model_error("No model specified. Please configure a model.")
        model = str(model_value)

    if temperature is None:
        temperature_value = config.get("temperature", EnvDefaults.TEMPERATURE)
        temperature = float(temperature_value) if temperature_value is not None else EnvDefaults.TEMPERATURE
    if max_tokens is None:
        max_tokens_value = config.get("max_output_tokens", EnvDefaults.MAX_OUTPUT_TOKENS)
        max_tokens = int(max_tokens_value) if max_tokens_value is not None else EnvDefaults.MAX_OUTPUT_TOKENS
    if max_retries is None:
        max_retries_value = config.get("max_retries", EnvDefaults.MAX_RETRIES)
        max_retries = int(max_retries_value) if max_retries_value is not None else EnvDefaults.MAX_RETRIES

    # Build the prompt
    system_prompt, user_prompt = build_changelog_prompt(
        commits=commits,
        tag=tag,
        from_tag=from_tag,
        hint=hint,
    )

    # Add diff content to user prompt if available, but limit its size to prevent timeouts
    if diff_content:
        # Limit diff content to 5000 characters to prevent extremely large prompts
        max_diff_length = 5000
        if len(diff_content) > max_diff_length:
            diff_content = diff_content[:max_diff_length] + "\n\n... (diff content truncated for brevity)"
        user_prompt += f"\n\n## Detailed Changes (Git Diff):\n\n{diff_content}"

    if show_prompt:
        console = Console()
        full_prompt = f"SYSTEM PROMPT:\n{system_prompt}\n\nUSER PROMPT:\n{user_prompt}"
        console.print(
            Panel(
                full_prompt,
                title="Prompt for LLM",
                border_style="bright_blue",
            )
        )

    # Count tokens
    prompt_tokens = count_tokens(system_prompt, model) + count_tokens(user_prompt, model)
    logger.info(f"Prompt tokens: {prompt_tokens}")

    # Generate the changelog content
    try:
        content = _generate_with_retries(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            quiet=quiet,
        )

        # Clean and format the content
        cleaned_content = clean_changelog_content(content)

        # Apply additional post-processing
        from clog.postprocess import postprocess_changelog_content
        cleaned_content = postprocess_changelog_content(cleaned_content)

        # Count completion tokens
        completion_tokens = count_tokens(cleaned_content, model)
        total_tokens = prompt_tokens + completion_tokens

        if not quiet:
            logger.info(f"Token usage: {prompt_tokens} prompt + {completion_tokens} completion = {total_tokens} total")

        return cleaned_content

    except Exception as e:
        logger.error(f"Failed to generate changelog entry: {e}")
        raise AIError.generation_error(f"Failed to generate changelog entry: {e}") from e


def _generate_with_retries(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    max_retries: int,
    quiet: bool = False,
) -> str:
    """Generate content with retry logic."""
    client = ai.Client()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    last_exception = None

    for attempt in range(max_retries):
        try:
            if not quiet and attempt > 0:
                logger.info(f"Retry attempt {attempt + 1}/{max_retries}")

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=120,  # Increase timeout to 120 seconds for larger prompts
            )

            content = response.choices[0].message.content
            if content:
                return content.strip()
            else:
                raise AIError.generation_error("Empty response from AI model")

        except Exception as e:
            last_exception = e
            error_type = _classify_error(e)

            if error_type in ["authentication", "model_not_found", "context_length", "sdk_error"]:
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


def _classify_error(error: Exception) -> str:
    """Classify an error for retry logic."""
    error_str = str(error).lower()

    if "authentication" in error_str or "unauthorized" in error_str or "api key" in error_str:
        return "authentication"
    elif "model" in error_str and ("not found" in error_str or "does not exist" in error_str):
        return "model_not_found"
    elif "context" in error_str and ("length" in error_str or "too long" in error_str):
        return "context_length"
    elif "rate limit" in error_str or "quota" in error_str:
        return "rate_limit"
    elif "timeout" in error_str:
        return "timeout"
    elif "cerebras.cloud.sdk" in error_str and "attribute" in error_str:
        return "sdk_error"
    else:
        return "unknown"
