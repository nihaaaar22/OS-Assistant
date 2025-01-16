import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from Src.llm_interface.llm import MistralModel



#module for planning i.e. breaking down the tasks into multiple subtasks. The tasks are stored
#and then provided as a list to the executor
#currently i am passing in the query in the planner stage itself. However need another
#utils module that will take query args along with other args such as file path for local files
#for now the planner will itself call the executor but later it needs to be done by an 
#external orchestorator. eventually it will be efficiengit 



class Planner():

    def __init__(self,user_query):
        self.planner_prompt_init()
        self.llm = MistralModel()

        self.message = [
            {"role":"system","content":self.planner_prompt},
            {"role":"user","content":user_query}
        ]
        

    def planner_prompt_init(self):

        output_format_eg = r"[{id:,description:,prompt_to_taskexecutor:,expected_result:,tool_use:}]"

        available_tools = r"[1.Google Search, 2. Website Scraper]"


        # system details = pwd,os version,
        

        self.planner_prompt = f"""You are an expert at breaking down a task into subtasks. You are helping in
          the  planning stage for an OS companion system. The OS companion system is powered with the following 
          tools {available_tools} .You will be given with the user query. After reading the
            query you will perform the following steps 


        1.Read the query carefully then determine what task is expected from the system.

        2. Break down the tasks if required depending on the complexity and return the steps(to determine in what 
        way the output will be). The steps will be sufficiently large so that one step output is required for the input
        of the next step. The steps will be run sequentially. A new step will be produced if and only if the current step 
        cannot proceed without the help of a language model. Optimize for the least amount of steps.
        Task example : Go out in the internet and find me the latest news on ai. In this example the tasks would be divided
        into two stages i.e. 1) search for the news on ai and  2)present the news in a readable format

        3. Produce the output only as a list of subtasks in the json list format.If
         no tool is needed then tool_use field should be empty.There should be no
         other unnecessary text in the output. Output format : {output_format_eg}.
        
        There should be no ambiguity. Each step should be well defined so that the executor exactly knows what output to produce.

        important note: If a function or tool is NOT explicitly specified, do not make up functions. Use training data to respond instead.

        """

    def run(self):
    

        response = ""
        stream = self.llm.chat(self.message)
        
        for chunk in stream:
            content = chunk.data.choices[0].delta.content
            print(content, end="")  # Print in real-time
            response += content


        # data = json.loads(self.converttojson(response))

        # print(data)



    def converttojson(self,input_string):

        cleaned_string = input_string.strip().removeprefix("'''json").removesuffix("'''").strip()
        return cleaned_string

        

    def callexecutor():
        pass

    
#temp execution code
user_query = "What is the current inr to dollar conversion rate"

    # Instantiate the Planner with the user query
planner = Planner(user_query)

    # Run the Planner to process the query
planner.run()


    