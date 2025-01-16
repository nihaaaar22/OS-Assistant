import os
import sys
import json


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from Src.llm_interface.llm import MistralModel

# from Src.Agents.base_agent import base_agent
# from Src.Env import base_env #module import
# from Src.Env.python_executor import PythonExecutor
# from Src.Env.js_executor import JavaScriptExecutor
from Src.Tools import tool_manager
 
 #this is the executor agent class. This is responsible for executing tasks using the environment.
 #the context will be provided by the planner. For maintaining context between tasks the 
 #base agent will not be instantiated for each task. Instead the intermediate stage output will be
 #stored in the executor only. 

class executor():

    def __init__(self,user_prompt,planner_prompt, max_iter=3):
        self.planner_prompt = planner_prompt
        self.user_prompt = user_prompt
        self.executor_prompt_init()
        self.llm = MistralModel()
        self.max_iter=3

        self.message = [
            {"role":"system","content":self.system_prompt}]

        

    def get_tool_dir(self):
        """Reads the tool_dir.json file and returns its content as a string."""
        with open("Src/Tools/tool_dir.json", "r") as file:
            json_string = file.read()
            return json_string


    def parse_tool_call(self, response):
        """
        Parses the LLM's response to extract tool call details.
        Looks for the special delimiters `<<TOOL_CALL>>` and `<<END_TOOL_CALL>>`
        and extracts the JSON content between them.
        """
        # Check if the response contains the delimiters
        if "<<TOOL_CALL>>" in response and "<<END_TOOL_CALL>>" in response:
            try:
                # Find the start and end of the tool call content
                start_index = response.find("<<TOOL_CALL>>") + len("<<TOOL_CALL>>")
                end_index = response.find("<<END_TOOL_CALL>>")

                # Extract the JSON content between the delimiters
                json_str = response[start_index:end_index].strip()

                # Parse the JSON string
                tool_call = json.loads(json_str)
                return tool_call
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                # If parsing fails, return None
                print(f"Error parsing JSON: {e}")
                return None
        else:
            # If the delimiters are not found, return None
            return None


    def executor_prompt_init(self):
        """Initializes the system and task-specific prompts for the LLM."""

        self.system_prompt = """You are an operating system assistant that helps in the execution of 
        planned tasks by the planner. System details: 
        The goal given by the user is {user_prompt}. You will be given tasks by the planner, and you 
        should only focus on the given task at hand and produce the desired result. You are powered by
        tools, about which you will be told by the planner. Your task is to check out the given tools
        and use them to implement the current task. When the task is completed, you must signal this
        by including the phrase "TASK_DONE" in your response."""

        self.individual_task_prompt = """The current task details are given here in JSON format:
        {task_details}. The details of tools mentioned in the task are {tools_details}. 

        To call a tool, follow these steps:
        1. Use the delimiters `<<TOOL_CALL>>` and `<<END_TOOL_CALL>>` to specify a tool call.
        2. Provide the tool details in the following JSON format between the delimiters:
           <<TOOL_CALL>>
           {{
               "tool_name": "",
               "input": ""
           }}
           <<END_TOOL_CALL>>

        Use the tools iteratively to achieve the desired result: {expected_output}. After each tool call, evaluate the output and decide if further iterations are needed. If the task is completed, include the phrase "TASK_DONE" in your response to signal that no further iterations are required.
"""

    def run_inference(self):
        """Runs inference using the LLM to generate responses."""
        response = ""
        stream = self.llm.chat(self.message)

        for chunk in stream:
            content = chunk.data.choices[0].delta.content
            print(content, end="")  # Print in real-time
            response += content

        assistant_message = {"role": "assistant", "content": response}
        self.message.append(assistant_message)

        return response

    def run(self):
        """Executes all tasks provided by the planner."""
        tools_details = self.get_tool_dir()
        
        for task in self.planner_prompt:
            # This will complete fully before moving to the next task
            self.run_task(task, tools_details)


    def run_task(self, task, tools_details):
        """Executes an individual task until the LLM certifies that it is done."""

        task_message = self.individual_task_prompt.format(
                task_details=task["prompt_to_taskexecutor"],
                expected_output=task["expected_output"],
                tools_details=tools_details
            )

        # Append the task message to the message history
        self.message.append({"role": "user", "content": task_message})

        response = self.run_inference()

        iteration = 0
        task_done = False

        while iteration < self.max_iter and not task_done:
          
            tool_call = self.parse_tool_call(response)

            if tool_call:
                # Call the tool with the extracted input parameters
                try:
                    tool_output =tool_manager.call_tool(tool_call["tool_name"], **tool_call["input"])
                except ValueError as e:
                    tool_output = str(e)

                # Append the tool output to the message history for context
                self.message.append({"role": "user", "content": f"Tool Output: {tool_output}"})

            

            # Check if the task is done
            if "TASK_DONE" in response:
                print("Task completed successfully.")
                task_done = True
            else:
                print("Task not yet completed. Running another iteration...")
                if(not tool_call):
                    self.message.append({"role":"user","content":"Continue with completing the task."})
                else:
                    self.message.append({"role":"user","content":"Above is the tool response of the tool that you requested.Continute with completing the task"})
                response = self.run_inference()
                iteration += 1

        if not task_done:
            print(f"Task could not be completed within {self.max_iter} iterations.")





    
    

    #     pass
    #the languge and prompt will be given by the planner
    #the prompt will be specific
    # def __init__(self,language,prompt):

    # def temp(self):
    #     env = base_env.create_environment("python")
    #     file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Test/testscript1.txt"))  # Relative path
    #     with open(file_path, "r") as file:
    #         code = file.read()
    #         env.execute(code)


    #     #for temprary purpose. its used to test the environment

    # def temp1(self):
    #     env = base_env.create_environment("javascript")
    #     file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Test/testscriptjs.txt"))  # Relative path
    #     with open(file_path, "r") as file:
    #         code = file.read()
    #         env.execute(code)

    # def temp2(self):
    #     env = JavaScriptExecutor()
    #     file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Test/testscriptjs.txt"))  # Relative path
    #     with open(file_path, "r") as file:
    #         code = file.read()
    #         result = env.execute(code)
    #         print(result)


    def generate_code(self):
        pass


    def execute(self,code,exec_env):
        pass


planner_output =[
  {
    "id": 1,
    "description": "Find the latest trends in AI.",
    "prompt_to_taskexecutor": "Search the web for the latest trends in AI, including breakthroughs, applications, and future predictions.",
    "expected_output": "A list of the latest trends in AI.",
    "next_task": "Organize the trends into categories.",
    "tool_use": "web_loader"
  },
  {
    "id": 2,
    "description": "Organize the trends into categories.",
    "prompt_to_taskexecutor": "Organize the AI trends into categories such as 'Breakthroughs', 'Applications', and 'Future Predictions'.",
    "expected_output": "A categorized list of AI trends.",
    "next_task": "Summarize the key insights from the trends.",
    "tool_use": ""
  },
]

user_query = "What is the current inr to dollar conversion rate"
# user_query = "What is the latest news on Ai. Cu"
e1 = executor(user_query,planner_output)
e1.run()

    



# execute = base_agent()
# execute.display
