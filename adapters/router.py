from typing import Dict, Type

from adapters.base_adapter import LanguageAdapter
from adapters.python import PythonAdapter
from adapters.javascript import JavaScriptAdapter

# A registry mapping language names to their adapter classes.
# This makes the router easily extensible.
ADAPTER_REGISTRY: Dict[str, Type[LanguageAdapter]] = {
    "python": PythonAdapter,
    "javascript": JavaScriptAdapter,
}

def get_language_adapter(language: str) -> LanguageAdapter:
    """
    Selects and returns a LanguageAdapter instance based on the language name.

    Args:
        language: The name of the language (e.g., "python").

    Returns:
        An instance of the appropriate LanguageAdapter.

    Raises:
        ValueError: If the language is not supported.
    """
    language = language.lower()

    adapter_class = ADAPTER_REGISTRY.get(language)
    if not adapter_class:
        raise ValueError(f"Unsupported language: '{language}'. Supported languages are: {list(ADAPTER_REGISTRY.keys())}")

    # Return a new instance of the adapter
    return adapter_class()
