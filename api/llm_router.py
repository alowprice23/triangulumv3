from typing import Any

from api.openai_client import OpenAIClient

def get_llm_client(model_name: str) -> Any:
    """
    Selects and returns an LLM client based on the model name.

    Args:
        model_name: The name of the model (e.g., "gpt-4", "gpt-3.5-turbo").

    Returns:
        An instance of the appropriate LLM client.

    Raises:
        ValueError: If the model_name is not supported.
    """
    if model_name.startswith("gpt-"):
        # In a more complex system, we might have different client classes
        # for different providers (Anthropic, Google, etc.)
        return OpenAIClient()

    # Add other models/providers here in the future
    # elif "claude" in model_name:
    #     return AnthropicClient()

    raise ValueError(f"Unsupported LLM model: {model_name}")
