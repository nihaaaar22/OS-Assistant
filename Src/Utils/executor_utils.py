import json
from typing import Optional

import re

def parse_tool_call(response: str) -> Optional[dict]:
    """
    Parses a tool call from the response, expecting it in a markdown JSON code block.
    Example:
    ```json
    {
        "tool_name": "tool_name",
        "input": {"arg": "value"}
    }
    ```
    """
    # Regex to find ```json ... ``` blocks
    # It captures the content within the fences.
    # re.DOTALL allows '.' to match newlines, which is crucial for multi-line JSON.
    match = re.search(r"```json\s*([\s\S]+?)\s*```", response, re.DOTALL)

    if match:
        json_str = match.group(1).strip()
        try:
            tool_call = json.loads(json_str)
            # Basic validation for the expected structure
            if isinstance(tool_call, dict) and "tool_name" in tool_call and "input" in tool_call:
                return tool_call
        except json.JSONDecodeError:
            # Invalid JSON within the markdown block
            return None
    return None
