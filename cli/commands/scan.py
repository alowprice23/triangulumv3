import click
import json
from pathlib import Path

from discovery import run_discovery

@click.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, path_type=Path))
def scan(path: Path):
    """
    Scans a repository, builds a dependency graph, and generates a manifest.
    """
    try:
        manifest = run_discovery(str(path))

        # Pretty print the JSON manifest
        click.echo(json.dumps(manifest, indent=2))

    except Exception as e:
        click.echo(f"An error occurred during scanning: {e}", err=True)
