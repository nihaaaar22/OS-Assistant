from abc import ABC, abstractmethod

class BaseExecutor(ABC):
    pass
#     def __init__(self):
#         pass

#     @abstractmethod
#     def execute(self, code: str):
#         """Executes the given code and returns the output or error."""
#         pass

#     def validate_code(self, code: str) -> bool:
#         """Basic validation to ensure code is safe to execute. Override for custom rules."""
#         # Implement basic checks (e.g., preventing dangerous commands)
#         if "import os" in code or "import sys" in code:
#             return False  # Disallow potentially unsafe imports for security
#         return True

#     def handle_error(self, error: Exception) -> str:
#         """Handles errors during execution and returns a standardized error message."""
#         return f"Execution failed: {str(error)}"
