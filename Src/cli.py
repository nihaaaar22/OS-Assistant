import click
from OpenCopilot import OpenCopilot

@click.group(invoke_without_command=True)
@click.option('--task', '-t', help='The task to automate')
@click.option('--max-iter', '-m', default=10, help='Maximum number of iterations for the task')
@click.pass_context
def cli(ctx, task, max_iter):
    """TaskAutomator - Your AI Task Automation Tool"""
    copilot = OpenCopilot()
    if ctx.invoked_subcommand is None:
        if task:
            copilot.run_task(user_prompt=task, max_iter=max_iter)
        else:
            copilot.run()

@cli.command('list-tools')
def list_tools():
    """List all available automation tools"""
    tools = OpenCopilot.list_available_tools()
    click.echo("Available Tools:")
    for tool in tools:
        click.echo(f"- {tool['name']}: {tool['summary']}")
        if tool.get('arguments'):
            click.echo(f"    Arguments: {tool['arguments']}")

if __name__ == '__main__':
    cli() 