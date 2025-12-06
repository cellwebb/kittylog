"""Replicate API provider for kittylog."""

import os
import time

import httpx

from kittylog.errors import AIError
from kittylog.providers.base import GenericHTTPProvider, ProviderConfig


class ReplicateProvider(GenericHTTPProvider):
    """Replicate API provider with async prediction handling."""

    config = ProviderConfig(
        name="Replicate",
        api_key_env="REPLICATE_API_TOKEN",
        base_url="https://api.replicate.com",
        path="/v1/predictions",
    )

    def _build_headers(self) -> dict[str, str]:
        """Build headers with Replicate token format."""
        headers = super()._build_headers()
        if self.api_key:
            headers["Authorization"] = f"Token {self.api_key}"
            # Remove standard Authorization that might be added differently
            if "Bearer" in headers.get("Authorization", ""):
                headers.pop("Authorization")
        return headers

    def _build_request_body(
        self, messages: list[dict], temperature: float, max_tokens: int, model: str, **kwargs
    ) -> dict:
        """Build Replicate prediction request body."""
        # Convert messages to a single prompt for Replicate
        prompt_parts = []
        system_message = None

        for message in messages:
            role = message.get("role")
            content = message.get("content", "")

            if role == "system":
                system_message = content
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        # Add system message at the beginning if present
        if system_message:
            prompt_parts.insert(0, f"System: {system_message}")

        # Add final assistant prompt
        prompt_parts.append("Assistant:")
        full_prompt = "\n\n".join(prompt_parts)

        # Replicate prediction payload
        return {
            "version": model,  # Replicate uses version string as model identifier
            "input": {
                "prompt": full_prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        }

    def _get_api_url(self, model: str | None = None) -> str:
        """Get Replicate prediction URL."""
        base = self.config.base_url.rstrip("/")
        path = self.config.path if self.config.path is not None else "/v1/predictions"
        return f"{base}{path}"

    def _make_http_request(self, url: str, body: dict, headers: dict[str, str]) -> dict:
        """Override to handle Replicate's async prediction workflow."""
        try:
            # Create prediction
            response = httpx.post(url, json=body, headers=headers, timeout=self.config.timeout)
            response.raise_for_status()
            prediction_data = response.json()

            # Get the prediction URL to check status
            get_url = f"https://api.replicate.com/v1/predictions/{prediction_data['id']}"

            # Poll for completion (Replicate predictions are async)
            max_wait_time = 120
            wait_interval = 2
            elapsed_time = 0

            while elapsed_time < max_wait_time:
                get_response = httpx.get(get_url, headers=headers, timeout=self.config.timeout)
                get_response.raise_for_status()
                status_data = get_response.json()

                if status_data["status"] == "succeeded":
                    return {"content": status_data["output"]}
                elif status_data["status"] == "failed":
                    raise AIError.model_error(
                        f"Replicate prediction failed: {status_data.get('error', 'Unknown error')}"
                    )
                elif status_data["status"] in ["starting", "processing"]:
                    time.sleep(wait_interval)
                    elapsed_time += wait_interval
                else:
                    raise AIError.model_error(f"Replicate API returned unknown status: {status_data['status']}")

            raise AIError.timeout_error("Replicate API prediction timed out")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise AIError.rate_limit_error(f"Replicate API rate limit exceeded: {e.response.text}") from e
            elif e.response.status_code == 401:
                raise AIError.authentication_error(f"Replicate API authentication failed: {e.response.text}") from e
            raise AIError.model_error(f"Replicate API error: {e.response.status_code} - {e.response.text}") from e
        except httpx.TimeoutException as e:
            raise AIError.timeout_error(f"Replicate API request timed out: {e!s}") from e
        except Exception as e:
            raise AIError.model_error(f"Error calling Replicate API: {e!s}") from e

    def _parse_response(self, response: dict) -> str:
        """Parse Replicate response."""
        content = response.get("content")
        if not content:
            raise AIError.model_error("Replicate API returned empty content")
        return content

    def _get_api_key(self) -> str:
        """Override to use REPLICATE_API_TOKEN instead of standard pattern."""
        api_key = os.getenv("REPLICATE_API_TOKEN")
        if not api_key:
            raise AIError.authentication_error("REPLICATE_API_TOKEN not found in environment variables")
        return api_key
