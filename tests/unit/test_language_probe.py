import pytest
from pathlib import Path
from discovery.language_probe import probe_language

def test_probe_language_single():
    """Tests probing a single language project."""
    files = [Path("file1.py"), Path("file2.py")]
    assert probe_language(files) == "Python"

def test_probe_language_mix():
    """Tests probing a mixed language project."""
    files = [
        Path("file1.py"),
        Path("file2.js"),
        Path("file3.js"),
        Path("style.css"),
    ]
    assert probe_language(files) == "JavaScript"

def test_probe_language_empty():
    """Tests probing an empty list of files."""
    assert probe_language([]) == "Unknown"

def test_probe_language_unknown():
    """Tests probing a project with unknown file extensions."""
    files = [Path("file1.foo"), Path("file2.bar")]
    assert probe_language(files) == "Unknown"

def test_probe_language_with_header():
    """Tests that C/C++ headers are handled."""
    files = [Path("main.c"), Path("utils.h")]
    assert probe_language(files) == "C/C++"

    files_cpp = [Path("main.cpp"), Path("utils.h")]
    assert probe_language(files_cpp) == "C++"

    files_mixed = [Path("a.c"), Path("b.h"), Path("c.h")]
    assert probe_language(files_mixed) == "C/C++"
