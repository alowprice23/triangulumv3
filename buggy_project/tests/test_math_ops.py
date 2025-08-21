from ..math_ops import add

def test_add_positive_numbers():
    assert add(2, 2) == 4

def test_add_negative_numbers():
    assert add(-1, -1) == -1
