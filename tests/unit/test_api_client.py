import unittest
from unittest.mock import patch, MagicMock
import os

from api.openai_client import OpenAIClient

class TestOpenAIClient(unittest.TestCase):

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_llm_caching(self):
        """
        Tests that the OpenAIClient caches responses for identical prompts.
        """
        client = OpenAIClient()

        # Mock the actual API call method within the client instance
        mock_completion_create = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "This is a test response."
        mock_completion_create.return_value.choices = [mock_choice]
        client.client.chat.completions.create = mock_completion_create

        prompt = "This is a test prompt."
        model = "test-model"

        # First call - should call the API
        response1 = client.get_completion(prompt, model=model)

        # Second call with same prompt - should use cache
        response2 = client.get_completion(prompt, model=model)

        # Assertions
        self.assertEqual(response1, "This is a test response.")
        self.assertEqual(response2, "This is a test response.")

        # The underlying API should only have been called once
        mock_completion_create.assert_called_once()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_cache_differentiates_by_model(self):
        """
        Tests that the cache key includes the model name.
        """
        client = OpenAIClient()

        mock_completion_create = MagicMock()
        client.client.chat.completions.create = mock_completion_create

        prompt = "This is a test prompt."

        # First call with model 1
        client.get_completion(prompt, model="model-1")

        # Second call with model 2
        client.get_completion(prompt, model="model-2")

        # The API should have been called twice, once for each model
        self.assertEqual(mock_completion_create.call_count, 2)

if __name__ == '__main__':
    unittest.main()
