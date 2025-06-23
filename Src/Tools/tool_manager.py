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

def verify_tool_input(tool_name, tool_input):
    """
    Verifies that tool_input contains all required arguments for the tool as specified in tool_dir.json.
    Raises ValueError if any required argument is missing or if unexpected arguments are provided.
    """
    tool_dir_path = os.path.join(os.path.dirname(__file__), 'tool_dir.json')
    with open(tool_dir_path, 'r') as f:
        tools = json.load(f)
    tool_spec = next((tool for tool in tools if tool['name'] == tool_name), None)
    if not tool_spec:
        raise ValueError(f"Tool '{tool_name}' not found in tool_dir.json.")
    required_args = set(tool_spec.get('arguments', {}).keys())
    provided_args = set(tool_input.keys())
    # Check for missing required arguments (ignore optional ones if specified in doc) 
    missing_args = [
        arg for arg in required_args
        if arg not in provided_args and
        not 'optional' in tool_spec.get('arguments', {}).get(arg, {})
        
    ]
    if missing_args:
        raise ValueError(f"Missing required arguments for tool '{tool_name}': {missing_args}")
    # Optionally, check for unexpected arguments
    unexpected_args = [arg for arg in provided_args if arg not in required_args]
    if unexpected_args:
        raise ValueError(f"Unexpected arguments for tool '{tool_name}': {unexpected_args}")
    return True

def call_tool(tool_name, tool_input):
    """
    Calls the appropriate tool function with the given input after verifying input parameters.
    Args:
        tool_name (str): Name of the tool to call
        tool_input (dict): Input parameters for the tool
    """
    verify_tool_input(tool_name, tool_input)
    if tool_name in tools_function_map:
        # Pass the tool_input dictionary as kwargs to the tool function
        return tools_function_map[tool_name](**tool_input)
    else:
        raise ValueError(f"This tool is invalid. Please check the tools available in the tool directory")
    
        

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


if __name__ == "__main__":
    # Test file_writer without the optional 'append' argument
    test_file_path = "test_output.txt"
    test_content = "This is a test."
    try:
        result = call_tool("get_user_input", {"prompt":"hi user"})
        print(f"file_writer result: {result}")
    except Exception as e:
        print(f"Error: {e}")



    