#used for terminal logging with panels, colours etc for different types of messages

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import json

class TerminalInterface:
    def __init__(self):
        self.console = Console()

    def tool_output_log(self, message: str, tool_name: str = "Tool"):
        """
        Print a tool output message in a formatted panel.
        
        Args:
            message (str): The message to display
            tool_name (str): Name of the tool generating the output
        """
        # Convert message to string if it's not already
        if isinstance(message, dict):
            message = json.dumps(message, indent=2)
        elif not isinstance(message, str):
            message = str(message)

        # Original code:
        # panel = Panel(
        #     Text(message, style="orange"),
        #     title=f"[bold green]{tool_name} Output[/bold green]",
        #     border_style="green"
        # )
        panel = Panel(
            Text(message, style="on blue"),
            title=f"[bold green]{tool_name} Output[/bold green]",
            border_style="green"
        )
        self.console.print(panel)

