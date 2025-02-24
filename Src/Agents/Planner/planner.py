import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from Src.llm_interface.llm import MistralModel
from Src.Agents.Executor.executor import executor



#module for planning i.e. breaking down the tasks into multiple subtasks. The tasks are stored
#and then provided as a list to the executor
#currently i am passing in the query in the planner stage itself. However need another
#utils module that will take query args along with other args such as file path for local files
#for now the planner will itself call the executor but later it needs to be done by an 
#external orchestorator. eventually it will be efficiengit 



class Planner():

    def __init__(self,user_query):
        self.user_query = user_query
        self.planner_prompt_init()
        self.llm = MistralModel()

        self.message = [
            {"role":"system","content":self.planner_prompt},
            {"role":"user","content":user_query}
        ]
        

    def planner_prompt_init(self):


        output_format_eg = r"""[{id:,description:,prompt_to_taskexecutor:(carefully mentions what the executor should do with edge cases),expected_output:,tool_use:(the name of the tool to use only populate if tool is required.Only one tool at a time),to_run_code:(yes or no),
        code_description:(should explicity mention what the code should do on execution)}]"""

        available_tools = r"[1.web_loader:loads the web page given the url,2.web_search:does a google search]"


        # system details = pwd,os version,
        

        self.planner_prompt = f"""You are an expert at breaking down a task into subtasks. You are responsible for the planning stage of OS assistant system. This assistant will act as a companion to do tasks in your computer for you. It works primarily by executing python code in the system. It also has access to the following tools : {available_tools}. 

You will be given with the user query.  Based on the query you will perform the following steps. 

1.Read the query carefully, think and determine what task is expected from the system. You can write down your thoughts for clarity.

2. Break down the tasks if required depending on the complexity and return the steps (to determine in what 
    way the output will be). The steps will be sufficiently large so that one step output is required for the input
    of the next step. The steps will be run sequentially. A new step will be produced if and only if the current step 
     cannot proceed without the help of a language model. Optimize for the least amount of steps.

    Task example : Go out in the internet and find me the latest news on ai. In this example the tasks would be divided
     into two stages i.e. 1) search for the news on ai and  2)present the news in a readable format.
   
3. Provide the task details in the following JSON list format between the delimiters:
           <<TASK_BREAK_DOWN>>
           {output_format_eg}
           <<TASK_BREAK_DOWN>>.Each step can either execute code or run a tool not both. There should be no other unnecessary text in the output.
        
There should be no ambiguity. Each step should be well defined so that the executor exactly knows what output to produce.
Each code is an individual python file that will be run and won't be a python notebook.

important note: If a function or tool is NOT explicitly specified, do not make up functions. Use whatever you have at the hand currently

        """

    def run(self):
        response = ""
        stream = self.llm.chat(self.message)
        
        for chunk in stream:
            content = chunk.data.choices[0].delta.content
            print(content, end="")  # Print in real-time
            response += content

        # Parse the response into a list of tasks
        tasks = self.parse_tasks(response)
        
        # Create executor instance with the parsed tasks
        to_proceed = input("do you want to proceed ?")
        if(to_proceed == 'y'):
            if tasks:
                exec = executor(self.user_query, tasks)
                exec.run()
        else:
            print("ending at the planner stage...")
        

    def converttojson(self,input_string):

        cleaned_string = input_string.strip().removeprefix("'''json").removesuffix("'''").strip()
        return cleaned_string

        

    def callexecutor():
        pass

    
    def parse_tasks(self, response):
        """
        Parses the LLM's response to extract task details.
        Returns a list of dictionaries containing task information.
        """
        try:
            # Find the content between <<TASK_BREAK_DOWN>> and <<TASK_BREAK_DOWN>>
            if "<<TASK_BREAK_DOWN>>" in response:
                # Get the content between the first and second occurrence of the delimiter
                parts = response.split("<<TASK_BREAK_DOWN>>")
                if len(parts) >= 3:
                    json_str = parts[1].strip()
                    
                    # Parse the JSON string into a list of dictionaries
                    tasks = json.loads(json_str)
                    
                    # Validate that we got a list
                    if not isinstance(tasks, list):
                        tasks = [tasks]  # Convert single dict to list if necessary
                    
                    return tasks
                else:
                    print("Error: Could not find both task delimiters in response")
                    return []
            else:
                print("Error: Could not find task delimiters in response")
                return []
                
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error while parsing tasks: {e}")
            return []

# Modify the execution code
if __name__ == "__main__":
    user_query = input("enter your prompt : ")
    
    # Instantiate the Planner with the user query
    planner = Planner(user_query)
    
    # Run the Planner which will also create and run the executor
    planner.run()


    