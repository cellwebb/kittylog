"""AI provider implementations for changelog generation."""

from .anthropic import call_anthropic_api
from .azure_openai import call_azure_openai_api
from .cerebras import call_cerebras_api
from .chutes import call_chutes_api
from .claude_code import call_claude_code_api
from .custom_anthropic import call_custom_anthropic_api
from .custom_openai import call_custom_openai_api
from .deepseek import call_deepseek_api
from .fireworks import call_fireworks_api
from .gemini import call_gemini_api
from .groq import call_groq_api
from .kimi_coding import call_kimi_coding_api
from .lmstudio import call_lmstudio_api
from .minimax import call_minimax_api
from .mistral import call_mistral_api
from .moonshot import call_moonshot_api
from .ollama import call_ollama_api
from .openai import call_openai_api
from .openrouter import call_openrouter_api
from .protocol import ProviderFunction, ProviderProtocol, validate_provider
from .replicate import call_replicate_api
from .streamlake import call_streamlake_api
from .synthetic import call_synthetic_api
from .together import call_together_api
from .zai import call_zai_api, call_zai_coding_api

# Provider registry - single source of truth for all providers
PROVIDER_REGISTRY = {
    "anthropic": call_anthropic_api,
    "azure-openai": call_azure_openai_api,
    "cerebras": call_cerebras_api,
    "chutes": call_chutes_api,
    "claude-code": call_claude_code_api,
    "custom-anthropic": call_custom_anthropic_api,
    "custom-openai": call_custom_openai_api,
    "deepseek": call_deepseek_api,
    "fireworks": call_fireworks_api,
    "gemini": call_gemini_api,
    "groq": call_groq_api,
    "kimi-coding": call_kimi_coding_api,
    "lm-studio": call_lmstudio_api,
    "minimax": call_minimax_api,
    "mistral": call_mistral_api,
    "moonshot": call_moonshot_api,
    "ollama": call_ollama_api,
    "openai": call_openai_api,
    "openrouter": call_openrouter_api,
    "replicate": call_replicate_api,
    "streamlake": call_streamlake_api,
    "synthetic": call_synthetic_api,
    "together": call_together_api,
    "zai": call_zai_api,
    "zai-coding": call_zai_coding_api,
}

# List of supported provider names - derived from registry keys
SUPPORTED_PROVIDERS = sorted(PROVIDER_REGISTRY.keys())

# API keys and environment variables for all providers - single source of truth
PROVIDER_ENV_VARS = {
    "anthropic": ["ANTHROPIC_API_KEY"],
    "azure-openai": ["AZURE_OPENAI_API_KEY"],
    "cerebras": ["CEREBRAS_API_KEY"],
    "chutes": ["CHUTES_API_KEY", "CHUTES_BASE_URL"],
    "claude-code": ["CLAUDE_CODE_ACCESS_TOKEN"],
    "custom-anthropic": ["CUSTOM_ANTHROPIC_API_KEY", "CUSTOM_ANTHROPIC_BASE_URL", "CUSTOM_ANTHROPIC_VERSION"],
    "custom-openai": ["CUSTOM_OPENAI_API_KEY", "CUSTOM_OPENAI_BASE_URL"],
    "deepseek": ["DEEPSEEK_API_KEY"],
    "fireworks": ["FIREWORKS_API_KEY"],
    "gemini": ["GEMINI_API_KEY"],
    "groq": ["GROQ_API_KEY"],
    "kimi-coding": ["KIMI_CODING_API_KEY"],
    "lm-studio": ["LMSTUDIO_API_KEY", "LMSTUDIO_API_URL"],
    "minimax": ["MINIMAX_API_KEY"],
    "mistral": ["MISTRAL_API_KEY"],
    "moonshot": ["MOONSHOT_API_KEY"],
    "ollama": ["OLLAMA_API_URL", "OLLAMA_HOST"],
    "openai": ["OPENAI_API_KEY"],
    "openrouter": ["OPENROUTER_API_KEY"],
    "replicate": ["REPLICATE_API_KEY", "REPLICATE_API_TOKEN"],
    "streamlake": ["STREAMLAKE_API_KEY", "VC_API_KEY"],
    "synthetic": ["SYNTHETIC_API_KEY", "SYN_API_KEY"],
    "together": ["TOGETHER_API_KEY"],
    "zai": ["ZAI_API_KEY"],
    "zai-coding": ["ZAI_API_KEY"],
}

# All API keys that should be exported to environment
ALL_API_KEYS = sorted({var for vars_list in PROVIDER_ENV_VARS.values() for var in vars_list})

__all__ = [
    "ALL_API_KEYS",
    "PROVIDER_ENV_VARS",
    "PROVIDER_REGISTRY",
    "SUPPORTED_PROVIDERS",
    "ProviderFunction",
    "ProviderProtocol",
    "call_anthropic_api",
    "call_azure_openai_api",
    "call_cerebras_api",
    "call_chutes_api",
    "call_claude_code_api",
    "call_custom_anthropic_api",
    "call_custom_openai_api",
    "call_deepseek_api",
    "call_fireworks_api",
    "call_gemini_api",
    "call_groq_api",
    "call_kimi_coding_api",
    "call_lmstudio_api",
    "call_minimax_api",
    "call_mistral_api",
    "call_moonshot_api",
    "call_ollama_api",
    "call_openai_api",
    "call_openrouter_api",
    "call_replicate_api",
    "call_streamlake_api",
    "call_synthetic_api",
    "call_together_api",
    "call_zai_api",
    "call_zai_coding_api",
    "validate_provider",
]
