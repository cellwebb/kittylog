"""Claude Code provider implementation.

This provider allows users with Claude Code subscriptions to use their OAuth tokens
instead of paying for the expensive Anthropic API.
"""

import logging
import os

import httpx

from kittylog.errors import AIError
from kittylog.providers.base import AnthropicCompatibleProvider, ProviderConfig

logger = logging.getLogger(__name__)


class ClaudeCodeProvider(AnthropicCompatibleProvider):
    """Claude Code API provider with OAuth token handling and re-authentication."""

    config = ProviderConfig(
        name="Claude Code",
        api_key_env="CLAUDE_CODE_ACCESS_TOKEN",
        base_url="https://api.anthropic.com",
        # Uses default path: /v1/messages
    )

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    def _build_headers(self) -> dict[str, str]:
        """Build headers with Claude Code OAuth Bearer token and beta header."""
        headers = super()._build_headers()
        # Claude Code uses Bearer token instead of x-api-key
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers.pop("x-api-key", None)  # Remove Anthropic-style header
        headers["anthropic-beta"] = "oauth-2025-04-20"
        return headers

    def _build_request_body(
        self, messages: list[dict], temperature: float, max_tokens: int, model: str, **kwargs
    ) -> dict:
        """Build Claude Code request body with specific system message requirements."""
        # Convert messages to Anthropic format
        anthropic_messages = []
        system_instructions = ""

        for msg in messages:
            if msg["role"] == "system":
                system_instructions = msg["content"]
            else:
                anthropic_messages.append({"role": msg["role"], "content": msg["content"]})

        # Claude Code requires this exact system message, nothing more
        system_message = "You are Claude Code, Anthropic's official CLI for Claude."

        # Move any system instructions into the first user message
        if system_instructions and anthropic_messages:
            # Prepend system instructions to the first user message
            first_user_msg = anthropic_messages[0]
            first_user_msg["content"] = f"{system_instructions}\n\n{first_user_msg['content']}"

        data = {
            "model": model,  # Use the actual model parameter passed in
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "system": system_message,
        }

        return data

    def _make_http_request(self, url: str, body: dict, headers: dict[str, str]) -> dict:
        """Override to handle Claude Code OAuth re-authentication on 401 errors."""
        try:
            response = httpx.post(url, json=body, headers=headers, timeout=self.config.timeout)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                # Authentication failed - attempt to re-authenticate
                logger.warning("Claude Code authentication failed (401). Attempting re-authentication...")

                try:
                    from kittylog.oauth.claude_code import prompt_for_reauth
                except ImportError as import_error:
                    # OAuth module not available, just raise the original error
                    raise e from import_error

                # Try to re-authenticate
                if prompt_for_reauth():
                    # Re-authentication succeeded, retry the API call once
                    logger.info("Re-authentication successful, retrying API call...")

                    # Get the new token
                    new_access_token = os.getenv("CLAUDE_CODE_ACCESS_TOKEN")
                    if new_access_token:
                        # Update headers with new token
                        headers["Authorization"] = f"Bearer {new_access_token}"

                        try:
                            # Retry the request
                            response = httpx.post(url, json=body, headers=headers, timeout=self.config.timeout)
                            response.raise_for_status()
                            return response.json()
                        except Exception as retry_error:
                            logger.error(f"Retry after re-authentication failed: {retry_error}")
                            raise AIError.authentication_error(
                                f"Claude Code authentication still failing after re-authentication: {retry_error}"
                            ) from retry_error

                # Re-authentication failed or was declined
                raise AIError.authentication_error(
                    f"Claude Code authentication failed: {e.response.text}. "
                    "Your token may have expired. Please re-authenticate using 'kittylog config reauth'."
                ) from e
            else:
                # Re-raise other HTTP errors
                raise

    def _parse_response(self, response: dict) -> str:
        """Parse Claude Code response with validation."""
        content = super()._parse_response(response)

        if content is None:
            raise AIError.model_error("Claude Code API returned null content")
        if content == "":
            raise AIError.model_error("Claude Code API returned empty content")

        return content

    def _get_api_key(self) -> str:
        """Get Claude Code OAuth access token."""
        access_token = os.getenv("CLAUDE_CODE_ACCESS_TOKEN")
        if not access_token:
            raise AIError.authentication_error(
                "CLAUDE_CODE_ACCESS_TOKEN not found in environment variables. "
                "Please authenticate with Claude Code using 'kittylog init' or 'kittylog config' and set this token."
            )
        return access_token
