"""
Adapter for handling Java-specific project conventions.
"""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import networkx as nx

from adapters.base_adapter import LanguageAdapter

# --- Adapter Implementation ---

class JavaAdapter(LanguageAdapter):
    """
    An adapter for analyzing Java codebases (primarily Maven and Gradle projects).
    """

    def map_source_to_test(self, source_file: str, all_tests: List[str]) -> Optional[str]:
        """
        Maps a Java source file to its corresponding test file.
        e.g., 'src/main/java/com/mypackage/MyClass.java' -> 'src/test/java/com/mypackage/MyClassTest.java'
        """
        source_path = Path(source_file)
        if "src/main/java" not in str(source_path):
            return None # Not a standard Maven/Gradle source file

        # Construct the expected test file path
        test_file_path_str = str(source_path).replace("src/main/java", "src/test/java").replace(".java", "Test.java")

        # Check if this exact test file exists
        if test_file_path_str in all_tests:
            return test_file_path_str

        return None

    def get_test_command(self, test_targets: List[str]) -> str:
        """
        Generates a test command for a Java project (Maven or Gradle).
        """
        # Determine the class name from the file path, e.g., '.../MyClassTest.java' -> 'MyClassTest'
        # This is a simplification; a real implementation needs the full package name.
        test_class_names = [Path(t).stem for t in test_targets]
        tests_str = ",".join(test_class_names)

        # Detect build tool
        if Path("pom.xml").exists():
            # Maven command
            return f"mvn test -Dtest={tests_str}"
        elif Path("build.gradle").exists() or Path("build.gradle.kts").exists():
            # Gradle command
            test_flags = " ".join([f"--tests {name}" for name in test_class_names])
            return f"gradle test {test_flags}"

        return f"echo 'No pom.xml or build.gradle found. Could not determine test command.'"

    def build_symbol_index(self, repo_root: Path, file_paths: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Builds a simplified symbol index for Java files using regex.
        """
        index = {}
        # Regex for: class Name, interface Name, method signatures
        symbol_pattern = re.compile(r"^(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:class|interface|enum)\s+(\w+)|(?:public|private|protected)?\s*\w+\s+(\w+)\s*\(", re.MULTILINE)

        for file_str in file_paths:
            if not file_str.endswith(".java"):
                continue

            file_path = repo_root / file_str
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    content = f.read()

                symbols = []
                for match in symbol_pattern.finditer(content):
                    name = match.group(1) or match.group(2)
                    if name:
                        symbols.append({
                            "name": name,
                            "type": "class/interface" if match.group(1) else "method",
                            "start_line": content.count('\\n', 0, match.start()) + 1,
                        })
                if symbols:
                    index[file_str] = symbols
            except Exception:
                continue
        return index

    def build_dependency_graph(self, symbol_index: Dict[str, List[Dict[str, Any]]], file_paths: List[str]) -> nx.DiGraph:
        """
        Constructs a dependency graph for Java modules based on imports.
        This is highly simplified.
        """
        graph = nx.DiGraph()
        for file_path in file_paths:
            graph.add_node(file_path)

        # Create a map from class name to file path for quick lookups
        class_to_file = {}
        for file_path in file_paths:
            if file_path.endswith(".java"):
                class_to_file[Path(file_path).stem] = file_path

        import_pattern = re.compile(r"^import\s+(?:static\s+)?([\w\.\*]+);", re.MULTILINE)

        for source_file in file_paths:
            if not source_file.endswith(".java"):
                continue

            try:
                with open(source_file, "r", encoding="utf-8") as f:
                    content = f.read()

                imports = import_pattern.findall(content)
                for imp in imports:
                    # Attempt to resolve the import to a file in the project
                    imported_class = imp.split('.')[-1]
                    if imported_class in class_to_file:
                        target_file = class_to_file[imported_class]
                        if source_file != target_file:
                            graph.add_edge(source_file, target_file)
            except Exception:
                continue
        return graph
