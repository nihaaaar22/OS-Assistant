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

    if not match:
        # Check if there's an opening backtick but no closing one
        match = re.search(r"```json\s*([\s\S]+)", response, re.DOTALL)

    if match:
                
        json_str = match.group(1).strip()
        # Use regex to replace triple quotes with double quotes, ensuring a colon precedes the first backtick
        json_str = re.sub(r':\s*"""(.*?)"""', r': "\1"', json_str, flags=re.DOTALL)
        try:
            tool_call = json.loads(json_str)
            # Basic validation for the expected structure
            if isinstance(tool_call, dict) and "tool_name" in tool_call and "input" in tool_call:
                return tool_call
        except json.JSONDecodeError as e:
            # Invalid JSON within the markdown block
            raise e
    return None
