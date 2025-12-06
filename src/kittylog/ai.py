"""AI integration for changelog generation.

This module handles AI model integration for generating changelog entries from commit data.
Based on gac's AI module but specialized for changelog generation.
"""

from rich.console import Console
from rich.panel import Panel

from kittylog.ai_utils import generate_with_retries
from kittylog.config import load_config
from kittylog.constants import Limits
from kittylog.errors import AIError
from kittylog.prompt import build_changelog_prompt, clean_changelog_content
from kittylog.providers import PROVIDER_REGISTRY
from kittylog.utils import count_tokens
from kittylog.utils.logging import get_logger, log_error, log_info

logger = get_logger(__name__)


def generate_changelog_entry(
    commits: list[dict],
    tag: str,
    from_boundary: str | None = None,
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
    context_entries: str = "",
    detail_level: str = "normal",
) -> tuple[str, dict[str, int]]:
    """Generate a changelog entry using AI.

    Args:
        commits: List of commit dictionaries
        tag: The target tag/version
        from_boundary: The previous boundary (for context)
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
        context_entries: Pre-formatted string of preceding changelog entries for style reference

    Returns:
        Generated changelog content
    """
    # Load config inside function to avoid module-level loading
    config = load_config()

    if model is None:
        model_value = config.model
        if not model_value:
            raise AIError.model_error("No model specified. Please configure a model.")
        model = str(model_value)

    if temperature is None:
        temperature = config.temperature
    if max_tokens is None:
        max_tokens = config.max_output_tokens
    if max_retries is None:
        max_retries = config.max_retries

    # Build the prompt
    system_prompt, user_prompt = build_changelog_prompt(
        commits=commits,
        tag=tag,
        from_boundary=from_boundary,
        hint=hint,
        boundary_mode=boundary_mode,
        language=language,
        translate_headings=translate_headings,
        audience=audience,
        context_entries=context_entries,
        detail_level=detail_level,
    )

    # Add diff content to user prompt if available, but limit its size to prevent timeouts
    if diff_content:
        # Limit diff content to prevent extremely large prompts
        if len(diff_content) > Limits.MAX_DIFF_LENGTH:
            diff_content = diff_content[: Limits.MAX_DIFF_LENGTH] + "\n\n... (diff content truncated for brevity)"
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
    log_info(
        logger,
        "Generating changelog entry",
        tag=tag or "unreleased",
        commit_count=len(commits),
        model=model,
        prompt_tokens=prompt_tokens,
    )

    # Generate the changelog content
    try:
        content = generate_with_retries(
            provider_funcs=PROVIDER_REGISTRY,
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
            log_info(
                logger,
                "Changelog generation successful",
                tag=tag or "unreleased",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )

        token_usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }
        return cleaned_content, token_usage

    except (AIError, ValueError, TypeError, RuntimeError) as e:
        log_error(
            logger,
            "Changelog generation failed",
            tag=tag or "unreleased",
            error_type=type(e).__name__,
            error_message=str(e),
        )
        raise AIError.generation_error(f"Failed to generate changelog entry: {e}") from e
    except Exception as e:
        # Re-raise system exceptions that should never be caught
        if isinstance(e, (KeyboardInterrupt, SystemExit, GeneratorExit)):
            raise
        # Wrap other unexpected exceptions
        log_error(
            logger,
            "Changelog generation failed",
            tag=tag or "unreleased",
            error_type=type(e).__name__,
            error_message=str(e),
        )
        raise AIError.generation_error(f"Unexpected error: {e}") from e
        log_error(
            logger,
            "Changelog generation failed",
            tag=tag or "unreleased",
            error_type=type(e).__name__,
            error_message=str(e),
        )
        raise AIError.generation_error(f"Failed to generate changelog entry: {e}") from e
