import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from Src.Tools.web_loader import load_data
from Src.Tools.web_search import web_search
#need to transform it into map of dictionary
#name : [function : xyz,description : blah bah]

tools_function_map = {
    "web_loader": load_data,
    "web_search": web_search
}



def call_tool(tool_name, tool_input):
    """
    Calls the appropriate tool function with the given input.
    
    Args:
        tool_name (str): Name of the tool to call
        tool_input (dict): Input parameters for the tool
    """
    if tool_name in tools_function_map:
        # Pass the tool_input dictionary as kwargs to the tool function
        return tools_function_map[tool_name](**tool_input)
    else:
        raise ValueError(f"Tool '{tool_name}' not found. Check the tools available in the tool directory")


# print(call_tool("web_loader","https://www.toastmasters.org"))
# print(call_tool("web_search","manus ai"))

    