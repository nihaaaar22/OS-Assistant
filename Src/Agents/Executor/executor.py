
from Agents.base_agent import base_agent
from Env.python_executor import PythonExecutor

#have to check wheter the import works

#executor module 
 
class executor(base_agent):
    def __init__(self, prompt, tool_manager, max_iter=3):
        pass
            # super().__init__()
            # self.prompt = prompt
            # self.tool_manager = tool_manager
            # self.max_iter = max_iter
            # self.open_api_doc_path = get_open_api_doc_path()
            # self.open_api_doc = {}
            # with open(self.open_api_doc_path) as f:
            # self.open_api_doc = json.load(f) 

    def temp(self):
        executor = PythonExecutor()

        file_path = "Test/testscript1.txt"  # Relative path
        with open(file_path, "r") as code:
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
