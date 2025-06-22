import subprocess
import tempfile
import os
from typing import Dict
import textwrap
import sys
from .base_env import BaseEnv
import time

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

        # Properly indent the code to fit inside the try block
        indented_code = textwrap.indent(code_or_command, '    ')
        # Wrap the indented code to capture output
        wrapped_code = f"""
try:
{indented_code}
except Exception as e:
    print(f"Error: {{str(e)}}")
"""


        try:
            # Execute the code in a subprocess
            self.process = subprocess.Popen(
                [sys.executable, "-u", "-c", wrapped_code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            stdout_data = []
            stderr_data = []
            start_time = time.time()
            
            # Read stdout character by character
            while True:
                char = self.process.stdout.read(1)
                if char == '' and self.process.poll() is not None:
                    break  # Process ended and no more output
                if char:
                    stdout_data.append(char)
                    print(char, end='', flush=True)  # Print in real-time, no extra newline
            
            # Then read all stderr
            for line in self.process.stderr:
                # Check for timeout
                if time.time() - start_time > 30:
                    self.process.kill()
                    return {
                        'success': False,
                        'output': 'Execution timed out after 30 seconds',
                        'error': 'Timeout error'
                    }
                
                stderr_data.append(line)
                print(line, end='', file=sys.stderr, flush=True)  # Print in real-time
            
            # Wait for process to complete
            returncode = self.process.wait()
            
            return {
                'success': returncode == 0,
                'output': ''.join(stdout_data) if returncode == 0 else ''.join(stderr_data),
                'error': ''.join(stderr_data) if returncode != 0 else ''
            }

        except Exception as e:
            return {
                'success': False,
                'output': f'Error: {str(e)}',
                'error': str(e)
            }
        finally:
            self.process = None # Reset process


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

