import subprocess
import time
import sys
from .base_env import BaseEnv
import re

class ShellExecutor(BaseEnv):
    def __init__(self):
        super().__init__()
        self.process = None

    def execute(self, code_or_command: str) -> dict:
        """
        Executes a shell command and streams its output in real-time.
        Strictly prevents execution of harmful commands and access to sensitive directories.

        Args:
            code_or_command: The shell command to execute.

        Returns:
            A dictionary with the following keys:
            - 'output': The captured standard output (string).
            - 'error': The captured standard error (string).
            - 'success': A boolean indicating whether the command executed successfully.
        """
        try:
            # Strict security check for harmful commands and sensitive directories
            forbidden_patterns = [
                r'rm\s+-rf\s+/?(\s|$)',
                r'rm\s+-rf\s+--no-preserve-root',
                r'rm\s+-rf\s+/\\?',
                r'shutdown(\s|$)',
                r'reboot(\s|$)',
                r'halt(\s|$)',
                r':(){:|:&};:',  # fork bomb
                r'chmod\s+777\s+/(\s|$)',
                r'chown\s+root',
                r'\bmkfs\b',
                r'\bdd\b.*\bif=\/dev\/zero\b',
                r'\bdd\b.*\bof=\/dev\/sda',
                r'\bpoweroff\b',
                r'\binit\s+0\b',
                r'\bsudo\s+rm\s+-rf\s+/?',
                r'\bsudo\s+shutdown',
                r'\bsudo\s+reboot',
                r'\bsudo\s+halt',
                r'\bsudo\s+mkfs',
                r'\bsudo\s+dd',
                r'\bsudo\s+init\s+0',
                r'\bsudo\s+poweroff',
                r'\bsudo\s+chmod\s+777\s+/',
                r'\bsudo\s+chown\s+root',
                r'\bdel\b.*\/s.*\/q.*\/f.*C:\\',  # Windows
                r'format\s+C:',
                r'rd\s+/?s\s+/?q\s+C:\\',
                r'\bshutdown\b.*\/s',
                r'\bshutdown\b.*\/r',
                r'\bshutdown\b.*\/f',
                r'\bshutdown\b.*\/p',
                r'\bshutdown\b.*\/t',
                r'\bshutdown\b.*\/a',
                r'\bnet\s+user\s+.*\s+/delete',
                r'\bnet\s+user\s+administrator\s+/active:no',
                r'\bnet\s+user\s+administrator\s+/active:yes',
                r'\bnet\s+localgroup\s+administrators\s+.*\s+/delete',
                r'\bnet\s+localgroup\s+administrators\s+.*\s+/add',
            ]
            sensitive_dirs = [
                '/', '/etc', '/bin', '/usr', '/var', '/root', '/boot', '/dev', '/proc', '/sys', '/lib', '/lib64',
                'C:\\', 'C:/', 'C:\\Windows', 'C:/Windows', 'C:\\System32', 'C:/System32',
                'D:\\', 'D:/', 'E:\\', 'E:/'
            ]
            # Check for forbidden patterns
            for pattern in forbidden_patterns:
                if re.search(pattern, code_or_command, re.IGNORECASE):
                    return {
                        'success': False,
                        'output': 'Blocked potentially harmful command.',
                        'error': f'Command matches forbidden pattern: {pattern}'
                    }
            # Improved check for sensitive directory access
            for sensitive_dir in sensitive_dirs:
                # Only block if the command is trying to directly operate on the sensitive dir itself (not subpaths)
                # For '/', block only if the command is exactly '/' or has a space and then '/'
                if sensitive_dir == '/':
                    if re.search(r'(\s|^)/($|\s)', code_or_command):
                        return {
                            'success': False,
                            'output': f'Blocked access to sensitive directory: {sensitive_dir}',
                            'error': f'Attempted access to sensitive directory: {sensitive_dir}'
                        }
                else:
                    # Block if the command is operating on the directory itself, not a subpath (e.g., 'ls /root' but not 'ls /root/somefile')
                    pattern = rf'(\s|^)({re.escape(sensitive_dir)})(\s|$)'
                    if re.search(pattern, code_or_command, re.IGNORECASE):
                        return {
                            'success': False,
                            'output': f'Blocked access to sensitive directory: {sensitive_dir}',
                            'error': f'Attempted access to sensitive directory: {sensitive_dir}'
                        }
            
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
            
            # First read all stdout character by character
            while True:
                char = self.process.stdout.read(1)
                if char == '' and self.process.poll() is not None:
                    break  # Process ended and no more output
                if char:
                    stdout_data.append(char)
                    print(char, end='', flush=True)  # Print in real-time, no extra newline
            
            # Then read all stderr (can keep line-by-line or do char-by-char similarly)
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
