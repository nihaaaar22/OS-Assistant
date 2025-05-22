import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Adjust sys.path to include the parent directory of Src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from Src.Agents.Executor.executor import executor
# Assuming ShellExecutor is in Src.Env.shell, and it's already tested separately
# from Src.Env.shell import ShellExecutor

class TestExecutorShellIntegration(unittest.TestCase):

    def setUp(self):
        # Mock the config loading for LLM and working directory
        mock_config = {
            "llm_provider": "mistral",  # or "groq", "openai" as per your default
            "working_directory": "/tmp"
        }
        # Ensure the config file path is correct relative to this test file
        config_path = os.path.join(os.path.dirname(__file__), '../../../../config.json')

        # Create a dummy config.json if it doesn't exist, or overwrite for test consistency
        with open(config_path, 'w') as f:
            json.dump(mock_config, f)

        # Mock tool_dir.json
        tool_dir_path = os.path.join(os.path.dirname(__file__), '../../../../Src/Tools/tool_dir.json')
        if not os.path.exists(os.path.dirname(tool_dir_path)):
            os.makedirs(os.path.dirname(tool_dir_path))
        with open(tool_dir_path, 'w') as f:
            json.dump({"tools": []}, f) # Empty tools list for simplicity

        self.executor_instance = executor(user_prompt="Test prompt")
        # Ensure shell_executor is initialized (it should be in executor's __init__)
        self.assertIsNotNone(self.executor_instance.shell_executor)


    def tearDown(self):
        # Clean up dummy config.json and tool_dir.json
        config_path = os.path.join(os.path.dirname(__file__), '../../../../config.json')
        if os.path.exists(config_path):
            os.remove(config_path)
        tool_dir_path = os.path.join(os.path.dirname(__file__), '../../../../Src/Tools/tool_dir.json')
        if os.path.exists(tool_dir_path):
            os.remove(tool_dir_path)
        if os.path.exists(os.path.dirname(tool_dir_path)):
            # Only remove if it was created by setup and is empty
            if not os.listdir(os.path.dirname(tool_dir_path)):
                 os.rmdir(os.path.dirname(tool_dir_path))


    # --- Tests for parse_shell_command ---
    def test_parse_shell_command_valid(self):
        response = "<<SHELL_COMMAND>>\nls -l\n<<END_SHELL_COMMAND>>"
        command = self.executor_instance.parse_shell_command(response)
        self.assertEqual(command, "ls -l")

    def test_parse_shell_command_missing_end_delimiter(self):
        response = "<<SHELL_COMMAND>>\nls -l"
        command = self.executor_instance.parse_shell_command(response)
        self.assertIsNone(command)

    def test_parse_shell_command_missing_start_delimiter(self):
        response = "ls -l\n<<END_SHELL_COMMAND>>"
        command = self.executor_instance.parse_shell_command(response)
        self.assertIsNone(command)

    def test_parse_shell_command_empty_command(self):
        response = "<<SHELL_COMMAND>>\n\n<<END_SHELL_COMMAND>>"
        command = self.executor_instance.parse_shell_command(response)
        self.assertEqual(command, "")

    def test_parse_shell_command_no_command(self):
        response = "This is a normal response without any command."
        command = self.executor_instance.parse_shell_command(response)
        self.assertIsNone(command)

    def test_parse_shell_command_multiple_delimiters_takes_first(self):
        response = "<<SHELL_COMMAND>>\necho 'first'\n<<END_SHELL_COMMAND>>\n<<SHELL_COMMAND>>\necho 'second'\n<<END_SHELL_COMMAND>>"
        command = self.executor_instance.parse_shell_command(response)
        self.assertEqual(command, "echo 'first'")

    # --- Tests for run_task shell command execution flow ---

    @patch('builtins.input', return_value='y') # Mock user input to always be 'y'
    @patch('Src.Agents.Executor.executor.MistralModel.chat') # Path to chat in the context of where executor runs it
    def test_run_task_shell_command_approved_and_executed(self, mock_llm_chat, mock_input):
        test_shell_command = "echo 'Shell approved'"
        llm_response_with_shell = f"<<SHELL_COMMAND>>\n{test_shell_command}\n<<END_SHELL_COMMAND>>\nTASK_DONE"
        mock_llm_chat.return_value = llm_response_with_shell

        # Mock shell_executor.execute
        self.executor_instance.shell_executor.execute = MagicMock(return_value={
            "output": "Shell approved",
            "error": "",
            "success": True
        })

        # Append initial user message to start the loop
        self.executor_instance.message.append({"role": "user", "content": self.executor_instance.task_prompt})
        self.executor_instance.run_task() # Max_iter is 10 by default

        mock_input.assert_called_once_with(f"Do you want to execute the shell command: '{test_shell_command}'?\n ")
        self.executor_instance.shell_executor.execute.assert_called_once_with(test_shell_command)
        
        # Check if the output message was added to self.message
        # The last message should be from the user role, containing the shell output
        last_message = self.executor_instance.message[-1]
        self.assertEqual(last_message["role"], "user")
        self.assertIn("Shell command execution succeeded", last_message["content"])
        self.assertIn("Output:\nShell approved", last_message["content"])


    @patch('builtins.input', return_value='n') # Mock user input to always be 'n'
    @patch('Src.Agents.Executor.executor.MistralModel.chat')
    def test_run_task_shell_command_denied(self, mock_llm_chat, mock_input):
        test_shell_command = "echo 'Shell denied'"
        llm_response_with_shell = f"<<SHELL_COMMAND>>\n{test_shell_command}\n<<END_SHELL_COMMAND>>\nTASK_DONE"
        mock_llm_chat.return_value = llm_response_with_shell

        self.executor_instance.shell_executor.execute = MagicMock()
        
        self.executor_instance.message.append({"role": "user", "content": self.executor_instance.task_prompt})
        self.executor_instance.run_task()

        mock_input.assert_called_once_with(f"Do you want to execute the shell command: '{test_shell_command}'?\n ")
        self.executor_instance.shell_executor.execute.assert_not_called()

        last_message = self.executor_instance.message[-1]
        self.assertEqual(last_message["role"], "user")
        self.assertIn("User chose not to execute the shell command.", last_message["content"])

    @patch('builtins.input', return_value='y')
    @patch('Src.Agents.Executor.executor.MistralModel.chat')
    def test_run_task_shell_command_execution_fails(self, mock_llm_chat, mock_input):
        test_shell_command = "ls /nonexistentdir"
        llm_response_with_shell = f"<<SHELL_COMMAND>>\n{test_shell_command}\n<<END_SHELL_COMMAND>>\nTASK_DONE"
        mock_llm_chat.return_value = llm_response_with_shell

        self.executor_instance.shell_executor.execute = MagicMock(return_value={
            "output": "",
            "error": "ls: cannot access '/nonexistentdir': No such file or directory",
            "success": False
        })

        self.executor_instance.message.append({"role": "user", "content": self.executor_instance.task_prompt})
        self.executor_instance.run_task()
        
        self.executor_instance.shell_executor.execute.assert_called_once_with(test_shell_command)
        last_message = self.executor_instance.message[-1]
        self.assertEqual(last_message["role"], "user")
        self.assertIn("Shell command execution failed", last_message["content"])
        self.assertIn("Error (if any):\nls: cannot access '/nonexistentdir': No such file or directory", last_message["content"])

    @patch('builtins.input', return_value='y')
    @patch('Src.Agents.Executor.executor.MistralModel.chat')
    def test_run_task_no_shell_command_just_response(self, mock_llm_chat, mock_input):
        llm_response_no_shell = "This is a simple response. TASK_DONE"
        mock_llm_chat.return_value = llm_response_no_shell

        self.executor_instance.shell_executor.execute = MagicMock()
        
        self.executor_instance.message.append({"role": "user", "content": self.executor_instance.task_prompt})
        self.executor_instance.run_task()

        # input() should not be called as there's no shell command or code
        mock_input.assert_not_called() 
        self.executor_instance.shell_executor.execute.assert_not_called()
        
        # The assistant's response is added, then the "If the task is complete..." message
        self.assertIn(llm_response_no_shell, [m["content"] for m in self.executor_instance.message if m["role"] == "assistant"])


if __name__ == '__main__':
    unittest.main()
