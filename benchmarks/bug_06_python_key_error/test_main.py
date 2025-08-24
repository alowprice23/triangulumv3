from main import get_config_value
import pytest

def test_get_existing_key():
  config = {"user": "admin"}
  assert get_config_value(config, "user") == "Value is admin"

def test_get_missing_key():
  config = {"user": "admin"}
  # This test will fail with a KeyError
  assert get_config_value(config, "host") == "Value is default"
