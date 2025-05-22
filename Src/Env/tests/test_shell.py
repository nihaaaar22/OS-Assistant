import unittest
import sys
import os

# Adjust sys.path to include the parent directory of Src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from Src.Env.shell import ShellExecutor

class TestShellExecutor(unittest.TestCase):

    def setUp(self):
        self.executor = ShellExecutor()

    def test_execute_success(self):
        command = "echo 'hello world'"
        result = self.executor.execute(command)
        self.assertEqual(result["output"].strip(), "hello world")
        self.assertEqual(result["error"], "")
        self.assertTrue(result["success"])

    def test_execute_error(self):
        command = "nonexistentcommand123"
        result = self.executor.execute(command)
        self.assertEqual(result["output"], "")
        self.assertIn("not found", result["error"].lower()) # Error message might vary
        self.assertFalse(result["success"])

    def test_execute_stdout_and_stderr(self):
        # This command will print "stdout_msg" to stdout and "stderr_msg" to stderr
        # and will exit with success.
        command = "echo 'stdout_msg' && echo 'stderr_msg' >&2"
        result = self.executor.execute(command)
        self.assertEqual(result["output"].strip(), "stdout_msg")
        self.assertEqual(result["error"].strip(), "stderr_msg")
        self.assertTrue(result["success"])

    def test_execute_stderr_and_failure(self):
        # This command will print to stderr and exit with failure
        command = "ls /non_existent_directory_for_test"
        result = self.executor.execute(command)
        self.assertEqual(result["output"], "")
        self.assertNotEqual(result["error"], "")
        self.assertFalse(result["success"])


    def test_execute_no_output_success(self):
        command = ":"  # The ':' command is a no-op in bash and produces no output
        result = self.executor.execute(command)
        self.assertEqual(result["output"], "")
        self.assertEqual(result["error"], "")
        self.assertTrue(result["success"])

    def test_execute_success_with_stderr_warning(self):
        # Some programs output warnings to stderr but still exit successfully
        command = "echo 'This is a warning' >&2"
        result = self.executor.execute(command)
        self.assertEqual(result["output"], "")
        self.assertEqual(result["error"].strip(), "This is a warning")
        self.assertTrue(result["success"])

if __name__ == '__main__':
    unittest.main()
