import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from Tools.web_loader import load_data
from Tools.web_search import web_search
from Tools.file_task import file_reader, file_maker, file_writer, directory_maker
from Tools.system_details import get_os_details, get_datetime, get_memory_usage, get_cpu_info
from Tools.userinp import get_user_input
from Env.python_executor import PythonExecutor
from Env.shell import ShellExecutor
from Utils.ter_interface import TerminalInterface

#need to transform it into map of dictionary
#name : [function : xyz,description : blah bah]

terminal = TerminalInterface()



def execute_python_code_tool(code: str) -> str:
    """ 
    Prompts for confirmation, then executes the given Python code and returns a formatted result string.
    """
    terminal.code_log(code)
    user_confirmation = input(f"Do you want to execute this Python code snippet?\n(y/n): ")
    if user_confirmation.lower() != 'y':
        return "User chose not to execute the Python code."
    executor = PythonExecutor()
    result = executor.execute(code)
    if result['output'] == "" and not result['success']:
        error_msg = (
            f"Python execution failed.\n"
            f"Error: {result.get('error', 'Unknown error')}"
        )
        return error_msg
    elif result['output'] == "":
        no_output_msg = (
            "Python execution completed but no output was produced. "
            "Ensure your code includes print() statements to show results."
        )
        return no_output_msg
    else:
        if result['success']:
            return f"Program Output:\n{result['output']}"
        else:
            return f"Program Output:\n{result['output']}\nError: {result.get('error', 'Unknown error')}"

def execute_shell_command_tool(command: str) -> str:
    """
    Prompts for confirmation, then executes the given shell command and returns a formatted result string.
    """
    terminal.code_log(command)
    user_confirmation = input(f"Do you want to execute the shell command? (y/n): ")
    if user_confirmation.lower() != 'y':
        return "User chose not to execute the shell command."
    executor = ShellExecutor()
    result = executor.execute(command)
    if result['output'] == "":
        if result['success']:
            return "Shell command executed successfully with no output."
        else:
            return f"Shell command executed with no output, but an error occurred: {result.get('error', 'Unknown error')}"
    else:
        if result['success']:
            return f"Command Output:\n{result['output']}"
        else:
            return f"Command Output:\n{result['output']}\nError: {result.get('error', 'Unknown error')}"

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
    else: raise ValueError(f"This tool is invalid. Please check the tools available in the tool directory")
    
        

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
    "get_user_input": get_user_input,
    "execute_python_code": execute_python_code_tool,
    "execute_shell_command": execute_shell_command_tool,
}

# print(call_tool("web_loader","https://www.toastmasters.org"))
# print(call_tool("web_search","manus ai"))
# print(call_tool("web_loader",{"url":"https://www.toastmasters.org"}))
# print(call_tool("file_reader",{"file_path":"/Users/niharshettigar/Web Dev Projects/Jsprograms/Arrays.js"}))



    