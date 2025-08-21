import difflib
import subprocess
from pathlib import Path
from typing import Dict, List

def create_patch_bundle(
    original_files: Dict[str, str],
    modified_files: Dict[str, str]
) -> Dict[str, str]:
    """
    Creates a bundle of patches by comparing original and modified file contents.

    Args:
        original_files: A dictionary mapping file paths to their original content.
        modified_files: A dictionary mapping file paths to their new content.

    Returns:
        A dictionary mapping file paths to their corresponding unified diff string
        in a git-compatible format.
    """
    patch_bundle = {}
    all_file_paths = set(original_files.keys()) | set(modified_files.keys())

    for file_path in all_file_paths:
        original_content = original_files.get(file_path, "")
        modified_content = modified_files.get(file_path, "")

        if original_content != modified_content:
            diff = difflib.unified_diff(
                original_content.splitlines(keepends=True),
                modified_content.splitlines(keepends=True),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
            )
            patch_bundle[file_path] = "".join(diff)

    return patch_bundle

def apply_patch_bundle(
    bundle: Dict[str, str],
    repo_root: Path
) -> Dict[str, str]:
    """
    Applies a bundle of patches to the files in a repository.

    Uses the `patch -p1` command-line tool.

    Args:
        bundle: A dictionary mapping file paths to their diffs.
        repo_root: The root directory of the repository.

    Returns:
        A dictionary with results, containing 'applied' and 'failed' patches.
    """
    results = {"applied": [], "failed": {}}

    for file_path_str, patch_content in bundle.items():
        if not patch_content:
            continue

        try:
            # The `patch` command reads from stdin by default.
            # -p1 strips the 'a/' and 'b/' prefixes from the file paths in the diff.
            process = subprocess.run(
                ["patch", "-p1"],
                input=patch_content,
                text=True,
                capture_output=True,
                check=False,
                cwd=repo_root,
            )

            if process.returncode == 0:
                results["applied"].append(file_path_str)
            else:
                # The file to be patched is inside the bundle, so we report
                # failure on the bundle, not a specific file.
                results["failed"][file_path_str] = process.stderr or process.stdout

        except FileNotFoundError:
            return {"error": "The 'patch' command is not installed or not in PATH."}
        except Exception as e:
            results["failed"][file_path_str] = str(e)

    return results
