#module for planning i.e. breaking down the tasks into multiple subtasks. The tasks are stored
#and then provided as a list to the executor
#currently i am passing in the query in the planner stage itself. However need another
#utils module that will take query args along with other args such as file path for local files
#for now the planner will itself call the executor but later it needs to be done by an 
#external orchestorator. eventually it will be efficiengit 

class planner():

    output_format_eg = my_string = r"[{id:,description:,prompt_to_taskexecutor:,expected_output:,tool_use:}]"
    planner_prompt = """ You are an expert at breaking down a task into subtasks. You are helping in the  planning stage for an OS companion system. The OS companion system is powered with the following tools [1.Google Search 2. Website Scraper] .You will be given with the user query. After reading the query you will perform the following steps 


1.Read the query carefully then determine what task is expected from the system.

2. Break down the tasks if required depending on the complexity and return the steps(to determine in what way the output will be). The steps will be sufficiently large so that one step output is required for the input of the next step. The steps will be run sequentially. A new step will be produced if and only if the current step cannot proceed without the help of a language model.
Tasks example : Go out in the internet and find me the latest news on ai 

3. Produce the output only as a list of subtasks in the json list format. Example :"""+ output_format_eg+f"""

User Query : {user_input}
"""
    def __init__(self,query):
        self.query = query

    def run():
        pass
    #decomposes the tasks

    def decomposetasks():
        pass

    def callexecutor():
        pass

    

    