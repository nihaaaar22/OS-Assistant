# the change in this executor is the the tasks will not be iterated in a for loop and execution will not be done one by one
# instead it would be asked what is the next course of action

import os
import sys
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from Src.Utils.ter_interface import TerminalInterface
from Src.Utils.executor_utils import parse_tool_call, parse_code, parse_shell_command
from Src.Agents.Executor.prompts import get_system_prompt, get_task_prompt # Import prompts

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
        self.message = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.task_prompt}
        ]
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

    def executor_prompt_init(self):
        # Load tools details when initializing prompt
        tools_details = self.get_tool_dir()

        # Read working_directory from config.json
        # This import needs to be here, or moved to the top if json is used elsewhere
        import json 
        with open(os.path.join(os.path.dirname(__file__), '../../../config.json'), "r") as config_file:
            config = json.load(config_file)
            working_dir = config.get("working_directory", "")

        self.system_prompt = get_system_prompt(self.user_prompt, working_dir, tools_details)
        self.task_prompt = get_task_prompt()

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
            tool_call = parse_tool_call(response)
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
                code = parse_code(response)
                shell_command = parse_shell_command(response)

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
                            self.message.append({"role": "user", "content": error_msg})

                        elif exec_result['output'] == "":
                            no_output_msg = (
                                "Python execution completed but no output was shown. "
                                "Please add print statements to show the results. This isn't a jupyter notebook environment. "
                                "For example: print(your_variable) or print('Your message')"
                            )
                            self.message.append({"role": "user", "content": no_output_msg})
                        
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
                            self.message.append({"role": "user", "content": error_msg})

                        elif shell_result['output'] == "":
                            print("command executed")
                            self.message.append({"role": "user", "content": "command executed"})
                        
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
    e1.message = [
        {"role": "system", "content": e1.system_prompt},
        {"role": "user", "content": e1.task_prompt}
    ]  # Reset message list properly
    e1.run()

    while True:
        user_prompt = input("Please enter your prompt: ")
        e1.message.append({"role": "user", "content": user_prompt})
        # e1.message.append({"role":"user","content":e1.system_prompt})
        e1.run()
