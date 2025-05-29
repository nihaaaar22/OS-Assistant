import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from Tools.web_loader import load_data
from Tools.web_search import web_search
from Tools.file_task import file_reader, file_maker, file_writer, directory_maker
from Tools.system_details import get_os_details, get_datetime, get_memory_usage, get_cpu_info
from Tools.userinp import get_user_input

#need to transform it into map of dictionary
#name : [function : xyz,description : blah bah]

tools_function_map = {
    "web_loader": load_data,
    "web_search": web_search,
    "file_maker": file_maker,
    "file_reader":file_reader,
    "directory_maker":directory_maker,
    "file_writer":file_writer,
    "get_os_details": get_os_details,
    "get_datetime": get_datetime,
    "get_memory_usage": get_memory_usage,
    "get_cpu_info": get_cpu_info,
    "get_user_input": get_user_input
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
# print(call_tool("web_loader",{"url":"https://www.toastmasters.org"}))
# print(call_tool("file_reader",{"file_path":"/Users/niharshettigar/Web Dev Projects/Jsprograms/Arrays.js"}))



    