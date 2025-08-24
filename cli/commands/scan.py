import click
import json
from pathlib import Path
import networkx as nx

from discovery.code_graph import CodeGraphBuilder
from discovery.language_probe import probe_language
from adapters.router import get_language_adapter

class ExtendedEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, nx.DiGraph):
            return nx.readwrite.json_graph.node_link_data(obj)
        return super().default(obj)

@click.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, path_type=Path))
def scan(path: Path):
    """
    Scans a repository, builds a dependency graph, and generates a manifest.
    """
    try:
        # 1. Probe the language
        files = list(path.rglob("*.*"))
        language = probe_language(files)
        if language == "Unknown":
            click.echo("Could not determine the language of the repository.", err=True)
            return

        # 2. Get the language adapter
        adapter = get_language_adapter(language.lower())

        # 3. Build the code graph
        builder = CodeGraphBuilder(repo_root=path, adapter=adapter)
        code_graph = builder.build()

        # 4. Pretty print the JSON manifest
        click.echo(json.dumps(code_graph.dict(), indent=2, cls=ExtendedEncoder))

    except Exception as e:
        click.echo(f"An error occurred during scanning: {e}", err=True)
