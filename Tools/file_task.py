# Dummy file_task.py for OpenCopilot to import
# The actual file_reader logic is mocked in the unit tests.

def file_reader(file_path):
    """
    Dummy file_reader. In a real scenario, this would read file content.
    For testing OpenCopilot.extract_files_and_process_prompt, this function
    is mocked.
    """
    print(f"Warning: Dummy file_reader called with {file_path}. This should be mocked in tests.")
    # Return a default error-like response so that if it's ever called unmocked,
    # it signals that something is wrong with the test setup.
    return {"success": False, "output": "Error: Dummy file_reader called directly."}
