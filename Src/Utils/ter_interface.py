#used for terminal logging with panels, colours etc for different types of messages

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.syntax import Syntax
from yaspin import yaspin
import time

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

    def code_log(self, code: str):
        """
        Print a code snippet in a formatted panel.
        """
        panel = Panel(
            Syntax(code, "python", theme="monokai", line_numbers=True),
            title=f"[bold green]Code Snippet[/bold green]",
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
                # self.console.print("[bold cyan]Tool Call:[/bold cyan]")
                self.spinner = yaspin(text="Tool Call...", color="yellow")
                self.spinner.start()

            # Handle tool call closing delimiter - be more flexible with whitespace
            elif "```" in line_stripped and self.inside_tool_call:
                if hasattr(self, 'spinner'):
                    self.spinner.stop()
                    delattr(self, 'spinner')
                self._display_tool_call_content()
                self.console.print("[bold cyan]--------------------------------[/bold cyan]")
                self.inside_tool_call = False
                self.tool_call_buffer = ""

            # Handle content inside tool calls
            elif self.inside_tool_call:
                self.tool_call_buffer += line + "\n"

            # Regular markdown content
            else:
                self.console.print(Markdown(line))

    def _display_tool_call_content(self):
        """
        Parse and display tool call JSON content in a simple key-value format.
        """
        try:
            # Try to parse the JSON content
            json_content = json.loads(self.tool_call_buffer.strip())
            
            # Check if tool_name is execute_python_code or execute_shell_command
            if 'tool_name' in json_content and json_content['tool_name'] in ['execute_python_code', 'execute_shell_command']:
                return
            
            # Build content for the panel
            panel_content = ""
            for key, value in json_content.items():
                if isinstance(value, dict):
                    panel_content += f"{key}:\n"
                    for sub_key, sub_value in value.items():
                        panel_content += f"  {sub_key}: {sub_value}\n"
                else:
                    panel_content += f"{key}: {value}\n"
            
            # Create and display panel
            panel = Panel(
                panel_content.strip(),
                title="[yellow]Tool Call[/yellow]",
                border_style="blue"
            )
            self.console.print(panel)
        except json.JSONDecodeError:
            # If JSON parsing fails, display the raw content in a panel
            panel = Panel(
                self.tool_call_buffer.strip(),
                title="[bold red]Raw Tool Call Content[/bold red]",
                border_style="red"
            )
            self.console.print(panel)

    def flush_markdown(self):
        """
        Flush any remaining markdown content in the buffer.
        """
        if hasattr(self, 'inside_tool_call') and self.inside_tool_call:
            # Handle case where tool call is not properly terminated

            if hasattr(self, 'spinner'):
                self.spinner.stop()
                delattr(self, 'spinner')

            if self.tool_call_buffer.strip():
                self._display_tool_call_content()
            self.console.print("[bold cyan]--------------------------------[/bold cyan]")
            self.inside_tool_call = False
        elif self.buffer:
            if "TASK_DONE" in self.buffer:
                self.console.print("━" * 80)  # Print a solid line
            else:
                self.console.print(Markdown(self.buffer))
        self.buffer = ""
        if hasattr(self, 'tool_call_buffer'):
            self.tool_call_buffer = ""

    