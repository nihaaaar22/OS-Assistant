import os
import sys
import json
import time
from typing import Optional
from mistralai.models.sdkerror import SDKError
from Src.Env import python_executor
from Src.llm_interface.llm import MistralModel
from Src.Tools import tool_manager

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

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
    def __init__(self, user_prompt, planner_prompt, max_iter=3):
        self.planner_prompt = planner_prompt
        self.user_prompt = user_prompt
        self.executor_prompt_init()
        self.llm = MistralModel()
        self.max_iter = max_iter
        self.rate_limiter = RateLimiter(wait_time=5.0, max_retries=3)
        self.python_executor = python_executor.PythonExecutor(timeout=5)  # Initialize PythonExecutor
        self.message = [{"role": "system", "content": self.system_prompt}]

    def get_tool_dir(self):
        with open("Src/Tools/tool_dir.json", "r") as file:
            return file.read()

    def parse_tool_call(self, response):
        if "<<TOOL_CALL>>" in response and "<<END_TOOL_CALL>>" in response:
            try:
                start_index = response.find("<<TOOL_CALL>>") + len("<<TOOL_CALL>>")
                end_index = response.find("<<END_TOOL_CALL>>")
                json_str = response[start_index:end_index].strip()
                return json.loads(json_str)
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
        self.system_prompt = f"""You are an operating system assistant that helps in the execution of 
        planned tasks by the planner. The goal given by the user is {self.user_prompt}. You will be given tasks 
        by the planner, and you should only focus on the given task at hand and produce the desired result. 
        You are powered by tools and can execute Python code. Your task is to check out the given tools or 
        generate Python code to implement the current task. When the task is completed, include 'TASK_DONE' 
        in your response."""

        self.individual_task_prompt = """The current task details are given here in JSON format:
            {task_details}. 

            To write and execute code, use the delimiters `<<CODE>>` and `<<CODE>>`. Each code is an individual
            Python file that will be run and won't be a Python notebook. The code should achieve the expected output: 
            {expected_output}. 

            To call a tool, use the delimiters `<<TOOL_CALL>>` and `<<END_TOOL_CALL>>` with JSON format:
            <<TOOL_CALL>>
            {{"tool_name": "", "input": ""}}
            <<END_TOOL_CALL>>

            If the task requires iterations (e.g., analyzing a file step-by-step), break it into smaller code blocks.
            After each execution or tool call, evaluate the output. If the task is completed, include 'TASK_DONE' 
            in your response.Note that the task isn't completed until you review the code execution output or tool execution
            output"""

    def run_inference(self):
        retries = 0
        while retries <= self.rate_limiter.max_retries:
            try:
                self.rate_limiter.wait_if_needed()
                response = ""
                stream = self.llm.chat(self.message)
                for chunk in stream:
                    content = chunk.data.choices[0].delta.content
                    print(content, end="")
                    response += content
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
        tools_details = self.get_tool_dir()
        for task in self.planner_prompt:
            self.run_task(task, tools_details)

    def run_task(self, task, tools_details):
        task_message = self.individual_task_prompt.format(
            task_details=task["prompt_to_taskexecutor"],
            expected_output=task["expected_output"]
        )
        self.message.append({"role": "user", "content": task_message})
        response = self.run_inference()

        iteration = 0
        task_done = False

        while iteration < self.max_iter and not task_done:
            # Check for tool calls
            tool_call = self.parse_tool_call(response)
            if tool_call:
                try:
                    # Pass tool name and input as separate arguments
                    tool_output = tool_manager.call_tool(tool_call["tool_name"], tool_call["input"])
                    self.message.append({"role": "user", "content": f"Tool Output: {tool_output}"})
                except ValueError as e:
                    error_msg = str(e)
                    self.message.append({"role": "user", "content": f"Tool Error: {error_msg}"})
                response = self.run_inference()
            else:

            # Check for code execution
                code = self.parse_code(response)
                if code:
                    # Ask user for confirmation before executing the code
                    user_confirmation = input("Do you want to execute the following code?\n" + code + "\n(y/n): ")
                    if user_confirmation.lower() == 'y':
                        exec_result = self.python_executor.execute(code)
                        output_msg = (
                            f"Code Output: {exec_result['output']}\n"
                            f"Execution {'succeeded' if exec_result['success'] else 'failed'}"
                        )
                        print(output_msg)  # Show result in the terminal
                        self.message.append({"role": "user", "content": output_msg})
                    else:
                        self.message.append({"role":"user","content":"i don't want to execute the code"})
                        print("Code execution skipped by the user.")
                    response = self.run_inference()

            # Check if task is done
            if "TASK_DONE" in response:
                print("\nTask completed successfully.")
                task_done = True
            else:
                print("\nTask not yet completed. Running another iteration...")
                self.message.append({"role": "user", "content": "Continue with completing the task."})
                response = self.run_inference()
                iteration += 1

        if not task_done:
            print(f"Task could not be completed within {self.max_iter} iterations.")
            

    def execute(self, code: str, exec_env: python_executor.PythonExecutor):
        """Executes the given Python code using the provided execution environment."""
        result = exec_env.execute(code)
        return result