from pathlib import Path
import click

from agents.coordinator import Coordinator

def start_debugging_session(repo_path: Path, bug_description: str):
    """
    Initializes and runs the agentic debugging session.

    Args:
        repo_path: The path to the repository to be debugged.
        bug_description: The user's description of the bug.
    """
    click.secho("Initializing agentic debugging session...", fg="cyan")

    try:
        coordinator = Coordinator(repo_root=repo_path)
        result = coordinator.run_debugging_cycle(bug_description=bug_description)

        click.secho("\n--- Debugging Session Complete ---", fg="cyan")

        if result.get("status") == "success":
            click.secho("Result: Bug Fixed Successfully!", fg="green")
            click.echo("\nLLM Rationale:")
            click.echo(result.get("llm_rationale", "Not provided."))

            patch_bundle = result.get("patch_bundle", {})
            if patch_bundle:
                click.secho("\nProposed Patch:", fg="yellow")
                for file_path, patch_content in patch_bundle.items():
                    click.secho(f"--- {file_path} ---", fg="yellow")
                    click.echo(patch_content)
        else:
            click.secho(f"Result: {result.get('status', 'unknown').upper()}", fg="red")
            click.echo(f"Reason: {result.get('reason', 'No reason provided.')}")

    except Exception as e:
        click.secho(f"A critical error occurred: {e}", fg="red")
