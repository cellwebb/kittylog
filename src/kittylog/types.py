#!/usr/bin/env python3
"""Error classification utilities to break circular imports.

This module only contains what's actually needed to avoid circular
import issues between ai.py and ai_utils.py.
"""


def classify_error(error: Exception) -> str:
    """Classify an error for retry logic.

    Extracted from ai.py to break circular imports between ai and ai_utils.
    This is the single purpose of this module.

    Args:
        error: Exception to classify

    Returns:
        Error classification string for retry logic:
        - 'authentication', 'model_not_found', 'context_length',
        - 'rate_limit', 'timeout', or 'unknown'
    """
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
