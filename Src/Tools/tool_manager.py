from web_loader import load_data

tools_function_map = {
    "web_loader": load_data
}



def call_tool(tool_name, *args, **kwargs):
    if tool_name in tools_function_map:
        return tools_function_map[tool_name](*args, **kwargs)
    else:
        raise ValueError(f"Tool '{tool_name}' not found.")


print(call_tool("load_data","https://www.toastmasters.org"))
    