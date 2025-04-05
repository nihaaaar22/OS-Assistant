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
        # Load available tools from tool_dir.json
        tools_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Tools/tool_dir.json'))
        with open(tools_path, 'r') as f:
            tools = json.load(f)
        
        # Pass the tools directly to the prompt
        output_format_eg = r"""[{id:,description:,prompt_to_taskexecutor:(carefully mentions what the executor should do with edge cases)
        ,expected_output:,tool_use:(the name of the tool to use only populate if tool is required.Only one tool at a time),to_run_code:(yes or no),
        code_description:(should explicity mention what the code should do on execution)}]"""

        # system details = pwd,os version,
        
        self.planner_prompt = f"""You are an expert at breaking down a task into subtasks. You are responsible for the planning stage of OS assistant system. This assistant will act as a companion to do 
        tasks in your computer for you. It has access to the following tools : {json.dumps(tools, indent=2)}.It can also execute python code in the system. 

You will be given with the user query.  Based on the query you will perform the following steps. 

1.Read the query carefully, think and determine what task is expected from the system. Write down your thoughts for clarity.

2. Break down the tasks if required depending on the complexity and return the steps (to determine in what 
    way the output will be). The steps should be sufficiently large so that one step output is required for the input
    of the next step. The steps will be run sequentially. A new step will be produced if and only if the current step 
     cannot proceed without the help of a language model. Optimize for the least amount of steps.

    Task example : Go out in the internet and find me the latest news on ai. In this example the tasks would be divided
     into two stages i.e. 1) search for the news on ai using web_search tool 2) Get the links from previous step tool call, scrape all relevant links
     using web_loader tool and 3)Present aggregation/summary of the news
   
3. Provide the task details in the following JSON list format between the delimiters:
           <<TASK_BREAK_DOWN>>
           {output_format_eg}
           <<TASK_BREAK_DOWN>>.Each step can either execute code or run a tool not both. There should be no other unnecessary text in the output.
        
There should be no ambiguity. Each step should be well defined so that the executor exactly knows what output to produce.
Each code is an individual python file that will be run and won't be a python notebook.
There is no need to use python just for print statments

important note: If a function or tool is NOT explicitly specified, do not make up functions. Use whatever you have at the han currently

        """

    def run(self):
        max_retries = 3
        attempt = 0
        
        while attempt < max_retries:
            response = ""
            stream = self.llm.chat(self.message)
            
            for chunk in stream:
                content = chunk.data.choices[0].delta.content
                print(content, end="")  # Print in real-time
                response += content

            # Parse the response into a list of tasks
            tasks, error_message = self.parse_tasks(response)
            
            if tasks:  # If tasks were successfully parsed and verified
                # Create executor instance with the parsed tasks
                to_proceed = input("do you want to proceed? (y/n): ")
                if to_proceed.lower() == 'y':
                    exec = executor(self.user_query, tasks)
                    exec.run()
                else:
                    print("ending at the planner stage...")
                return
            else:
                # If there was an error, add it to the conversation and retry
                print(f"\nError in planning. Retrying... (Attempt {attempt + 1}/{max_retries})")
                self.message.append({"role": "assistant", "content": response})
                self.message.append({"role": "user", "content": f"""There was an error in your response: {error_message}
                Please provide a new task breakdown that:
                1. Uses only valid tools from the tool directory
                2. Ensures each task uses either a tool OR code execution, not both
                3. Follows the correct JSON format between <<TASK_BREAK_DOWN>> delimiters"""})
                attempt += 1
        
        print("Maximum retries reached. Planning failed.")

    def converttojson(self,input_string):

        cleaned_string = input_string.strip().removeprefix("'''json").removesuffix("'''").strip()
        return cleaned_string

        

    def callexecutor():
        pass

    
    def parse_tasks(self, response):
        """
        Parses the LLM's response to extract task details.
        Returns:
        - (tasks_list, None) if successful
        - (None, error_message) if there's an error
        """
        try:
            # Find the content between <<TASK_BREAK_DOWN>> and <<TASK_BREAK_DOWN>>
            if "<<TASK_BREAK_DOWN>>" in response:
                parts = response.split("<<TASK_BREAK_DOWN>>")
                if len(parts) >= 3:
                    json_str = parts[1].strip()
                    
                    # Parse the JSON string into a list of dictionaries
                    tasks = json.loads(json_str)
                    
                    # Validate that we got a list
                    if not isinstance(tasks, list):
                        tasks = [tasks]  # Convert single dict to list if necessary
                    
                    # Verify tasks meet requirements
                    valid_tasks, error_message = self.verify_tasks(tasks)
                    if not valid_tasks:
                        return None, error_message
                    
                    return tasks, None
                else:
                    return None, "Could not find both task delimiters in response"
            else:
                return None, "Could not find task delimiters in response"
                
        except json.JSONDecodeError as e:
            return None, f"Error parsing JSON: {e}"
        except Exception as e:
            return None, f"Unexpected error while parsing tasks: {e}"
    
    def verify_tasks(self, tasks):
        """
        Verifies that tasks meet the required conditions:
        1. Each task should only have a single tool
        2. The tool should be valid (from tool_dir.json)
        3. A task cannot have both tool_use and to_run_code=yes
        
        Returns:
        - (True, None) if all tasks are valid
        - (False, error_message) if any task is invalid
        """
        # Load available tools from tool_dir.json
        tools_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Tools/tool_dir.json'))
        with open(tools_path, 'r') as f:
            tools_data = json.load(f)
        
        # Extract valid tool names
        valid_tool_names = [tool["name"] for tool in tools_data]
        
        for i, task in enumerate(tasks):
            # Check if task has a tool specified
            if "tool_use" in task and task["tool_use"]:
                # Condition 1 & 2: Verify tool is valid
                if task["tool_use"] not in valid_tool_names:
                    return False, f"Task {i+1} uses invalid tool: {task['tool_use']}. Valid tools are: {valid_tool_names}"
                
                # Condition 3: Cannot have both tool_use and to_run_code=yes
                if "to_run_code" in task and task["to_run_code"].lower() == "yes":
                    return False, f"Task {i+1} cannot use both a tool and run code"
        
        return True, None

# Modify the execution code
if __name__ == "__main__":
    user_query = input("enter your prompt : ")
    
    # Instantiate the Planner with the user query
    planner = Planner(user_query)
    
    # Run the Planner which will also create and run the executor
    planner.run()


    