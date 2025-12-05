"""OAuth authentication modules for kittylog."""

from .claude_code import (
    authenticate_and_save,
    get_token_storage_path,
    load_stored_token,
    perform_oauth_flow,
    prompt_for_reauth,
    save_token,
)
from .qwen_oauth import QwenDeviceFlow, QwenOAuthProvider
from .token_store import OAuthToken, TokenStore

__all__ = [
    "OAuthToken",
    "QwenDeviceFlow",
    "QwenOAuthProvider",
    "TokenStore",
    "authenticate_and_save",
    "get_token_storage_path",
    "load_stored_token",
    "perform_oauth_flow",
    "prompt_for_reauth",
    "save_token",
]
