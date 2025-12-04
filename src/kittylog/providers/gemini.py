"""Gemini provider implementation for kittylog."""

from typing import Any

from kittylog.providers.base_configured import GenericHTTPProvider, ProviderConfig
from kittylog.providers.error_handler import handle_provider_errors


class GeminiProvider(GenericHTTPProvider):
    """Gemini API provider with custom request/response handling."""

    def _build_headers(self) -> dict[str, str]:
        """Build headers with Google API key format."""
        headers = super()._build_headers()
        if self.api_key:
            headers["x-goog-api-key"] = self.api_key
            # Remove standard Authorization that might be added
            headers.pop("Authorization", None)
        return headers

    def _build_request_body(
        self, messages: list[dict], temperature: float, max_tokens: int, model: str, **kwargs
    ) -> dict[str, Any]:
        """Build Gemini-specific request body."""
        contents: list[dict[str, Any]] = []
        system_instruction_parts: list[dict[str, str]] = []

        for msg in messages:
            role = msg.get("role")
            content_value = msg.get("content")
            content = "" if content_value is None else str(content_value)

            if role == "system":
                if content.strip():
                    system_instruction_parts.append({"text": content})
                continue

            if role == "assistant":
                gemini_role = "model"
            elif role == "user":
                gemini_role = "user"
            else:
                from kittylog.errors import AIError

                raise AIError.model_error(f"Unsupported message role for Gemini API: {role}")

            contents.append({"role": gemini_role, "parts": [{"text": content}]})

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }

        if system_instruction_parts:
            payload["systemInstruction"] = {"role": "system", "parts": system_instruction_parts}

        return payload

    def _parse_response(self, response: dict[str, Any]) -> str:
        """Parse Gemini-specific response."""
        from kittylog.errors import AIError

        candidates = response.get("candidates")
        if not candidates:
            raise AIError.model_error("Gemini API response missing candidates")

        candidate = candidates[0]
        content_entry = candidate.get("content")
        if not isinstance(content_entry, dict):
            raise AIError.model_error("Gemini API response has invalid content structure")

        parts = content_entry.get("parts")
        if not isinstance(parts, list) or not parts:
            raise AIError.model_error("Gemini API response missing parts")

        for part in parts:
            if isinstance(part, dict):
                part_text = part.get("text")
                if isinstance(part_text, str) and part_text:
                    return part_text

        raise AIError.model_error("Gemini API response missing text content")

    def _get_api_url(self, model: str | None = None) -> str:
        """Get Gemini API URL with model."""
        if not model:
            raise ValueError("Model is required for Gemini")
        return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


# Create provider configuration - base_url is placeholder since we override _get_api_url
_gemini_config = ProviderConfig(
    name="Gemini",
    api_key_env="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com",  # Overridden in _get_api_url
)

# Create provider instance
gemini_provider = GeminiProvider(_gemini_config)


@handle_provider_errors("Gemini")
def call_gemini_api(model: str, messages: list[dict[str, Any]], temperature: float, max_tokens: int) -> str:
    """Call the Gemini API.

    Args:
        model: Model name
        messages: List of message dictionaries
        temperature: Temperature parameter
        max_tokens: Maximum tokens in response

    Returns:
        Generated text content

    Raises:
        AIError: For any API-related errors
    """
    return gemini_provider.generate(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
