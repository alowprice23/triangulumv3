from typing import Dict, Any
import click

def request_human_feedback(bug_context: Dict[str, Any]) -> str:
    """
    Presents the current bug-fixing context to the human user and
    prompts for feedback or a hint.

    Args:
        bug_context: A dictionary containing information about the bug,
                     such as the failing tests, logs, and last failed patch.

    Returns:
        A string containing the hint or suggestion from the user.
    """
    click.echo("\n" + "="*50)
    click.echo(click.style("      🤖 HUMAN INTERVENTION REQUIRED 🤖", fg="yellow", bold=True))
    click.echo("="*50)
    click.echo("The agent has been unable to fix the bug automatically and needs your guidance.")

    click.echo(click.style("\n--- Bug Summary ---", fg="cyan"))
    failing_tests = bug_context.get("failing_tests", [])
    if failing_tests:
        click.echo(click.style("Failing Tests:", bold=True))
        for test in failing_tests:
            click.echo(f"  - {test}")

    logs = bug_context.get("logs", "No logs available.")
    click.echo(click.style("\nOriginal Error Log:", bold=True))
    click.echo(click.style(logs, fg="red"))

    last_patch = bug_context.get("last_failed_patch")
    if last_patch:
        click.echo(click.style("\n--- Last Attempted Patch (failed) ---", fg="cyan"))
        click.echo(last_patch)

    click.echo("\n" + "="*50)
    click.echo(click.style("Please provide a hint for the next attempt.", fg="green"))
    click.echo("Example: 'The error might be in how the 'total' is calculated. Check for off-by-one errors.'")
    click.echo("You can also type 'skip' to let the agent try again without a hint, or 'quit' to abort.")

    hint = click.prompt(click.style("Your Hint", bold=True))

    return hint
