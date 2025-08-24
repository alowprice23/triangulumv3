from .main import process_data

def test_process_with_string():
  # This test will fail because it passes a string instead of a dict
  assert "Processed value: 123" in process_data("123")

def test_process_with_dict():
  assert "Processed value: 123" in process_data({"value": "123"})
