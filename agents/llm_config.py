import logging
from api.llm_router import get_llm_client
from api.llm_base_client import LLMBaseClient

logger = logging.getLogger(__name__)

class LLMConfig:
    """
    Holds configuration for the LLM and provides a client instance via the router.

    This class is intended to be configured from a central config file in the future.
    """
    def __init__(self, provider: str = "openai", model_name: str = "gpt-3.5-turbo"):
        # In the future, these defaults will be loaded from config/defaults.toml
        self.provider = provider
        self.model_name = model_name
        self._client: LLMBaseClient | None = None
        logger.info(f"LLM configured for provider: '{self.provider}', model: '{self.model_name}'")

    def get_client(self) -> LLMBaseClient:
        """
        Returns a client to interact with the configured LLM provider.
        Initializes the client on the first call using the router.
        """
        if self._client is None:
            logger.info(f"Initializing LLM client for provider: {self.provider}")
            self._client = get_llm_client(self.provider)
        return self._client
