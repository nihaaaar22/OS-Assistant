import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from Agents.Executor.executor2 import executor

class OpenCopilot:
    def __init__(self):
        self.e1 = None  # Initialize as None, will be set in run()

    def run(self):
        # Get initial user prompt
        user_prompt = input("Please enter your prompt: ")
        
        # Initialize executor with the prompt
        self.e1 = executor(user_prompt)
        self.e1.executor_prompt_init()  # Initialize the system prompt
        self.e1.message.append({"role": "system", "content": self.e1.system_prompt})
        
        # Run the first task
        self.e1.run()

        # Continue conversation loop
        while True:
            try:
                user_prompt = input("\nPlease enter your prompt (or 'quit' to exit): ")
                if user_prompt.lower() == 'quit':
                    print("Goodbye!")
                    break
                    
                self.e1.message.append({"role": "user", "content": user_prompt})
                self.e1.run()
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                continue

# To run the copilot
if __name__ == "__main__":
    copilot = OpenCopilot()
    copilot.run()



    
