import unittest
from Src.Env.shell import ShellExecutor

class TestShellExecutor(unittest.TestCase):

    def test_execute_success(self):
        executor = ShellExecutor()
        result = executor.execute("echo hello")
        self.assertTrue(result["success"])
        self.assertEqual(result["output"].strip(), "hello")
        self.assertEqual(result["error"], "")

    def test_execute_error(self):
        executor = ShellExecutor()
        result = executor.execute("ls non_existent_directory_for_test")
        self.assertFalse(result["success"])
        self.assertEqual(result["output"], "")
        self.assertTrue("non_existent_directory_for_test" in result["error"])

    def test_stop_execution(self):
        executor = ShellExecutor()
        # This test mainly ensures that calling stop_execution doesn't raise an error
        try:
            executor.stop_execution()
        except Exception as e:
            self.fail(f"stop_execution raised an exception: {e}")

if __name__ == '__main__':
    unittest.main()
