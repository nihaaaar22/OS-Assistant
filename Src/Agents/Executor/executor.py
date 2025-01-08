import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from Src.llm_interface.llm import MistralModel

from Agents.base_agent import base_agent
from Env import base_env #module import
from Env.python_executor import PythonExecutor
from Env.js_executor import JavaScriptExecutor
 
 #this is the executor agent class. This is responsible for executing tasks using the environment.
 #the context will be provided by the planner. For maintaining context between tasks the 
 #base agent will not be instantiated for each task. Instead the intermediate stage output will be
 #stored in the executor only. 

class executor():

    def __init__(self,user_prompt,planner_prompt,tool_manager, max_iter=3):
        self.planner_prompt = planner_prompt
        self.user_prompt = user_prompt
        self.executor_prompt_init()
        self.llm = MistralModel()

        self.message = [
            {"role":"system","content":self.system_prompt},
            
        ]

    
    def executor_prompt_init(self):
        pass
        
        self.system_prompt = """You are an operating system assistant that helps in the execution of 
        planned tasks by the planner. System details : 
        The goal given by the user is {user_prompt}. You will be given tasks by the planner and you 
        should only focus on the given task at hand and produce the desired result.You are powered by
        tools about which you will be told by the planner.Your task is to check out the given tools.
        Use the tools to implement the current task."""

        self.individual_task_prompt = """The current task details is given here in the JSON string format
        {task_details}. The details of tools mentioned in the task are {tools_details}.You have to use the 
        tools and using multiple iterations you have to active the desired result i.e. {task_details.expectedresult}
    """


    def run_inference(self):
        response = ""
        stream = self.llm.chat(self.message)
        
        for chunk in stream:
            content = chunk.data.choices[0].delta.content
            print(content, end="")  # Print in real-time
            response += content

        return response
    
    


    def run(self):
        pass
        #after init break down the planner response into individual tasks. 
        #pass each task into the executor.you need to give it a way for tool use
        
        for task in self.planner_prompt:
            self.run_task(task)


    def run_task(task):
        #run the task return the result to the llm. if its okay then llm should return ok 
        #else should perform more iterations. 

        pass








    
    

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
    "prompt_to_taskexecutor": "Extract the INR to USD conversion rate from the following search results: {{search_results}}",
    "expected_output": "The extracted INR to USD conversion rate.",
    "tool_use": ""
  }
]

user_query = "What is the current inr to dollar conversion rate"
e1 = executor()
e1.temp()

    



# execute = base_agent()
# execute.display
