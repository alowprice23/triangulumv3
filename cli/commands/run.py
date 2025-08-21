import click
from pathlib import Path

from cli.agentic_router import start_debugging_session

@click.command()
@click.option('--description', '-d', required=True, help='A description of the bug to be fixed.')
@click.argument('path', type=click.Path(exists=True, file_okay=False, path_type=Path))
def run(description: str, path: Path):
    """
    Runs the full automated debugging cycle on a repository.
    """
    start_debugging_session(repo_path=path, bug_description=description)
