from abc import ABC, abstractmethod

class LLMBaseClient(ABC):
    """
    Abstract base class for all LLM clients, ensuring a consistent interface.
    """

    @abstractmethod
    def get_completion(self, prompt: str, model: str) -> str | None:
        """
        Gets a completion from the specified LLM.

        Args:
            prompt: The prompt to send to the model.
            model: The specific model to use for the completion (e.g., 'llama3', 'gpt-4').

        Returns:
            The content of the completion, or None if no completion was generated.
        """
        pass
