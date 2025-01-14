import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from Src.llm_interface.llm import MistralModel

# from Agents.base_agent import base_agent
# from Env import base_env #module import
# from Env.python_executor import PythonExecutor
# from Env.js_executor import JavaScriptExecutor
import Src.Tools
 
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

        self.message = [
            {"role":"system","content":self.system_prompt}]

    def get_tool_dir(self):
        """Reads the tool_dir.json file and returns its content as a string."""
        with open("Src/Tools/tool_dir.json", "r") as file:
            json_string = file.read()
            return json_string

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

        To call a tool, use the following format:
        - Tool Name: <tool_name>
        - Input: <input_parameters>

        You have to use the tools and, through multiple iterations, achieve the desired result: 
        {expected_output}. Once the task is completed, include the phrase "TASK_DONE" in your response
        to signal that no further iterations are needed."""

    def run_inference(self):
        """Runs inference using the LLM to generate responses."""
        response = ""
        stream = self.llm.chat(self.message)

        for chunk in stream:
            content = chunk.data.choices[0].delta.content
            print(content, end="")  # Print in real-time
            response += content

        return response

    def run(self):
        """Executes all tasks provided by the planner."""
        tools_details = self.get_tool_dir()  # Get the tools details from the JSON file

        for task in self.planner_prompt:
            # Run each task until the LLM signals that it is done
            self.run_task(task, tools_details)

    def run_task(self, task, tools_details):
        """Executes an individual task until the LLM certifies that it is done."""

        task_message = self.individual_task_prompt.format(
                task_details=task["prompt_to_taskexecutor"],
                expected_output=task["expected_output"],
                tools_details=tools_details
            )

        response = self.run_inference()



        # iteration = 0
        # task_done = False

        # while iteration < self.max_iter and not task_done:
        #     # Format the task-specific prompt
        #     task_message = self.individual_task_prompt.format(
        #         task_details=task["prompt_to_taskexecutor"],
        #         expected_output=task["expected_output"],
        #         tools_details=tools_details
        #     )

            

        #     # Append the task message to the message history
        #     self.message.append({"role": "planner", "content": task_message})

        #     # Run inference with the updated message
        #     response = self.run_inference()

        #     # Check if the task is done
        #     if "TASK_DONE" in response:
        #         print("Task completed successfully.")
        #         task_done = True
        #     else:
        #         print("Task not yet completed. Running another iteration...")
        #         iteration += 1

        # if not task_done:
        #     print(f"Task could not be completed within {self.max_iter} iterations.")





    
    

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
    "description": "Identify the latest INR to USD conversion rate.",
    "prompt_to_taskexecutor": "Find the latest INR to USD conversion rate.",
    "expected_output": "The latest INR to USD conversion rate.",
    "tool_use": "Google Search"
  },
  {
    "id": 2,
    "description": "Extract the conversion rate from the search results.",
    "prompt_to_taskexecutor": "Extract the INR to USD conversion rate from the search results",
    "expected_output": "The extracted INR to USD conversion rate.",
    "tool_use": ""
  }
]

user_query = "What is the current inr to dollar conversion rate"
e1 = executor(user_query,planner_output)
e1.run()

    



# execute = base_agent()
# execute.display
