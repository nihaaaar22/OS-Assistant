import os
import sys
import json
from Agents.Executor.executor import executor

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

class OpenCopilot:
    def __init__(self):
        self.e1 = None  # Initialize as None, will be set in run()

    def run(self):
        # Conversational mode
        user_prompt = input("Please enter your prompt: ")
        self.e1 = executor(user_prompt)
        self.e1.executor_prompt_init()  # Initialize the system prompt
        self.e1.message.append({"role": "system", "content": self.e1.system_prompt})
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

    def run_task(self, user_prompt, max_iter=10):
        # One-shot task execution
        e1 = executor(user_prompt, max_iter=max_iter)
        e1.executor_prompt_init()
        e1.message.append({"role": "system", "content": e1.system_prompt})
        e1.run()

    @staticmethod
    def list_available_tools():
        tool_dir_path = os.path.join(os.path.dirname(__file__), '../Tools/tool_dir.json')
        with open(tool_dir_path, 'r') as f:
            tools = json.load(f)
        return tools

# To run the copilot
if __name__ == "__main__":
    copilot = OpenCopilot()
    copilot.run()



    
