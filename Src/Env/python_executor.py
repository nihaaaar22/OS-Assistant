# from .base_executor import BaseExecutor

class PythonExecutor():
    def execute(self, code: str) -> str:
        """Executes Python code and returns the result or an error message."""

        # if not self.validate_code(code):
        #     return "Code validation failed: Unsafe code detected."

        local_vars = {}
        try:
            exec(code, {}, local_vars)  # Execute code in an isolated environment
            return local_vars.get("output", "Code executed successfully.")
        except Exception as e:
            # return self.handle_error(e)
            print("error in running python code", e)

    

