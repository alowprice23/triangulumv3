def process_data(data):
  """Processes data, expecting a dictionary. Fails on other types."""
  # Bug: Assumes data is always a dict with 'value'
  return f"Processed value: {data['value']}"
