from main import get_last_element
import pytest

def test_get_last_element_with_items():
  assert get_last_element([1, 2, 3]) == 3

def test_get_last_element_with_empty_list():
  # This test will fail with an IndexError
  assert get_last_element([]) is None
