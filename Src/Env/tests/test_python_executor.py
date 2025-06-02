import unittest
from Src.Env.python_executor import PythonExecutor
import time
import threading

class TestPythonExecutor(unittest.TestCase):

    def test_execute_simple_script(self):
        executor = PythonExecutor()
        result = executor.execute("print('hello python')")
        self.assertTrue(result["success"])
        self.assertEqual(result["output"].strip(), "hello python")
        self.assertEqual(result["error"], "")

    def test_execute_script_with_error(self):
        executor = PythonExecutor()
        result = executor.execute("1/0")
        self.assertFalse(result["success"])
        self.assertTrue("ZeroDivisionError" in result["output"]) # Error message goes to stdout for python_executor
        self.assertEqual(result["error"], "") # stderr should be empty as Popen merges stderr to stdout in this case

    def test_stop_execution_long_script(self):
        executor = PythonExecutor()
        long_script = "import time; time.sleep(5); print('should not print')"

        execute_result = {}
        def target():
            res = executor.execute(long_script)
            execute_result.update(res)

        thread = threading.Thread(target=target)
        thread.start()

        time.sleep(1) # Give the script time to start
        executor.stop_execution()

        thread.join(timeout=2) # Wait for the thread to finish (should be quick after stop)

        self.assertFalse(execute_result.get("success", True), "Script execution should have failed or been stopped.")
        # Depending on timing, the process might be killed before it produces output,
        # or it might produce a timeout error, or a specific error from being terminated.
        # We check if the output indicates it didn't complete normally.
        output = execute_result.get("output", "")
        error = execute_result.get("error", "")

        # Check if 'should not print' is NOT in the output
        self.assertNotIn("should not print", output, "Script should have been terminated before completion.")

        # Check for signs of termination or timeout
        # This part is a bit tricky as the exact message can vary.
        # If basic_code_check fails, output is "Error: Code contains potentially unsafe operations..."
        # If timeout in communicate(), output is "Execution timed out..."
        # If process is terminated, output might be empty or contain partial error.
        # For now, we'll accept that if "should not print" is not there, it's a good sign.
        # A more robust check might involve looking for specific error messages related to termination if available.

        # A simple check that process is no longer listed in executor
        self.assertIsNone(executor.process, "Executor process should be None after stopping.")


    def test_stop_execution_no_script(self):
        executor = PythonExecutor()
        try:
            executor.stop_execution()
        except Exception as e:
            self.fail(f"stop_execution with no script raised an exception: {e}")
        self.assertIsNone(executor.process, "Executor process should be None.")

if __name__ == '__main__':
    unittest.main()
