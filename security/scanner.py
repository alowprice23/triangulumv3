import re
from typing import Dict, Optional

# A simple set of heuristics to detect potentially malicious code patterns.
# This is not exhaustive and can be expanded significantly.
SUSPICIOUS_PATTERNS = {
    "Network Access": re.compile(r"import\s+socket|import\s+requests|import\s+urllib|from\s+urllib"),
    "File System Write": re.compile(r"open\s*\(\s*.*(w|a|x)"),
    "Subprocess Execution": re.compile(r"import\s+subprocess|from\s+subprocess|import\s+os|os\.system|os\.popen"),
    "Environment Variable Access": re.compile(r"os\.environ"),
    "Dynamic Execution": re.compile(r"eval\s*\(|exec\s*\("),
}

def scan_for_malicious_code(code: str) -> Optional[str]:
    """
    Scans a string of code for potentially malicious patterns.

    Args:
        code: The code content to scan.

    Returns:
        A string describing the detected threat, or None if no threats
        are found.
    """
    for threat_type, pattern in SUSPICIOUS_PATTERNS.items():
        if pattern.search(code):
            return f"Potential security risk detected: {threat_type}"

    return None
