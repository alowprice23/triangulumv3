from typing import Dict, Type

from api.llm_base_client import LLMBaseClient
from api.llm_clients import OpenAIClient, OllamaClient

# A registry mapping provider names to their client classes.
# This makes the router easily extensible.
PROVIDER_REGISTRY: Dict[str, Type[LLMBaseClient]] = {
    "openai": OpenAIClient,
    "ollama": OllamaClient,
    # Add new providers here, e.g., "anthropic": AnthropicClient
}

# A cache for client instances to avoid re-initializing them.
_client_instances: Dict[str, LLMBaseClient] = {}

def get_llm_client(provider: str) -> LLMBaseClient:
    """
    Selects and returns an LLM client instance based on the provider name.
    Uses a cache to ensure a single instance per provider.

    Args:
        provider: The name of the LLM provider (e.g., "openai", "ollama").

    Returns:
        An instance of the appropriate LLM client.

    Raises:
        ValueError: If the provider is not supported.
    """
    provider = provider.lower()

    if provider in _client_instances:
        return _client_instances[provider]

    client_class = PROVIDER_REGISTRY.get(provider)
    if not client_class:
        raise ValueError(f"Unsupported LLM provider: '{provider}'. Supported providers are: {list(PROVIDER_REGISTRY.keys())}")

    instance = client_class()
    _client_instances[provider] = instance

    return instance
