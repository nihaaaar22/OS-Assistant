#used for terminal logging with panels, colours etc for different types of messages

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.syntax import Syntax

import json

class TerminalInterface:
    def __init__(self):
        self.console = Console()
        # Markdown streaming attributes
        self.buffer = ""
        self.inside_code_block = False
        self.code_lang = ""
        self.code_buffer = ""
        self.inside_tool_call = False
        self.tool_call_buffer = ""
        # Shell command tracking attributes
        self.inside_shell_command = False
        self.shell_command_buffer = ""

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

      
        panel = Panel(
            Text(message, style="blue"),
            title=f"[bold green]{tool_name} Output[/bold green]",
            border_style="green"
        )
        self.console.print(panel)

    def process_markdown_chunk(self, chunk):
        """
        Process a chunk of markdown text, handling tool calls and regular markdown.
        Args:
        chunk (str): A piece of markdown text to process
        """
        self.buffer += chunk
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            line_stripped = line.strip()

            # Handle tool call opening delimiter - be more flexible with whitespace
            if "```json" in line_stripped:
                self.inside_tool_call = True
                self.tool_call_buffer = ""
                self.console.print("[bold cyan]Tool Call:[/bold cyan]")

            # Handle tool call closing delimiter - be more flexible with whitespace
            elif "```" in line_stripped and self.inside_tool_call:
                self.console.print(self.tool_call_buffer)
                # self.console.print(Syntax('{"status": "end_tool_call"}', "json", theme="monokai", line_numbers=False))
                self.console.print("[bold cyan]--------------------------------[/bold cyan]")
                self.inside_tool_call = False
                self.tool_call_buffer = ""

            # Handle content inside tool calls
            elif self.inside_tool_call:
                self.tool_call_buffer += line + "\n"

            # Regular markdown content
            else:
                self.console.print(Markdown(line))

    def flush_markdown(self):
        """
        Flush any remaining markdown content in the buffer.
        """
        if hasattr(self, 'inside_tool_call') and self.inside_tool_call:
            # Handle case where tool call is not properly terminated
            self.console.print(Syntax(self.tool_call_buffer.strip(), "json", theme="monokai", line_numbers=False))
            # self.console.print("[bold cyan]End Tool Call (forced)[/bold cyan]")
            self.inside_tool_call = False
        elif self.buffer:
            if "TASK_DONE" in self.buffer:
                self.console.print("━" * 80)  # Print a solid line
            else:
                self.console.print(Markdown(self.buffer))
        self.buffer = ""
        if hasattr(self, 'tool_call_buffer'):
            self.tool_call_buffer = ""

    