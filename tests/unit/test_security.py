import unittest
from security.scanner import scan_for_malicious_code

class TestSecurityScanner(unittest.TestCase):

    def test_no_threat_found(self):
        """Tests that safe code passes the scan."""
        safe_code = "def my_function(a, b):\n    return a + b"
        self.assertIsNone(scan_for_malicious_code(safe_code))

    def test_network_access_threat(self):
        """Tests detection of network access patterns."""
        malicious_code = "import socket\ns = socket.socket()"
        result = scan_for_malicious_code(malicious_code)
        self.assertIsNotNone(result)
        self.assertIn("Network Access", result)

    def test_file_write_threat(self):
        """Tests detection of file writing patterns."""
        malicious_code = "with open('some_file.txt', 'w') as f:\n    f.write('pwned')"
        result = scan_for_malicious_code(malicious_code)
        self.assertIsNotNone(result)
        self.assertIn("File System Write", result)

    def test_subprocess_threat(self):
        """Tests detection of subprocess execution."""
        malicious_code = "import os\nos.system('rm -rf /')"
        result = scan_for_malicious_code(malicious_code)
        self.assertIsNotNone(result)
        self.assertIn("Subprocess Execution", result)

    def test_dynamic_execution_threat(self):
        """Tests detection of eval/exec."""
        malicious_code = "exec('print(\"hello\")')"
        result = scan_for_malicious_code(malicious_code)
        self.assertIsNotNone(result)
        self.assertIn("Dynamic Execution", result)

if __name__ == '__main__':
    unittest.main()
