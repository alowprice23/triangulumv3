import pytest
from pathlib import Path
from discovery.build_systems import detect_build_systems

@pytest.fixture
def project_root(tmp_path):
    d = tmp_path / "project"
    d.mkdir()
    return d

def test_detect_build_systems_npm(project_root):
    """Tests detection of npm."""
    (project_root / "package.json").touch()
    systems = detect_build_systems(project_root)
    assert "npm" in systems

def test_detect_build_systems_maven(project_root):
    """Tests detection of maven."""
    (project_root / "pom.xml").touch()
    systems = detect_build_systems(project_root)
    assert "maven" in systems

def test_detect_build_systems_multiple(project_root):
    """Tests detection of multiple build systems."""
    (project_root / "package.json").touch()
    (project_root / "requirements.txt").touch()
    systems = detect_build_systems(project_root)
    assert "npm" in systems
    assert "pip" in systems

def test_detect_build_systems_none(project_root):
    """Tests a project with no known build system files."""
    systems = detect_build_systems(project_root)
    assert not systems

def test_detect_build_systems_poetry(project_root):
    """Tests detection of poetry."""
    (project_root / "pyproject.toml").write_text("[tool.poetry]")
    systems = detect_build_systems(project_root)
    assert "poetry" in systems
