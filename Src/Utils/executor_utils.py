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
