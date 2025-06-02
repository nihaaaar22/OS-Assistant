# from .base_executor import BaseExecutor

# class PythonExecutor():
#     def execute(self, code: str) -> str:
#         """Executes Python code and returns the result or an error message."""

#         # if not self.validate_code(code):
#         #     return "Code validation failed: Unsafe code detected."

#         local_vars = {}
#         try:
#             exec(code, {}, local_vars)  # Execute code in an isolated environment
#             return local_vars.get("output", "Code executed successfully.")
#         except Exception as e:
#             # return self.handle_error(e)
#             print("error in running python code", e)

import subprocess
import tempfile
import os
from typing import Dict
import textwrap
import sys
from Src.Env.base_env import BaseEnv

class PythonExecutor(BaseEnv):
    def __init__(self):
        super().__init__()
        self.process = None
        self.forbidden_terms = [
            'import os', 'import sys', 'import subprocess',
            'open(', 'exec(', 'eval(',
        ]

    def basic_code_check(self, code: str) -> bool:
        """Simple check for potentially dangerous code"""
        code_lower = code.lower()
        return not any(term.lower() in code_lower for term in self.forbidden_terms)

    def execute(self, code_or_command: str) -> Dict[str, str]:
        """Executes Python code in a separate process and returns the result"""
        
        # Basic safety check
        if not self.basic_code_check(code_or_command):
            return {
                'success': False,
                'output': 'Error: Code contains potentially unsafe operations. You can try and use tools to achieve same functionality.',
                'error': 'Security check failed'
            }

        # Create a temporary file to store the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Properly indent the code to fit inside the try block
            indented_code = textwrap.indent(code_or_command, '    ')
            # Wrap the indented code to capture output
            wrapped_code = f"""
try:
{indented_code}
except Exception as e:
    print(f"Error: {{str(e)}}")
"""
            f.write(wrapped_code)
            temp_file = f.name

        try:
            # Execute the code in a subprocess
            self.process = subprocess.Popen(
                [sys.executable, temp_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = self.process.communicate(timeout=30) # 30 second timeout
            returncode = self.process.returncode

            return {
                'success': returncode == 0,
                'output': stdout if returncode == 0 else stderr,
                'error': stderr if returncode != 0 else ''
            }

        except subprocess.TimeoutExpired:
            if self.process:
                self.process.kill() # Ensure process is killed on timeout
            return {
                'success': False,
                'output': 'Execution timed out after 30 seconds',
                'error': 'Timeout error'
            }
        except Exception as e:
            return {
                'success': False,
                'output': f'Error: {str(e)}',
                'error': str(e)
            }
        finally:
            self.process = None # Reset process
            # Clean up the temporary file
            try:
                os.unlink(temp_file)
            except:
                pass  # Ignore cleanup errors

    def stop_execution(self):
        if self.process and hasattr(self.process, 'pid') and self.process.pid is not None:
            try:
                self.process.terminate()
                print(f"Attempted to terminate Python process with PID: {self.process.pid}")
            except Exception as e:
                print(f"Error terminating Python process with PID {self.process.pid}: {e}")
            finally:
                self.process = None
        else:
            print("No active Python process to stop.")

