import subprocess
import sys
from .base_executor import BaseExecutor

class JavaScriptExecutor(BaseExecutor):
    def __init__(self):
        super().__init__()
        self.node_installed = self.check_node_installed()

    def check_node_installed(self) -> bool:
        """Checks if Node.js is installed on the system."""
        try:
            subprocess.run(["node", "-v"], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
        except FileNotFoundError:
            return False

    def install_node(self) -> bool:
        """Attempts to install Node.js based on the operating system."""
        try:
            if sys.platform.startswith("linux"):
                # Try to install Node.js using apt-get (for Debian/Ubuntu-based systems)
                subprocess.run(["sudo", "apt-get", "update"], check=True)
                subprocess.run(["sudo", "apt-get", "install", "-y", "nodejs"], check=True)
            elif sys.platform == "darwin":
                # Try to install Node.js using Homebrew on macOS
                subprocess.run(["brew", "install", "node"], check=True)
            elif sys.platform == "win32":
                # Check if Chocolatey is installed, and install Node.js
                subprocess.run(["choco", "install", "nodejs", "-y"], check=True)
            else:
                return False  # Unsupported OS for automatic installation
            return True
        except subprocess.CalledProcessError:
            return False  # Installation failed

    def execute(self, code: str) -> str:
        """Executes JavaScript code using Node.js and returns the result or an error message."""
        # Check if Node.js is installed, attempt installation if not
        if not self.node_installed:
            if not self.install_node():
                return "Node.js is not installed, and automatic installation failed. Please install Node.js manually."

        # Recheck after attempted installation
        self.node_installed = self.check_node_installed()
        if not self.node_installed:
            return "Node.js is required but not installed. Please install Node.js manually."

        # Proceed with code execution if Node.js is available
        if not self.validate_code(code):
            return "Code validation failed: Unsafe code detected."

        try:
            result = subprocess.run(
                ["node", "-e", code],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout if result.stdout else "Code executed successfully."
        except subprocess.CalledProcessError as e:
            return self.handle_error(e)
