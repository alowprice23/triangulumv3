import unittest
from unittest.mock import patch, MagicMock
import os

from api.llm_router import get_llm_client
from api.openai_client import OpenAIClient

class TestApiModule(unittest.TestCase):

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_llm_router_get_openai_client(self):
        """Test that the router returns an OpenAIClient for gpt models."""
        client = get_llm_client("gpt-4")
        self.assertIsInstance(client, OpenAIClient)

    def test_llm_router_unsupported_model(self):
        """Test that the router raises an error for unsupported models."""
        with self.assertRaises(ValueError):
            get_llm_client("unsupported-model-123")

    def test_openai_client_no_api_key(self):
        """Test that the client raises an error if the API key is not set."""
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        with self.assertRaises(ValueError):
            OpenAIClient()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("api.openai_client.OpenAI") # Correct patch target
    def test_openai_client_get_completion(self, mock_openai_class):
        """Test the get_completion method with a mocked API call."""
        mock_client_instance = MagicMock()
        mock_openai_class.return_value = mock_client_instance

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a test completion."
        mock_client_instance.chat.completions.create.return_value = mock_response

        client = OpenAIClient()
        completion = client.get_completion("test prompt")

        self.assertEqual(completion, "This is a test completion.")
        mock_client_instance.chat.completions.create.assert_called_once()

if __name__ == '__main__':
    unittest.main()
