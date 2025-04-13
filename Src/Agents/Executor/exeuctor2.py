# the change in this executor is the the tasks will not be iterated in a for loop and execution will not be done one by one
# instead it would be asked what is the next course of action

import os
import sys
import json
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from typing import Optional
from mistralai.models.sdkerror import SDKError
from Src.Env import python_executor
from Src.llm_interface.llm import MistralModel
from Src.llm_interface.llm import Groqinference


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
        self.executor_prompt_init()
        self.llm = Groqinference()
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
        # Load tools details when initializing prompt
        tools_details = self.get_tool_dir()
        
        self.system_prompt = f"""You are a terminal-based operating system assistant designed to assist users in executing tasks provided in text format. The current goal given by the user is: {self.user_prompt}.
    
    You have access to the following tools:
    {tools_details}
    
    Your primary objective is to achieve the user's goal by iteratively performing actions—using available tools, generating Python code, or providing direct responses. You must approach the task step-by-step, evaluating the output of each action to determine the next step toward completing the user's objective.
    
    ### Instructions:
    - **Iterative Execution**: Break down the user's goal into manageable steps. Execute one action per step (tool call, code execution, or direct response). Tasks may not be completed in a single action, so continue iterating as needed.
    - **Action Options**:
      - **Tool Call**: Use a tool when it directly supports the current step.
      - **Code Execution**: Write Python code if a tool isn’t suitable or if custom logic is required. 
      - **Direct Response**: Answer the user directly if the task doesn’t require tools or code.
    - **Output Evaluation**: After each tool call or code execution, you will receive the output. Analyze this output carefully to plan the next action, adapting your approach to align with the user’s goal.
    - **Task Completion**: Continue executing steps until the user’s objective is fully achieved. Once complete, include 'TASK_DONE' in your response to indicate the task is finished.
    
    ### Action Formats:
    - **Tool Call**: Use this exact JSON format within delimiters:
<<TOOL_CALL>>
{{
"tool_name": "name_of_tool",
"input": {{
"key": "value"  // Use the appropriate argument key for each tool
}}
}}
<<END_TOOL_CALL>>
    - **Code Execution**: Enclose Python code within these delimiters:
<<CODE>>
your_python_code_here
<<CODE>>
    - **Direct Response**: Provide the answer or information directly without delimiters.

    ### Key Reminders:
    - Perform only one action at a time (tool call, code execution, or direct response).
    - Use the output of each action to inform your next step.
    - Choose the most appropriate action based on the current context and the user’s goal.
    - Include 'TASK_DONE' only when the entire task is completed.

    Now think carefully, break down the task, and begin with the first step to achieve the goal """


        self.task_prompt = """
         
         If using a tool, use these delimiters with the exact JSON format:
            <<TOOL_CALL>>
            {
                "tool_name": "name_of_tool",
                "input": {
                    "key": "value"  // Use the correct argument key for each tool
                }
            }
            <<END_TOOL_CALL>>

            If writing code, use these delimiters:
            <<CODE>>
            your_python_code_here
            <<CODE>>

        This is to remind you that after each execution or tool call, you have to evaluate the output 
        then decide the next action and
        that you can only execute a single tool call or code at a time.
        Include 'TASK_DONE' when the user's task is completed.

"""


    def run_inference(self):
        retries = 0
        while retries <= self.rate_limiter.max_retries:
            try:
                self.rate_limiter.wait_if_needed()
                response = ""
                response += self.llm.chat(self.message).choices[0].message.content

                # -------------------streaming for mistral ------------------------
                # for chunk in stream:
                #     content = chunk.data.choices[0].delta.content
                #     print(content, end="")
                #     response += content
                self.message.append({"role": "assistant", "content": response})
                print(response)
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
        # Remove tools_details from run since it's now in the prompt
        
        self.run_task()

    def run_task(self):
        # Remove tools_details parameter since it's in the prompt
        task_message = self.task_prompt

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
                    print(tool_output)
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
                        self.message.append({"role":"user","content":"i don't want to execute the code."})
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


e1 = executor("do visualisation of the file : /Users/niharshettigar/downloads/air_quality.csv")

e1.run()
