# the change in this executor is the the tasks will not be iterated in a for loop and execution will not be done one by one
# instead it would be asked what is the next course of action

import os
import sys
import json
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from Src.Utils.ter_interface import TerminalInterface

from typing import Optional
from mistralai.models.sdkerror import SDKError
from Src.Env import python_executor
from Src.llm_interface.llm import MistralModel
from Src.llm_interface.llm import Groqinference
from Src.llm_interface.llm import OpenAi

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
        self.message = [{"role": "system", "content": self.system_prompt}]
        self.terminal = TerminalInterface()
        self.initialize_llm()

    def initialize_llm(self):
        config_path = os.path.join(os.path.dirname(__file__), '../../../config.json')
        with open(config_path, "r") as config_file:
            config = json.load(config_file)
            llm_provider = config.get("llm_provider", "mistral")
            
        
        if llm_provider.lower() == "mistral":
            self.llm = MistralModel()
        elif llm_provider.lower() == "groq":
            self.llm = Groqinference()
        elif llm_provider.lower() == "openai":
            self.llm = OpenAi()
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")

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
3. Providing a direct response

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

                response = self.llm.chat(self.message)

                # -------------------streaming for mistral ------------------------
                # for chunk in stream:
                #     content = chunk.data.choices[0].delta.content
                #     print(content, end="")
                #     response += content
                self.message.append({"role": "assistant", "content": response})
                return response

            except SDKError as e:
                if "429" in str(e) and retries < self.rate_limiter.max_retries:
                    retries += 1
                    print(f"\nRate limit exceeded. Waiting {self.rate_limiter.wait_time} seconds before retry {retries}/{self.rate_limiter.max_retries}")
                    time.sleep(self.rate_limiter.wait_time)
                else:
                    print(f"\nError occurred: {str(e)}")
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

            else:

            # Check for code execution
                code = self.parse_code(response)
                if code:
                    # Ask user for confirmation before executing the code
                    user_confirmation = input("Do you want to execute the above code?\n ")
                    if user_confirmation.lower() == 'y':
                        exec_result = self.python_executor.execute(code)

                        if exec_result['output'] == "":
                            no_output_msg = (
                                "Execution completed but no output was shown. "
                                "Please add print statements to show the results.This isn't a jupiter notebook environment. "
                                "For example: print(your_variable) or print('Your message')"
                            )
                            self.message.append({"role": "user", "content": no_output_msg})
                            continue

                        else:
                            output_msg = (
                                f"Execution {'succeeded. Evaluate if the output is correct and what you needed' if exec_result['success'] else 'failed'}\n"
                                f"Code Output: {exec_result['output']}\n"
                            )
                            print(output_msg)
                            self.message.append({"role": "user", "content": output_msg})
                    else:
                        self.message.append({"role":"user","content":"i don't want to execute the code."})
                        print("Code execution skipped by the user.")

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

