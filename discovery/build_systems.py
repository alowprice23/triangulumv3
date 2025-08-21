from pathlib import Path
from typing import List, Dict

BUILD_SYSTEM_FILES: Dict[str, List[str]] = {
    "npm": ["package.json"],
    "yarn": ["yarn.lock"],
    "pnpm": ["pnpm-lock.yaml"],
    "maven": ["pom.xml"],
    "gradle": ["build.gradle", "build.gradle.kts"],
    "pip": ["requirements.txt", "setup.py"],
    "poetry": ["pyproject.toml"],
    "cmake": ["CMakeLists.txt"],
    "make": ["Makefile"],
}

def detect_build_systems(project_root: Path) -> List[str]:
    """
    Detects the build systems used in a project based on the presence of
    specific configuration files.

    :param project_root: The root directory of the project.
    :return: A list of detected build system names.
    """
    if not project_root.is_dir():
        raise ValueError("Project root must be a directory.")

    detected_systems = []
    for system, files in BUILD_SYSTEM_FILES.items():
        for file in files:
            if (project_root / file).is_file():
                detected_systems.append(system)
                break  # Move to the next system once one of its files is found

    return detected_systems
