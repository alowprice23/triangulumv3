import unittest
from tooling.compress import compress_text

class TestCompress(unittest.TestCase):

    def test_no_compression_needed(self):
        text = "This is a short text."
        compressed = compress_text(text, max_tokens=100)
        self.assertEqual(text, compressed)

    def test_simple_truncation(self):
        text = "This is a very long text that needs to be truncated because it exceeds the token limit."
        compressed = compress_text(text, max_tokens=5) # Approx 20 chars
        self.assertTrue(len(compressed) < len(text))
        self.assertTrue(compressed.endswith("... (truncated)"))

    def test_preserves_head_and_tail(self):
        lines = [f"Line {i}" for i in range(100)]
        text = "\n".join(lines)
        # Increased budget to be more realistic for this amount of text
        compressed = compress_text(text, max_tokens=100)

        self.assertIn("Line 0", compressed)
        self.assertIn("Line 1", compressed)
        self.assertIn("Line 98", compressed)
        self.assertIn("Line 99", compressed)
        self.assertIn("...", compressed)

    def test_preserves_important_keywords(self):
        # Shortened the unimportant lines to be more realistic
        lines = [f"INFO: line {i}" for i in range(50)]
        lines.insert(25, "ERROR: Something went wrong here.")
        lines.insert(30, "Exception: NullPointerException")
        text = "\n".join(lines)

        # Increased budget
        compressed = compress_text(text, max_tokens=150)

        self.assertIn("ERROR: Something went wrong", compressed)
        self.assertIn("Exception: NullPointerException", compressed)
        self.assertIn("INFO: line 49", compressed) # Check tail is present
        self.assertIn("...", compressed)

    def test_empty_text(self):
        text = ""
        compressed = compress_text(text, max_tokens=100)
        self.assertEqual(text, compressed)

if __name__ == '__main__':
    unittest.main()
