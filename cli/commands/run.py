import click
from pathlib import Path

from runtime.supervisor import Supervisor

@click.command()
@click.option('--description', '-d', required=True, help='A description of the bug to be fixed.')
@click.option('--severity', '-s', type=int, default=5, help='The severity of the bug (1-10).')
@click.option('--duration', '-t', type=int, default=60, help='How long the supervisor should run (in seconds).')
@click.argument('path', type=click.Path(exists=True, file_okay=False, path_type=Path))
def run(description: str, severity: int, duration: int, path: Path):
    """
    Submits a bug to the runtime supervisor and starts its execution loop.
    """
    repo_root = path.resolve()

    # In a real application, the supervisor might be a long-running daemon.
    # Here, we instantiate and run it for a fixed duration.
    supervisor = Supervisor(max_concurrent_sessions=3, repo_root=repo_root)

    click.echo(f"Submitting bug to supervisor: '{description}'")
    supervisor.submit_bug(description, severity)

    click.echo(f"Starting supervisor for {duration} seconds...")
    supervisor.run(duration_seconds=duration)

    click.echo("Supervisor has finished its run.")
