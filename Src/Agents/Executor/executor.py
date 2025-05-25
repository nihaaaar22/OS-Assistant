# the change in this executor is the the tasks will not be iterated in a for loop and execution will not be done one by one
# instead it would be asked what is the next course of action

import os
import sys
import json
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from Src.Utils.ter_interface import TerminalInterface

from typing import Optional
from mistralai.models.sdkerror import SDKError # This might be an issue if LiteLLM doesn't use SDKError
                                              # LiteLLM maps exceptions to OpenAI exceptions.
                                              # We'll keep it for now and see if errors arise during testing.
from Src.Env import python_executor
from Src.Env.shell import ShellExecutor # Import ShellExecutor
from Src.llm_interface.llm import LiteLLMInterface # Import LiteLLMInterface

from Src.Tools import tool_manager

class RateLimiter:
    def __init__(self, wait_time: float = 5.0, max_retries: int = 3):
        self.wait_time = wait_time
        self.max_retries = max_retries
        self.last_call_time = None

    def wait_if_needed(self):
        if self.last_call_time is not None:
            elapsed = time.time() - self.last_call_time
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
        self.last_call_time = time.time()

class executor:
    def __init__(self, user_prompt, max_iter=10):
        self.user_prompt = user_prompt
        self.max_iter = max_iter
        self.rate_limiter = RateLimiter(wait_time=5.0, max_retries=3)
        self.executor_prompt_init()  # Update system_prompt
        self.python_executor = python_executor.PythonExecutor()  # Initialize PythonExecutor
        self.shell_executor = ShellExecutor() # Initialize ShellExecutor
        self.message = [{"role": "system", "content": self.system_prompt}]
        self.terminal = TerminalInterface()
        self.initialize_llm()

    def initialize_llm(self):
        # Directly instantiate LiteLLMInterface. 
        # It handles its own configuration loading (including model_name from config.json).
        self.llm = LiteLLMInterface()

    def get_tool_dir(self):
        # Get the absolute path to the project root directory
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
        tool_dir_path = os.path.join(project_root, 'Src', 'Tools', 'tool_dir.json')
        with open(tool_dir_path, "r") as file:
            return file.read()

    def parse_tool_call(self, response):
        if "<<TOOL_CALL>>" in response and "<<END_TOOL_CALL>>" in response:
            try:
                start_index = response.find("<<TOOL_CALL>>") + len("<<TOOL_CALL>>")
                end_index = response.find("<<END_TOOL_CALL>>")
                json_str = response[start_index:end_index].strip()
                return json.loads(json_str)#this returns python dictionary
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Error parsing JSON: {e}")
                return None
        return None

    def parse_code(self, response):
        """Extracts Python code from the response between <<CODE>> delimiters."""
        if "<<CODE>>" in response:
            try:
                start_index = response.find("<<CODE>>") + len("<<CODE>>")
                end_index = response.find("<<CODE>>", start_index)
                if end_index != -1:
                    code_str = response[start_index:end_index].strip()
                    return code_str
                else:
                    print("Error: Could not find both code delimiters in response")
                    return None
            except Exception as e:
                print(f"Error parsing code: {e}")
                return None
        return None

    def parse_shell_command(self, response):
        """Extracts shell commands from the response between <<SHELL_COMMAND>> delimiters."""
        if "<<SHELL_COMMAND>>" in response:
            try:
                start_index = response.find("<<SHELL_COMMAND>>") + len("<<SHELL_COMMAND>>")
                end_index = response.find("<<END_SHELL_COMMAND>>", start_index)
                if end_index != -1:
                    shell_command_str = response[start_index:end_index].strip()
                    return shell_command_str
                else:
                    print("Error: Could not find both shell command delimiters in response")
                    return None
            except Exception as e:
                print(f"Error parsing shell command: {e}")
                return None
        return None

    def executor_prompt_init(self):
        # Load tools details when initializing prompt
        tools_details = self.get_tool_dir()

        with open(os.path.join(os.path.dirname(__file__), '../../../config.json'), "r") as config_file:
            config = json.load(config_file)
            working_dir = config.get("working_directory", "")

        self.system_prompt = f"""You are a terminal-based operating system assistant designed to help users achieve their goals by executing tasks provided in text format. The current user goal is: {self.user_prompt}.

Working Directory: {working_dir}

You have access to the following tools:
{tools_details}

Your primary objective is to accomplish the user's goal by performing step-by-step actions. These actions can include:
1. Calling a tool
2. Executing Python code
3. Executing Shell commands
4. Providing a direct response

You must break down the user's goal into smaller steps and perform one action at a time. After each action, carefully evaluate the output to determine the next step.

### Action Guidelines:
- **Tool Call**: Use when a specific tool can help with the current step. Format:
  <<TOOL_CALL>>
  {{
    "tool_name": "name_of_tool",
    "input": {{
      "key": "value"   //Replace 'key' with the actual parameter name for the tool
    }}
  }}
  <<END_TOOL_CALL>>
- **Code Execution**: Write Python code when no tool is suitable or when custom logic is needed. Format:
  <<CODE>>
  your_python_code_here
  <<CODE>>
- **Shell Command Execution**: Execute shell commands when needed. Format:
  <<SHELL_COMMAND>>
  your_shell_command_here
  <<END_SHELL_COMMAND>>
- **Direct Response**: Provide a direct answer if the task doesn't require tools or code.

### Important Notes:
- Perform only one action per step.
- Always evaluate the output of each action before deciding the next step.
- Continue performing actions until the user's goal is fully achieved. Only then, include 'TASK_DONE' in your response.
- Do not end the task immediately after a tool call or code execution without evaluating its output.

Now, carefully plan your approach and start with the first step to achieve the user's goal.
"""

        self.task_prompt = """
Following are the things that you must read carefully and remember:

        - For tool calls, use:
        <<TOOL_CALL>>
        {
            "tool_name": "name_of_tool",
            "input": {
            "key": "value"  // Use the correct parameter name for each tool
            }
        }
        <<END_TOOL_CALL>>

        - For code execution, use:
        <<CODE>>
        your_python_code_here
        <<CODE>>

        - For shell command execution, use:
        <<SHELL_COMMAND>>
        your_shell_command_here
        <<END_SHELL_COMMAND>>

        After each action, always evaluate the output to decide your next step. Only include 'TASK_DONE'
        When the entire task is completed. Do not end the task immediately after a tool call or code execution without
        checking its output. 
        You can only execute a single tool call or code execution at a time, then check its ouput
        then proceed with the next call
        Use the working directory as the current directory for all file operations unless otherwise specified.
        
        

        These are the things that you learn't from the mistakes you made earlier :

        - When given a data file and asked to understand data/do data analysis/ data visualisation or similar stuff
        do not use file reader and read the whole data. Only use python code to do the analysis
        - This is a standard Python environment, not a python notebook or a repl. previous execution
         context is not preserved between executions.
        - You have a get_user_input tool to ask user more context before, in between or after tasks

"""

    def run_inference(self):
        retries = 0
        while retries <= self.rate_limiter.max_retries:
            try:
                self.rate_limiter.wait_if_needed()

                response = self.llm.chat(self.message) # LiteLLMInterface.chat() returns the full response string

                # Streaming is handled within LiteLLMInterface.chat()
                # and TerminalInterface.process_markdown_chunk()
                self.message.append({"role": "assistant", "content": response})
                return response

            except Exception as e: # Catching generic Exception as LiteLLM maps to OpenAI exceptions
                # Check if the error message contains "429" for rate limiting
                if "429" in str(e) and retries < self.rate_limiter.max_retries:
                    retries += 1
                    print(f"\nRate limit error detected. Waiting {self.rate_limiter.wait_time} seconds before retry {retries}/{self.rate_limiter.max_retries}")
                    time.sleep(self.rate_limiter.wait_time)
                # Check if the error is an SDKError (though less likely with LiteLLM directly)
                # or if it's any other exception that we should retry or raise.
                elif isinstance(e, SDKError) and "429" in str(e) and retries < self.rate_limiter.max_retries: # Added SDKError check just in case
                    retries += 1
                    print(f"\nRate limit exceeded (SDKError). Waiting {self.rate_limiter.wait_time} seconds before retry {retries}/{self.rate_limiter.max_retries}")
                    time.sleep(self.rate_limiter.wait_time)
                else:
                    print(f"\nError occurred during inference: {str(e)}")
                    # You might want to log the full traceback here for debugging
                    # import traceback
                    # print(traceback.format_exc())
                    raise
        raise Exception("Failed to complete inference after maximum retries")

    def run(self):

        self.run_task()

    def run_task(self):
        # Remove tools_details parameter since it's in the prompt
        task_message = self.task_prompt

        self.message.append({"role": "user", "content": task_message})

        iteration = 0
        task_done = False

        while iteration < self.max_iter and not task_done:
            # Check for tool calls
            response = self.run_inference()
            tool_call = self.parse_tool_call(response)
            if tool_call:
                print(f"\nCalling tool: {tool_call['tool_name']}")
                try:
                    # Pass tool name and input as separate arguments
                    tool_output = tool_manager.call_tool(tool_call["tool_name"], tool_call["input"])
                    self.terminal.tool_output_log(tool_output, tool_call["tool_name"])
                    self.message.append({"role": "user", "content": f"Tool Output: {tool_output}"})
                except ValueError as e:
                    error_msg = str(e)
                    self.message.append({"role": "user", "content": f"Tool Error: {error_msg}"})
            
            else: # Not a tool call, check for code or shell command
                code = self.parse_code(response)
                shell_command = self.parse_shell_command(response)

                if code:
                    # Ask user for confirmation before executing the code
                    user_confirmation = input("Do you want to execute the Python code?")
                    if user_confirmation.lower() == 'y':
                        exec_result = self.python_executor.execute(code)
                        if exec_result['output'] == "" and not exec_result['success']:
                            error_msg = (
                                f"Python execution failed.\n"
                                f"Error: {exec_result.get('error', 'Unknown error')}"
                            )
                            print(f"there was an error in the python code execution {exec_result.get('error', 'Unknown error')}")
                            self.message.append({"role": "system", "content": error_msg})

                        elif exec_result['output'] == "":
                            no_output_msg = (
                                "Python execution completed but no output was shown. "
                                "Please add print statements to show the results. This isn't a jupyter notebook environment. "
                                "For example: print(your_variable) or print('Your message')"
                            )
                            self.message.append({"role": "system", "content": no_output_msg})
                        
                        #if there is an output (partial or full exeuction)
                        else:
                            # First, show the program output
                            if exec_result['output'].strip():
                                print(f"Program Output:\n{exec_result['output']}")
                            
                            # Then handle success/failure cases
                            if exec_result['success']:
                                self.message.append({"role": "user", "content": f"Program Output:\n{exec_result['output']}"})
                            else:
                                self.message.append({"role": "user", "content": f"Program Output:\n{exec_result['output']}\n{exec_result.get('error', 'Unknown error')}"})
    
                    else:
                        self.message.append({"role":"user","content":"User chose not to execute the Python code."})
                        print("Python code execution skipped by the user.")
                
                elif shell_command:
                    user_confirmation = input(f"Do you want to execute the shell command: '{shell_command}'?\n ")
                    if user_confirmation.lower() == 'y':
                        shell_result = self.shell_executor.execute(shell_command)
                        if shell_result['output'] == "" and not shell_result['success']:
                            error_msg = (
                                f"Shell command execution failed.\n"
                                f"Error: {shell_result.get('error', 'Unknown error')}"
                            )
                            print(f"there was an error in the shell command execution {shell_result.get('error', 'Unknown error')}")
                            self.message.append({"role": "system", "content": error_msg})

                        elif shell_result['output'] == "":
                            print("command executed")
                            self.message.append({"role": "system", "content": "command executed"})
                        
                        #if there is an output (partial or full execution)
                        else:
                            # First, show the command output
                            if shell_result['output'].strip():
                                print(f"Command Output:\n{shell_result['output']}")
                            
                            # Then handle success/failure cases
                            if shell_result['success']:
                                self.message.append({"role": "user", "content": f"Command Output:\n{shell_result['output']}"})
                            else:
                                self.message.append({"role": "user", "content": f"Command Output:\n{shell_result['output']}\n{shell_result.get('error', 'Unknown error')}"})
    
                    else:
                        self.message.append({"role":"user","content":"User chose not to execute the shell command."})
                        print("Shell command execution skipped by the user.")

            # Check if task is done
            if "TASK_DONE" in response:
                
                task_done = True

            else:
                self.message.append({"role": "user", "content": "If the task i mentioned is complete then output TASK_DONE .If not then run another iteration."})
                iteration += 1

        if not task_done:
            print(f"Task could not be completed within {self.max_iter} iterations.")

    def execute(self, code: str, exec_env: python_executor.PythonExecutor):
        """Executes the given Python code using the provided execution environment."""
        result = exec_env.execute(code)
        return result

if __name__ == "__main__":
    e1 = executor("")
    user_prompt = input("Please enter your prompt: ")
    e1.user_prompt = user_prompt
    e1.executor_prompt_init()  # Update system_prompt
    e1.message.append({"role": "system", "content": e1.system_prompt})  # Reset message list
    e1.run()

    while True:
        user_prompt = input("Please enter your prompt: ")
        e1.message.append({"role": "user", "content": user_prompt})
        # e1.message.append({"role":"user","content":e1.system_prompt})
        e1.run()
