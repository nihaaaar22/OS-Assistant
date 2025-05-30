import unittest
from unittest.mock import patch, MagicMock, call
import os

# Assuming OpenCopilot.py is in Src directory and uses:
# from Tools.file_task import file_reader
# from prompt_toolkit.shortcuts import print_formatted_text
# So we patch them in Src.OpenCopilot context
from Src.OpenCopilot import OpenCopilot, FormattedText

class TestExtractFilesAndProcessPrompt(unittest.TestCase):

    def setUp(self):
        self.copilot = OpenCopilot()
        # Default behavior for path functions to simplify tests
        # These can be overridden in specific tests if needed
        self.abspath_patcher = patch('os.path.abspath', side_effect=lambda x: '/abs/' + os.path.basename(x))
        self.expanduser_patcher = patch('os.path.expanduser', side_effect=lambda x: x.replace('~', '/user/home'))
        
        self.mock_abspath = self.abspath_patcher.start()
        self.mock_expanduser = self.expanduser_patcher.start()
        
        self.addCleanup(self.abspath_patcher.stop)
        self.addCleanup(self.expanduser_patcher.stop)

    @patch('Src.OpenCopilot.print_formatted_text')
    @patch('Src.OpenCopilot.file_reader')
    @patch('os.path.isfile')
    @patch('os.path.exists')
    def test_successful_text_file_load(self, mock_exists, mock_isfile, mock_file_reader, mock_print_formatted_text):
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_file_reader.return_value = {"success": True, "output": "Text content"}

        user_input = "@test.txt explain this"
        # Path seen by file_reader will be /abs/test.txt due to mock_abspath
        expected_file_path_in_prompt = '/abs/test.txt'
        
        expected_final_prompt = f"=== Content of file: {expected_file_path_in_prompt} ===\nText content\n=== End of file: {expected_file_path_in_prompt} ===\n\nexplain this"
        
        result_prompt = self.copilot.extract_files_and_process_prompt(user_input)
        
        mock_file_reader.assert_called_once_with(file_path=expected_file_path_in_prompt)
        
        # Check that a success message was printed for the loaded file
        # The first call to print_formatted_text is for loading, the second (if any) for total files.
        args, _ = mock_print_formatted_text.call_args_list[0]
        self.assertIsInstance(args[0], FormattedText)
        self.assertEqual(args[0][0], ('class:success', f"✓ Loaded file: {expected_file_path_in_prompt}"))
        
        self.assertEqual(expected_final_prompt.strip(), result_prompt.strip())

    @patch('Src.OpenCopilot.print_formatted_text')
    @patch('Src.OpenCopilot.file_reader')
    @patch('os.path.isfile')
    @patch('os.path.exists')
    def test_file_read_error_from_file_reader(self, mock_exists, mock_isfile, mock_file_reader, mock_print_formatted_text):
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_file_reader.return_value = {"success": False, "output": "Specific read error"}

        user_input = "@error.txt explain this"
        expected_file_path_in_error = '/abs/error.txt'
        # If file_reader fails, @file directive is NOT removed from prompt currently
        expected_final_prompt = "@error.txt explain this" 

        result_prompt = self.copilot.extract_files_and_process_prompt(user_input)

        mock_file_reader.assert_called_once_with(file_path=expected_file_path_in_error)
        
        args, _ = mock_print_formatted_text.call_args_list[0] # Error message for the specific file
        self.assertIsInstance(args[0], FormattedText)
        self.assertEqual(args[0][0], ('class:error', f"✗ Error reading file {expected_file_path_in_error}: Specific read error"))
        
        self.assertEqual(expected_final_prompt.strip(), result_prompt.strip())

    @patch('Src.OpenCopilot.print_formatted_text')
    @patch('Src.OpenCopilot.file_reader')
    @patch('os.path.isfile') # Still need to patch isfile even if not called
    @patch('os.path.exists')
    def test_non_existent_file(self, mock_exists, mock_isfile, mock_file_reader, mock_print_formatted_text):
        mock_exists.return_value = False
        # mock_isfile should not be called if mock_exists is False

        user_input = "@nonexistent.txt explain this"
        # Path that os.path.exists will check
        path_checked = '/abs/nonexistent.txt'
        expected_final_prompt = "@nonexistent.txt explain this" # Unchanged as per current logic

        result_prompt = self.copilot.extract_files_and_process_prompt(user_input)

        mock_exists.assert_called_once_with(path_checked)
        mock_isfile.assert_not_called() # Crucial check
        mock_file_reader.assert_not_called()
        
        args, _ = mock_print_formatted_text.call_args_list[0] # Warning message
        self.assertIsInstance(args[0], FormattedText)
        self.assertEqual(args[0][0], ('class:warning', f"⚠ Path not found: {path_checked}"))
        
        self.assertEqual(expected_final_prompt.strip(), result_prompt.strip())

    @patch('Src.OpenCopilot.print_formatted_text')
    @patch('Src.OpenCopilot.file_reader')
    @patch('os.path.isfile')
    @patch('os.path.exists')
    def test_directory_path(self, mock_exists, mock_isfile, mock_file_reader, mock_print_formatted_text):
        mock_exists.return_value = True
        mock_isfile.return_value = False # This indicates it's a directory (or not a file)

        user_input = "@testdir explain this"
        # Path that will be processed
        processed_path = '/abs/testdir'
        # In the prompt, @testdir is replaced by its absolute path
        expected_final_prompt = f"{processed_path} explain this" 

        result_prompt = self.copilot.extract_files_and_process_prompt(user_input)

        mock_exists.assert_called_once_with(processed_path)
        mock_isfile.assert_called_once_with(processed_path)
        mock_file_reader.assert_not_called()
        
        args, _ = mock_print_formatted_text.call_args_list[0] # Directory message
        self.assertIsInstance(args[0], FormattedText)
        self.assertEqual(args[0][0],('class:success', f"✓ Added directory path: {processed_path}"))
        
        self.assertEqual(expected_final_prompt.strip(), result_prompt.strip())

    @patch('Src.OpenCopilot.print_formatted_text')
    @patch('Src.OpenCopilot.file_reader')
    @patch('os.path.isfile')
    @patch('os.path.exists')
    def test_multiple_files_success_and_error(self, mock_exists, mock_isfile, mock_file_reader, mock_print_formatted_text):
        # All paths will be prefixed with /abs/ by the mock_abspath
        path_file1 = '/abs/file1.txt'
        path_error_file = '/abs/error.txt'
        path_file2 = '/abs/file2.txt'

        mock_exists.return_value = True # For all files
        mock_isfile.return_value = True # For all files

        def file_reader_side_effect(file_path):
            if file_path == path_file1:
                return {"success": True, "output": "content1"}
            elif file_path == path_error_file:
                return {"success": False, "output": "read error"}
            elif file_path == path_file2:
                return {"success": True, "output": "content2"}
            return {} # Should not happen
        mock_file_reader.side_effect = file_reader_side_effect

        user_input = "@file1.txt @error.txt @file2.txt go"
        
        # Each block in file_contents already ends with a newline.
        # So "\n".join will put an additional newline between them.
        # Then another "\n" is added before the processed_prompt.
        block1_content = f"=== Content of file: {path_file1} ===\ncontent1\n=== End of file: {path_file1} ===\n"
        block2_content = f"=== Content of file: {path_file2} ===\ncontent2\n=== End of file: {path_file2} ===\n"
        remaining_prompt = "@error.txt  go" # After successful removals and stripping

        expected_final_prompt = block1_content + "\n" + block2_content + "\n" + remaining_prompt
        
        result_prompt = self.copilot.extract_files_and_process_prompt(user_input)

        # Check file_reader calls
        mock_file_reader.assert_any_call(file_path=path_file1)
        mock_file_reader.assert_any_call(file_path=path_error_file)
        mock_file_reader.assert_any_call(file_path=path_file2)
        self.assertEqual(mock_file_reader.call_count, 3)

        # Check print_formatted_text calls
        # Call 1: Success for file1.txt
        args1, _ = mock_print_formatted_text.call_args_list[0]
        self.assertEqual(args1[0][0], ('class:success', f"✓ Loaded file: {path_file1}"))
        # Call 2: Error for error.txt
        args2, _ = mock_print_formatted_text.call_args_list[1]
        self.assertEqual(args2[0][0], ('class:error', f"✗ Error reading file {path_error_file}: read error"))
        # Call 3: Success for file2.txt
        args3, _ = mock_print_formatted_text.call_args_list[2]
        self.assertEqual(args3[0][0], ('class:success', f"✓ Loaded file: {path_file2}"))
        # Call 4: Summary message "Loaded 2 file(s) into context"
        args4, _ = mock_print_formatted_text.call_args_list[3]
        self.assertEqual(args4[0][0], ('class:info', f"📁 Loaded 2 file(s) into context"))

        self.assertEqual(expected_final_prompt.strip(), result_prompt.strip())

if __name__ == '__main__':
    unittest.main()
