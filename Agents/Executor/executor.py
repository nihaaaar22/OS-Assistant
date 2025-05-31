# Dummy executor.py for OpenCopilot to import

class executor:
    """
    Dummy executor class.
    The actual functionality of the executor is not relevant for
    the OpenCopilot.extract_files_and_process_prompt unit tests.
    """
    def __init__(self, initial_prompt, max_iter=10):
        print(f"Warning: Dummy executor initialized with prompt: '{initial_prompt}', max_iter: {max_iter}. This should be mocked if its methods are called.")
        self.message = [] # OpenCopilot.py appends to this

    def executor_prompt_init(self):
        print("Warning: Dummy executor_prompt_init called.")
        pass

    def run(self):
        print("Warning: Dummy executor run called.")
        pass
