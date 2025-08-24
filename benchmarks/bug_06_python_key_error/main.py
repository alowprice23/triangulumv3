def get_config_value(config, key):
  """
  This function gets a value from a config dictionary.
  The bug is that it doesn't handle the case where the key does not exist.
  """
  return f"Value is {config[key]}"
