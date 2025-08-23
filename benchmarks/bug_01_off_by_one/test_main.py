from main import count_items

def test_count_five_items():
  assert count_items([1, 2, 3, 4, 5]) == 5

def test_count_zero_items():
  assert count_items([]) == 0
