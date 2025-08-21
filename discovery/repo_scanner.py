from pathlib import Path
from typing import List
from discovery.ignore_rules import IgnoreRules

def scan_repo(project_root: Path, ignore_rules: IgnoreRules) -> List[Path]:
    """
    Scans a repository and returns a list of all files that are not ignored.

    :param project_root: The root directory of the repository to scan.
    :param ignore_rules: An IgnoreRules object containing the ignore patterns.
    :return: A list of paths to the files that are not ignored.
    """
    if not project_root.is_dir():
        raise ValueError("Project root must be a directory.")

    all_files = []
    for path in project_root.rglob("*"):
        if path.is_file():
            relative_path = path.relative_to(project_root)
            if not ignore_rules.is_ignored(relative_path):
                all_files.append(path)

    return all_files
