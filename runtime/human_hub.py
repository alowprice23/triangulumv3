from typing import Dict, Any
import click

def request_human_feedback(bug_context: Dict[str, Any]) -> str:
    """
    Presents the current bug-fixing context to the human user and
    prompts for feedback or a hint.

    Args:
        bug_context: A dictionary containing information about the bug,
                     such as the failing tests and logs.

    Returns:
        A string containing the hint or suggestion from the user.
    """
    click.echo("\n" + "="*30)
    click.echo("      🤖 ASSISTANCE REQUESTED 🤖")
    click.echo("="*30)
    click.echo("The AI agent has failed to fix the bug within its budget and requires your help.")

    click.echo("\n--- Bug Context ---")
    failing_tests = bug_context.get("failing_tests", [])
    if failing_tests:
        click.echo(click.style("Failing Tests:", fg="yellow"))
        for test in failing_tests:
            click.echo(f"- {test}")

    logs = bug_context.get("logs", "No logs available.")
    click.echo(click.style("\nLogs:", fg="yellow"))
    click.echo(logs)

    click.echo("\n" + "="*30)
    click.echo("Please provide a hint or suggestion for the AI to continue.")
    click.echo("For example: 'Try adding a null check for the user object in the process_order function.'")

    hint = click.prompt("Your Hint")

    return hint
