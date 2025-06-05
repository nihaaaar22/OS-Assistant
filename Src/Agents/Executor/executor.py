# the change in this executor is the the tasks will not be iterated in a for loop and execution will not be done one by one
# instead it would be asked what is the next course of action

import os
import sys
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from Utils.ter_interface import TerminalInterface
from Utils.executor_utils import parse_tool_call
from Agents.Executor.prompts import get_system_prompt, get_task_prompt # Import prompts

from typing import Optional
from mistralai.models.sdkerror import SDKError # This might be an issue if LiteLLM doesn't use SDKError
                                              # LiteLLM maps exceptions to OpenAI exceptions.
                                              # We'll keep it for now and see if errors arise during testing.
# from Env import python_executor # Will be replaced by BaseEnv
# from Env.shell import ShellExecutor # Will be replaced by BaseEnv
from Src.Env.base_env import create_environment, BaseEnv # Added
from Env import python_executor # Keep for type hint in the old execute method if needed, or remove if execute is fully removed
from llm_interface.llm import LiteLLMInterface # Import LiteLLMInterface

from Tools import tool_manager

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
        # self.python_executor = python_executor.PythonExecutor()  # Initialize PythonExecutor
        # self.shell_executor = ShellExecutor() # Initialize ShellExecutor
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
        import pkg_resources
        tool_dir_path = pkg_resources.resource_filename('Tools', 'tool_dir.json')
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
                tool_name = tool_call['tool_name']
                tool_input = tool_call['input']
                print(f"\nIdentified tool call: {tool_name} with input {tool_input}")

                # Call the tool and append the result (no confirmation or special logic)
                try:
                    tool_output_result = tool_manager.call_tool(tool_name, tool_input)
                    self.terminal.tool_output_log(tool_output_result, tool_name)
                    print(tool_output_result)
                    self.message.append({"role": "user", "content": tool_output_result})
                except ValueError as e:
                    error_msg = str(e)
                    print(f"Tool Error: {error_msg}")
                    self.message.append({"role": "user", "content": f"Tool Error: {error_msg}"})

            else: # Not a tool call, could be a direct response or requires clarification
                # This part handles responses that are not formatted as tool calls.
                # It might be a final answer, a question, or just conversational text.
                # The existing logic for TASK_DONE or asking for next step handles this.
                # No specific code/shell parsing here anymore as they are tools.
                pass # Explicitly pass if no tool call and no old code/shell logic.

            # Check if task is done
            if "TASK_DONE" in response:
                
                task_done = True

            else:
                self.message.append({"role": "user", "content": "If the task i mentioned is complete then output TASK_DONE .If not then run another iteration."})
                iteration += 1

        if not task_done:
            print(f"Task could not be completed within {self.max_iter} iterations.")

    # This method is superseded by the BaseEnv approach in run_task
    # def execute(self, code: str, exec_env: python_executor.PythonExecutor):
    #     """Executes the given Python code using the provided execution environment."""
    #     result = exec_env.execute(code)
    #     return result

if __name__ == "__main__":
    # e1 = executor("") # Commenting out example usage for now as it might need adjustment
    # user_prompt = input("Please enter your prompt: ")
    # e1.user_prompt = user_prompt
    # e1.executor_prompt_init()  # Update system_prompt
    # e1.message = [
    #     {"role": "system", "content": e1.system_prompt},
    #     {"role": "user", "content": e1.task_prompt}
    # ]  # Reset message list properly
    # e1.run()

    # while True:
    #     user_prompt = input("Please enter your prompt: ")
    #     e1.message.append({"role": "user", "content": user_prompt})
    #     # e1.message.append({"role":"user","content":e1.system_prompt})
    #     e1.run()
    pass # Placeholder if main execution is commented out
