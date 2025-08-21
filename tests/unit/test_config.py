import pytest
import tomli
import yaml
from pathlib import Path

def test_defaults_toml_parsable():
    """Tests that config/defaults.toml is a valid TOML file."""
    config_path = Path("config/defaults.toml")
    assert config_path.is_file()
    with open(config_path, "rb") as f:
        try:
            data = tomli.load(f)
            assert isinstance(data, dict)
            assert "pid" in data
            assert "caps" in data
            assert "safe_mode" in data
        except tomli.TOMLDecodeError as e:
            pytest.fail(f"Failed to parse config/defaults.toml: {e}")

def test_language_rules_toml_parsable():
    """Tests that config/language_rules.toml is a valid TOML file."""
    config_path = Path("config/language_rules.toml")
    assert config_path.is_file()
    with open(config_path, "rb") as f:
        try:
            data = tomli.load(f)
            assert isinstance(data, dict)
            assert "python" in data
            assert "javascript" in data
            assert "java" in data
        except tomli.TOMLDecodeError as e:
            pytest.fail(f"Failed to parse config/language_rules.toml: {e}")

def test_security_yaml_parsable():
    """Tests that config/security.yaml is a valid YAML file."""
    config_path = Path("config/security.yaml")
    assert config_path.is_file()
    with open(config_path, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
            assert isinstance(data, dict)
            assert "key_policy" in data
            assert "path_sandbox" in data
        except yaml.YAMLError as e:
            pytest.fail(f"Failed to parse config/security.yaml: {e}")

def test_ignore_defaults_readable():
    """Tests that config/ignore.defaults can be read."""
    config_path = Path("config/ignore.defaults")
    assert config_path.is_file()
    try:
        content = config_path.read_text(encoding="utf-8")
        assert ".git/" in content
        assert "node_modules/" in content
    except Exception as e:
        pytest.fail(f"Failed to read config/ignore.defaults: {e}")
