import click
from pathlib import Path

from agents.coordinator import Coordinator

@click.command()
@click.option('--description', '-d', required=True, help='A description of the bug to be fixed.')
@click.argument('path', type=click.Path(exists=True, file_okay=False, path_type=Path))
def run(description: str, path: Path):
    """
    Runs the full automated debugging cycle on a repository.
    """
    repo_root = path.resolve()
    coordinator = Coordinator(repo_root=repo_root)
    initial_scope = [str(p.resolve().relative_to(repo_root)) for p in path.glob("**/*.py")]
    result = coordinator.run_debugging_cycle(description, initial_scope)

    if result.get("status") == "success":
        click.echo("Result: Bug Fixed Successfully!")
    else:
        click.echo(f"Result: Bug fix failed. Reason: {result.get('reason', 'Unknown')}")
