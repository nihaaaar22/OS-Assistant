import json
from typing import Optional

def parse_tool_call(response: str) -> Optional[dict]:
    """
    Parses a tool call from the response.
    """
    if "<<TOOL_CALL>>" in response and "<<END_TOOL_CALL>>" in response:
        tool_call_str = response.split("<<TOOL_CALL>>")[1].split("<<END_TOOL_CALL>>")[0].strip()
        try:
            tool_call = json.loads(tool_call_str)
            return tool_call
        except json.JSONDecodeError:
            return None
    return None

def parse_code(response: str) -> Optional[str]:
    """
    Parses code from the response.
    """
    if "<<CODE>>" in response and "<<CODE>>" in response: # There was a typo in the original file, it checked for <<CODE>> twice
        code = response.split("<<CODE>>")[1].split("<<CODE>>")[0].strip()
        return code
    return None

def parse_shell_command(response: str) -> Optional[str]:
    """
    Parses a shell command from the response.
    """
    if "<<SHELL_COMMAND>>" in response and "<<END_SHELL_COMMAND>>" in response:
        shell_command = response.split("<<SHELL_COMMAND>>")[1].split("<<END_SHELL_COMMAND>>")[0].strip()
        return shell_command
    return None
