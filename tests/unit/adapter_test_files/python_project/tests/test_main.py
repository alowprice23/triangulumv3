# This test file imports the source file, which is the strongest link.
from src.app.main import hello

def test_hello():
    assert hello() == "world"
