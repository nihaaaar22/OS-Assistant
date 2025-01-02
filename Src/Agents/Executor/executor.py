import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from Agents.base_agent import base_agent
from Env import base_env #module import
from Env.python_executor import PythonExecutor
from Env.js_executor import JavaScriptExecutor
 
 #this is the executor agent class. This is responsible for executing tasks using the environment.
 #the context will be provided by the planner. For maintaining context between tasks the 
 #base agent will not be instantiated for each task. Instead the intermediate stage output will be
 #stored in the executor only. 

class executor(base_agent):

    # def __init__(self, prompt, tool_manager, max_iter=3):
    #     pass
    

    #     pass
    #the languge and prompt will be given by the planner
    #the prompt will be specific
    # def __init__(self,language,prompt):

    def temp(self):
        env = base_env.create_environment("python")
        file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Test/testscript2.txt"))  # Relative path
        with open(file_path, "r") as file:
            code = file.read()
            env.execute(code)


        #for temprary purpose. its used to test the environment

    def temp1(self):
        env = base_env.create_environment("javascript")
        file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Test/testscriptjs.txt"))  # Relative path
        with open(file_path, "r") as file:
            code = file.read()
            env.execute(code)

    def temp2(self):
        env = JavaScriptExecutor()
        file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Test/testscriptjs.txt"))  # Relative path
        with open(file_path, "r") as file:
            code = file.read()
            result = env.execute(code)
            print(result)


    def generate_code(self):
        pass


    def execute(self,code,exec_env):
        pass

e1 = executor()
e1.temp2()

    



# execute = base_agent()
# execute.display
