import subprocess
from Src.Env.base_env import BaseEnv

class ShellExecutor(BaseEnv):
    def __init__(self):
        super().__init__()

    def execute(self, code_or_command: str) -> dict:
        """
        Executes a shell command and captures its output, error, and success status.

        Args:
            code_or_command: The shell command to execute.

        Returns:
            A dictionary with the following keys:
            - 'output': The captured standard output (string).
            - 'error': The captured standard error (string).
            - 'success': A boolean indicating whether the command executed successfully.
        """
        try:
            process = subprocess.run(
                code_or_command,
                shell=True,
                capture_output=True,
                text=True,
                check=False  # Don't raise an exception on non-zero exit codes
            )
            return {
                "output": process.stdout,
                "error": process.stderr,
                "success": process.returncode == 0,
            }
        except Exception as e:
            return {
                "output": "",
                "error": str(e),
                "success": False,
            }

    def stop_execution(self):
        print("Stopping shell command is not fully implemented")
        # In a real scenario, you might try to find and kill the process
        # using self.process.terminate() or self.process.kill()
        # For now, this is a placeholder.

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
