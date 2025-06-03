import subprocess
import time
import sys
from Src.Env.base_env import BaseEnv

class ShellExecutor(BaseEnv):
    def __init__(self):
        super().__init__()
        self.process = None

    def execute(self, code_or_command: str) -> dict:
        """
        Executes a shell command and streams its output in real-time.

        Args:
            code_or_command: The shell command to execute.

        Returns:
            A dictionary with the following keys:
            - 'output': The captured standard output (string).
            - 'error': The captured standard error (string).
            - 'success': A boolean indicating whether the command executed successfully.
        """
        try:
            # Execute the command in a subprocess
            self.process = subprocess.Popen(
                code_or_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            stdout_data = []
            stderr_data = []
            start_time = time.time()
            
            # First read all stdout
            for line in self.process.stdout:
                # Check for timeout
                if time.time() - start_time > 30:
                    self.process.kill()
                    return {
                        'success': False,
                        'output': 'Execution timed out after 30 seconds',
                        'error': 'Timeout error'
                    }
                
                stdout_data.append(line)
                print(line, end='', flush=True)  # Print in real-time
            
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
            self.process = None  # Reset process

    def stop_execution(self):
        if self.process and hasattr(self.process, 'pid') and self.process.pid is not None:
            try:
                self.process.terminate()
                print(f"Attempted to terminate shell process with PID: {self.process.pid}")
            except Exception as e:
                print(f"Error terminating shell process with PID {self.process.pid}: {e}")
            finally:
                self.process = None
        else:
            print("No active shell process to stop.")

if __name__ == '__main__':
    # Example usage (optional, for testing)
    executor = ShellExecutor()

    # Test case 1: Successful command
    result1 = executor.execute("echo 'Hello, World!'")
    print(f"Test Case 1 Result: {result1}")

    # Test case 2: Command with an error
    result2 = executor.execute("ls non_existent_directory")
    print(f"Test Case 2 Result: {result2}")

    # Test case 3: Command that succeeds but writes to stderr (e.g. some warnings)
    result3 = executor.execute("echo 'Error output' >&2")
    print(f"Test Case 3 Result: {result3}")

    # Test case 4: Command that produces no output
    result4 = executor.execute(":") # The ':' command is a no-op in bash
    print(f"Test Case 4 Result: {result4}")
