import os
from openai import OpenAI

from typing import Dict

class OpenAIClient:
    """
    A wrapper for the OpenAI API client that includes a simple in-memory cache
    to avoid redundant API calls.
    """
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")

        self.cache: Dict[str, str] = {}

        try:
            self.client = OpenAI(api_key=self.api_key)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenAI client: {e}") from e

    def get_completion(self, prompt: str, model: str = "gpt-3.5-turbo") -> str | None:
        """
        Gets a completion from the specified OpenAI model, using a cache to
        avoid re-sending identical prompts.

        Args:
            prompt: The prompt to send to the model.
            model: The model to use for the completion.

        Returns:
            The content of the first choice in the completion, or None if no
            completion was generated.
        """
        # Create a cache key from the prompt and model
        cache_key = f"{model}::{prompt}"
        if cache_key in self.cache:
            print("LLM Client: Returning cached response.")
            return self.cache[cache_key]

        try:
            print("LLM Client: Making new API call.")
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that fixes bugs in code."},
                    {"role": "user", "content": prompt}
                ]
            )
            if response.choices:
                content = response.choices[0].message.content
                # Store the successful response in the cache
                self.cache[cache_key] = content
                return content
            return None
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None
