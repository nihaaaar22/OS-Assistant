

#module for planning i.e. breaking down the tasks into multiple subtasks. The tasks are stored
#and then provided as a list to the executor
#currently i am passing in the query in the planner stage itself. However need another
#utils module that will take query args along with other args such as file path for local files
#for now the planner will itself call the executor but later it needs to be done by an 
#external orchestorator. eventually it will be efficiengit 



class Planner():

    def __init__(self,user_query):
        planner_prompt_init()

        self.message = [
            {"role":"system","content":self.planner_prompt()},
            {"role":"user","content":user_query}
        ]
        

    def planner_prompt_init():

        output_format_eg = r"[{id:,description:,prompt_to_taskexecutor:,expected_output:,tool_use:}]"

        available_tools = r"[1.Google Search, 2. Website Scraper]"

        #os system details = 
        

        self.planner_prompt = f"""You are an expert at breaking down a task into subtasks. You are helping in
          the  planning stage for an OS companion system. The OS companion system is powered with the following 
          tools {available_tools} .You will be given with the user query. After reading the
            query you will perform the following steps 


        1.Read the query carefully then determine what task is expected from the system.

        2. Break down the tasks if required depending on the complexity and return the steps(to determine in what 
        way the output will be). The steps will be sufficiently large so that one step output is required for the input
        of the next step. The steps will be run sequentially. A new step will be produced if and only if the current step 
        cannot proceed without the help of a language model.
        Tasks example : Go out in the internet and find me the latest news on ai 

        3. Produce the output only as a list of subtasks in the json list format. Example : {output_format_eg}

        
        """

    def run():
        pass

        

    def decomposetasks():
        pass

    def callexecutor():
        pass

    

    