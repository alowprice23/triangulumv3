"""
tests/unit/test_environment.py

This test file is designed to help debug the test environment itself.
It prints out key information about the Python environment that pytest is using.
"""

import sys
import os
import importlib

def test_environment_details():
    """Prints environment details to help diagnose import issues."""
    print("\n\n" + "="*50)
    print("PYTHON ENVIRONMENT DIAGNOSTICS")
    print("="*50)

    print(f"sys.executable: {sys.executable}")
    print(f"sys.version: {sys.version}")
    print("\nsys.path:")
    for p in sys.path:
        print(f"  - {p}")

    print("\nPYTHONPATH environment variable:")
    print(f"  - {os.getenv('PYTHONPATH', 'Not Set')}")

    print("\nChecking for key packages:")
    packages_to_check = ["fastapi", "click", "networkx", "docker", "openai", "requests", "tomli", "pathspec", "chromadb"]
    for pkg in packages_to_check:
        try:
            module = importlib.import_module(pkg)
            print(f"  - Found '{pkg}' at: {module.__file__}")
        except ImportError:
            print(f"  - Could not find '{pkg}'")

    print("="*50 + "\n\n")

    # This assertion will always fail, but that's okay.
    # The purpose of this test is to print the diagnostics.
    assert True
