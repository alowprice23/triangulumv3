import os
import logging
from typing import Dict

from openai import OpenAI
import ollama

from api.llm_base_client import LLMBaseClient

logger = logging.getLogger(__name__)

class OpenAIClient(LLMBaseClient):
    """
    A wrapper for the OpenAI API client that includes a simple in-memory cache.
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

    def get_completion(self, prompt: str, model: str) -> str | None:
        cache_key = f"{model}::{prompt}"
        if cache_key in self.cache:
            logger.info("OpenAI Client: Returning cached response.")
            return self.cache[cache_key]

        try:
            logger.info(f"OpenAI Client: Making new API call to model '{model}'.")
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert software engineer AI that fixes bugs in code."},
                    {"role": "user", "content": prompt}
                ]
            )
            if response.choices:
                content = response.choices[0].message.content
                self.cache[cache_key] = content
                return content
            return None
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return None


class OllamaClient(LLMBaseClient):
    """
    A client for interacting with a local Ollama service.
    """
    def __init__(self, host: str = "http://localhost:11434"):
        self.client = ollama.Client(host=host)
        self.cache: Dict[str, str] = {}
        logger.info(f"Ollama Client initialized for host: {host}")

    def get_completion(self, prompt: str, model: str) -> str | None:
        cache_key = f"{model}::{prompt}"
        if cache_key in self.cache:
            logger.info("Ollama Client: Returning cached response.")
            return self.cache[cache_key]

        try:
            logger.info(f"Ollama Client: Making new API call to model '{model}'.")
            response = ollama.chat(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert software engineer AI that fixes bugs in code."},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response['message']['content']
            self.cache[cache_key] = content
            return content
        except Exception as e:
            logger.error(f"Error calling Ollama API: {e}")
            return None
