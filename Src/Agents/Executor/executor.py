# the change in this executor is the the tasks will not be iterated in a for loop and execution will not be done one by one
# instead it would be asked what is the next course of action

import os
import sys
import time
import logging
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from Utils.ter_interface import TerminalInterface
from Utils.executor_utils import parse_tool_call
from Agents.Executor.prompts import get_executor_prompt # Import prompts

from llm_interface.llm import LiteLLMInterface # Import LiteLLMInterfacea
from Tools import tool_manager

class RateLimiter:
    def __init__(self, wait_time: float = 1.0, max_retries: int = 3):
        self.wait_time = wait_time
        self.max_retries = max_retries
        self.last_call_time = None

    def wait_if_needed(self):
        if self.last_call_time is not None:
            elapsed = time.time() - self.last_call_time
            if elapsed < self.wait_time:
                time.sleep(self.wait_time - elapsed)
        self.last_call_time = time.time()

class executor:
    def __init__(self, user_prompt, max_iter=30):
        self.user_prompt = user_prompt
        self.max_iter = max_iter
        self.rate_limiter = RateLimiter(wait_time=3.0, max_retries=3)
        
        # Load environment configuration
        self.environment = self.load_environment_config()
        
        # Setup logging if in development environment
        if self.environment == "development":
            self.setup_logging()
        
        self.executor_prompt_init()  # Update system_prompt
        # self.python_executor = python_executor.PythonExecutor()  # Initialize PythonExecutor
        # self.shell_executor = ShellExecutor() # Initialize ShellExecutor
        self.message = [
            {"role": "system", "content": self.system_prompt},
            {"role":"user","content":"Hi"},
            {"role":"assistant","content":"""```json
{
    "tool_name": "get_user_input",
     "input": {
        "query": "Hi,im your terminal assistant. How can I help you?"
    }
}
```"""},
            {"role": "user", "content": self.user_prompt}
        ]
        self.terminal = TerminalInterface()
        self.initialize_llm()

    def initialize_llm(self):
        # Directly instantiate LiteLLMInterface. 
        # It handles its own configuration loading (including model_name from config.json).
        self.llm = LiteLLMInterface()

    def get_tool_dir(self):
        # Use direct path resolution instead of pkg_resources
        # pkg_resources is used for finding resources within installed packages,
        # but since we're working with a local project structure, we can use direct paths
        tool_dir_path = os.path.join(os.path.dirname(__file__), '../../Tools/tool_dir.json')
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

        self.system_prompt = get_executor_prompt(working_dir, tools_details)

    def run_inference(self):
        retries = 0
        while retries <= self.rate_limiter.max_retries:
            try:
                self.rate_limiter.wait_if_needed()

                response = self.llm.chat(self.message) # LiteLLMInterface.chat() returns the full response string

                # Log response in development environment
                if self.environment == "development":
                    self.logger.info(f"LLM Response: {response}")

                # Streaming is handled within LiteLLMInterface.chat()
                # and TerminalInterface.process_markdown_chunk()
                if response.strip():
                    self.message.append({"role": "assistant", "content": response})
                return response

            except Exception as e: # Catching generic Exception as LiteLLM maps to OpenAI exceptions
                # Check if the error message contains "429" for rate limiting
                if retries < self.rate_limiter.max_retries:
                    retries += 1
                    print(f"\nRate limit error detected. Waiting {self.rate_limiter.wait_time} seconds before retry {retries}/{self.rate_limiter.max_retries}")
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
        iteration = 0
        task_done = False

        while iteration < self.max_iter and not task_done:
            # Check for tool calls
            response = self.run_inference()
            tool_call = parse_tool_call(response)

            if tool_call:
                tool_name = tool_call['tool_name']
                tool_input = tool_call['input']
                

                # Call the tool and append the result (no confirmation or special logic)
                try:
                    tool_output_result = tool_manager.call_tool(tool_name, tool_input)
                    if tool_name not in ['execute_python_code', 'execute_shell_command']:
                        self.terminal.tool_output_log(tool_output_result, tool_name)
                    self.message.append({"role": "user", "content": "Tool Output: " + str(tool_output_result)})
                except ValueError as e:
                    error_msg = str(e)
                    print(f"Tool Error: {error_msg}")
                    self.message.append({"role": "user", "content": f"Tool Error: {error_msg}"})

            else: # Not a tool call, could be a direct response or requires clarification
                pass # Explicitly pass if no tool call and no old code/shell logic.

            # Check if task is done
            if "TASK_DONE" in response:
                
                task_done = True

            else:
                self.message.append({"role": "user", "content": "Continue with the task if not complete.Else simply output TASK_DONE. "})
                iteration += 1

        if not task_done:
            print(f"Task could not be completed within {self.max_iter} iterations.")

    # This method is superseded by the BaseEnv approach in run_task
    # def execute(self, code: str, exec_env: python_executor.PythonExecutor):
    #     """Executes the given Python code using the provided execution environment."""
    #     result = exec_env.execute(code)
    #     return result

    def load_environment_config(self):
        """Load environment configuration from config.json"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '../../../config.json')
            with open(config_path, "r") as config_file:
                config = json.load(config_file)
                return config.get("environment", "production")
        except Exception as e:
            
            return "production"

    def setup_logging(self):
        """Setup logging for development environment"""
        try:
            # Create logs directory if it doesn't exist
            logs_dir = os.path.join(os.path.dirname(__file__), '../../../logs')
            os.makedirs(logs_dir, exist_ok=True)
            
            # Create a specific logger for executor responses
            self.logger = logging.getLogger('executor_responses')
            self.logger.setLevel(logging.INFO)
            
            # Prevent propagation to parent loggers (this stops console output)
            self.logger.propagate = False
            
            # Remove any existing handlers to avoid duplicates
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)
            
            # Add file handler only (no console output)
            log_file = os.path.join(logs_dir, 'executor_responses.log')
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)
            
            # Suppress LiteLLM's verbose logging
            logging.getLogger('litellm').setLevel(logging.WARNING)
            
            self.logger.info("Development logging enabled for executor responses")
        except Exception as e:
            print(f"Warning: Could not setup logging: {e}")

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
    pass 
