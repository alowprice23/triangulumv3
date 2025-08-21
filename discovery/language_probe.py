from pathlib import Path
from typing import List, Dict
from collections import Counter

# A simple mapping of file extensions to languages.
# This can be extended to support more languages.
EXTENSION_TO_LANGUAGE = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C/C++",
    ".h": "C/C++",
    ".hpp": "C++",
    ".hxx": "C++",
    ".hh": "C++",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".json": "JSON",
    ".md": "Markdown",
    ".sh": "Shell",
    ".yml": "YAML",
    ".yaml": "YAML",
}

def probe_language(files: List[Path]) -> str:
    """
    Detects the primary language of a project based on file extensions.

    :param files: A list of file paths in the project.
    :return: The name of the primary language, or "Unknown" if it cannot be determined.
    """
    if not files:
        return "Unknown"

    language_counts = Counter(
        EXTENSION_TO_LANGUAGE.get(file.suffix.lower())
        for file in files
        if file.suffix.lower() in EXTENSION_TO_LANGUAGE
    )

    if not language_counts:
        return "Unknown"

    primary_language, _ = language_counts.most_common(1)[0]
    return primary_language
