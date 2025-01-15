import sys
from Src.Tools.web_loader import load_data

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

tools_function_map = {
    "web_loader": load_data
}



def call_tool(tool_name, *args, **kwargs):
    if tool_name in tools_function_map:
        return tools_function_map[tool_name](*args, **kwargs)
    else:
        raise ValueError(f"Tool '{tool_name}' not found.")


# print(call_tool("web_loader","https://www.toastmasters.org"))
    