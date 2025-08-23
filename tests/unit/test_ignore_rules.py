import pytest
from pathlib import Path
from discovery.ignore_rules import IgnoreRules

@pytest.fixture
def project_root(tmp_path):
    d = tmp_path / "project"
    d.mkdir()
    return d

def test_ignore_rules_default_patterns(project_root):
    """Tests that default ignore patterns are loaded."""
    ignore_rules = IgnoreRules(project_root=project_root)
    assert ".git/" in ignore_rules.get_patterns()

def test_ignore_rules_gitignore(project_root):
    """Tests loading of .gitignore file."""
    (project_root / ".gitignore").write_text("*.log\n/temp_dir/")
    ignore_rules = IgnoreRules(project_root=project_root)
    assert "*.log" in ignore_rules.get_patterns()
    assert "/temp_dir/" in ignore_rules.get_patterns()

def test_ignore_rules_triangulumignore(project_root):
    """Tests loading of .triangulumignore file."""
    (project_root / ".triangulumignore").write_text("*.tmp\n/results/")
    ignore_rules = IgnoreRules(project_root=project_root)
    assert "*.tmp" in ignore_rules.get_patterns()
    assert "/results/" in ignore_rules.get_patterns()

def test_is_ignored(project_root):
    """Tests the is_ignored method."""
    (project_root / ".gitignore").write_text("*.log\n/temp_dir/\n.env")
    ignore_rules = IgnoreRules(project_root=project_root)
    assert ignore_rules.is_ignored(Path("file.log"))
    assert ignore_rules.is_ignored(Path("temp_dir/some_file.txt"))
    assert ignore_rules.is_ignored(Path(".env"))
    assert not ignore_rules.is_ignored(Path("src/main.py"))

def test_is_ignored_with_defaults(project_root):
    """Tests the is_ignored method with default patterns."""
    ignore_rules = IgnoreRules(project_root=project_root)
    assert ignore_rules.is_ignored(Path(".git/config"))
    assert ignore_rules.is_ignored(Path("build/output.bin"))
    assert not ignore_rules.is_ignored(Path("my_important_file.txt"))
