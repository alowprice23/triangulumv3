import pytest
from pathlib import Path
from discovery.ignore_rules import IgnoreRules
from discovery.repo_scanner import scan_repo

@pytest.fixture
def project_with_files(tmp_path):
    d = tmp_path / "project"
    d.mkdir()
    (d / "file1.txt").write_text("hello")
    (d / "file2.log").write_text("log")
    sub = d / "subdir"
    sub.mkdir()
    (sub / "file3.py").write_text("print('hello')")
    (d / ".gitignore").write_text("*.log")
    return d

def test_scan_repo(project_with_files):
    """Tests scanning a repository with some files and ignored files."""
    ignore_rules = IgnoreRules(project_with_files)
    files = scan_repo(project_with_files, ignore_rules)

    file_names = {f.name for f in files}

    assert "file1.txt" in file_names
    assert "file3.py" in file_names
    assert ".gitignore" in file_names
    assert "file2.log" not in file_names
    assert len(files) == 3

def test_scan_repo_empty(tmp_path):
    """Tests scanning an empty repository."""
    d = tmp_path / "project"
    d.mkdir()
    ignore_rules = IgnoreRules(d)
    files = scan_repo(d, ignore_rules)
    assert not files

def test_scan_repo_non_existent():
    """Tests scanning a non-existent repository."""
    with pytest.raises(ValueError):
        scan_repo(Path("/non/existent/path"), IgnoreRules(Path("/non/existent/path")))
