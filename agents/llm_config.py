from typing import Any

from api.llm_router import get_llm_client

class LLMConfig:
    """
    Holds configuration for the LLM and provides a client instance.
    """
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.model_name = model_name
        self.temperature = 0.1
        self.stop_tokens = ["```"]
        self._client = None

    def get_client(self) -> Any:
        """
        Returns a client to interact with the configured LLM.
        Initializes the client on the first call.
        """
        if self._client is None:
            print(f"Initializing LLM client for model: {self.model_name}")
            self._client = get_llm_client(self.model_name)
        return self._client
