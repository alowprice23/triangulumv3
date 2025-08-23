import click
import os

# To allow the CLI to be run from anywhere and still find the project modules,
# we might need to adjust the Python path.
# For now, we assume it's run from the project root.

from cli.commands.scan import scan
from cli.commands.run import run
from cli.commands.interactive import interactive_session

@click.group()
def cli():
    """
    Triangulum: An AI-powered debugging assistant.
    """
    pass

cli.add_command(scan)
cli.add_command(run)
cli.add_command(interactive_session)

if __name__ == '__main__':
    # This allows the script to be run directly for debugging
    # e.g., python cli/main.py scan .
    cli()
