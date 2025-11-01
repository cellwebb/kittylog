"""AI integration for changelog generation.

This module handles AI model integration for generating changelog entries from commit data.
Based on gac's AI module but specialized for changelog generation.
"""

import logging

from rich.console import Console
from rich.panel import Panel

from kittylog.ai_utils import generate_with_retries
from kittylog.config import load_config
from kittylog.constants import EnvDefaults
from kittylog.errors import AIError
from kittylog.prompt import build_changelog_prompt, clean_changelog_content
from kittylog.providers import (
    call_anthropic_api,
    call_cerebras_api,
    call_chutes_api,
    call_custom_anthropic_api,
    call_custom_openai_api,
    call_deepseek_api,
    call_fireworks_api,
    call_gemini_api,
    call_groq_api,
    call_lmstudio_api,
    call_minimax_api,
    call_mistral_api,
    call_ollama_api,
    call_openai_api,
    call_openrouter_api,
    call_streamlake_api,
    call_synthetic_api,
    call_together_api,
    call_zai_api,
    call_zai_coding_api,
)
from kittylog.utils import count_tokens

logger = logging.getLogger(__name__)
config = load_config()


def classify_error(error: Exception) -> str:
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
    else:
        return "unknown"


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
    boundary_mode: str = "tags",
    language: str | None = None,
    translate_headings: bool = False,
    audience: str | None = None,
) -> tuple[str, dict[str, int]]:
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
        language: Optional override language for the generated changelog
        translate_headings: Whether to translate section headings into the selected language
        audience: Target audience slug controlling tone and emphasis

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
        boundary_mode=boundary_mode,
        language=language,
        translate_headings=translate_headings,
        audience=audience,
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

    # Provider functions mapping
    provider_funcs = {
        "anthropic": call_anthropic_api,
        "cerebras": call_cerebras_api,
        "chutes": call_chutes_api,
        "custom-anthropic": call_custom_anthropic_api,
        "custom-openai": call_custom_openai_api,
        "deepseek": call_deepseek_api,
        "fireworks": call_fireworks_api,
        "gemini": call_gemini_api,
        "groq": call_groq_api,
        "lm-studio": call_lmstudio_api,
        "minimax": call_minimax_api,
        "mistral": call_mistral_api,
        "ollama": call_ollama_api,
        "openai": call_openai_api,
        "openrouter": call_openrouter_api,
        "streamlake": call_streamlake_api,
        "synthetic": call_synthetic_api,
        "together": call_together_api,
        "zai": call_zai_api,
        "zai-coding": call_zai_coding_api,
    }

    # Generate the changelog content
    try:
        content = generate_with_retries(
            provider_funcs=provider_funcs,
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            quiet=quiet,
        )

        # Clean and format the content
        # Preserve version header for unreleased changes (when tag is None)
        preserve_version_header = tag is None
        cleaned_content = clean_changelog_content(content, preserve_version_header)

        # Count completion tokens
        completion_tokens = count_tokens(cleaned_content, model)
        total_tokens = prompt_tokens + completion_tokens

        if not quiet:
            logger.info(f"Token usage: {prompt_tokens} prompt + {completion_tokens} completion = {total_tokens} total")

        token_usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }
        return cleaned_content, token_usage

    except Exception as e:
        logger.error(f"Failed to generate changelog entry: {e}")
        raise AIError.generation_error(f"Failed to generate changelog entry: {e}") from e
