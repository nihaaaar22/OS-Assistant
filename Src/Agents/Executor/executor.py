import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from Agents.base_agent import base_agent
from Env.python_executor import PythonExecutor


#have to check wheter the import works

#executor module 
 
class executor(base_agent):

    # def __init__(self, prompt, tool_manager, max_iter=3):
    #     pass
        

    def temp(self):
        executor = PythonExecutor()
        file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Test/testscript1.txt"))  # Relative path
        with open(file_path, "r") as file:
            code = file.read()
            executor.execute(code)


        #for temprary purpose. its used to test the environment
        

    def generate_code(self):
        pass

    def execute(self,code,exec_env):
        pass

e1 = executor()
e1.temp()

    



# execute = base_agent()
# execute.display
