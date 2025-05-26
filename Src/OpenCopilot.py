import os
import sys
import json
import re
from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText

# Add the parent directory to the path to enable imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from Src.Agents.Executor.executor import executor

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

class FilePathCompleter(Completer):
    def get_completions(self, document, complete_event):
        text_before_cursor = document.text_before_cursor
        
        # Find the last @ symbol and the path after it
        path_match = re.search(r'@([^@\s]*)$', text_before_cursor)
        if not path_match:
            return

        current_path = path_match.group(1)
        
        # Handle home directory expansion
        if current_path.startswith('~'):
            normalized_path = os.path.expanduser(current_path)
        else:
            # If it's a relative path, make it relative to current working directory
            normalized_path = os.path.abspath(current_path) if os.path.isabs(current_path) else current_path
        
        # Determine directory and filename parts
        if current_path.endswith('/') or (current_path and os.path.isdir(normalized_path)):
            # If path ends with / or is an existing directory, list its contents
            dir_path = normalized_path if os.path.isabs(current_path) else os.path.abspath(current_path)
            base_name = ""
        else:
            # Split into directory and filename parts
            if os.path.isabs(current_path):
                dir_path = os.path.dirname(normalized_path)
                base_name = os.path.basename(normalized_path)
            else:
                dir_path = os.path.dirname(os.path.abspath(current_path)) if current_path else os.getcwd()
                base_name = os.path.basename(current_path) if current_path else ""

        # If directory doesn't exist, try current working directory
        if not os.path.isdir(dir_path):
            dir_path = os.getcwd()
            base_name = current_path

        try:
            # Get all items in the directory
            items = os.listdir(dir_path)
            
            # Filter items that start with the base name (case-insensitive)
            matching_items = [item for item in items if item.lower().startswith(base_name.lower())]
            
            # Sort items: directories first, then files
            matching_items.sort(key=lambda x: (not os.path.isdir(os.path.join(dir_path, x)), x.lower()))
            
            for item in matching_items:
                full_path = os.path.join(dir_path, item)
                display_text = item
                
                # Add trailing slash for directories
                if os.path.isdir(full_path):
                    completion_text = item + '/'
                    display_text = f"{item}/ (directory)"
                else:
                    completion_text = item
                    # Show file extension info
                    _, ext = os.path.splitext(item)
                    if ext:
                        display_text = f"{item} ({ext[1:]} file)"
                
                # Calculate the replacement length
                start_position = -len(current_path)
                
                yield Completion(
                    text=completion_text,
                    start_position=start_position,
                    display=display_text
                )
                
        except (OSError, PermissionError):
            # Handle cases where we can't read the directory
            pass

class OpenCopilot:
    def __init__(self):
        self.e1 = None  # Initialize as None, will be set in run()
        self.session = PromptSession(completer=FilePathCompleter())

    def extract_files_and_process_prompt(self, user_input):
        """Extract file paths from @ commands and process the prompt."""
        # Find all @file patterns
        file_patterns = re.findall(r'@(\S+)', user_input)
        file_contents = []
        processed_prompt = user_input
        
        for file_path in file_patterns:
            # Expand user home directory if needed
            expanded_path = os.path.expanduser(file_path)
            
            # Convert to absolute path if it's relative
            if not os.path.isabs(expanded_path):
                expanded_path = os.path.abspath(expanded_path)
            
            if os.path.exists(expanded_path) and os.path.isfile(expanded_path):
                try:
                    with open(expanded_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Add file content with clear formatting
                    file_contents.append(f"=== Content of file: {expanded_path} ===\n{content}\n=== End of file: {expanded_path} ===\n")
                    
                    # Remove the @file pattern from the processed prompt
                    processed_prompt = processed_prompt.replace(f"@{file_path}", "")
                    
                    print_formatted_text(FormattedText([
                        ('class:success', f"✓ Loaded file: {expanded_path}")
                    ]))
                    
                except Exception as e:
                    print_formatted_text(FormattedText([
                        ('class:error', f"✗ Error reading file {expanded_path}: {str(e)}")
                    ]))
            else:
                print_formatted_text(FormattedText([
                    ('class:warning', f"⚠ File not found: {expanded_path}")
                ]))
        
        # Combine file contents with the processed prompt
        if file_contents:
            final_prompt = "\n".join(file_contents) + "\n" + processed_prompt.strip()
            print_formatted_text(FormattedText([
                ('class:info', f"📁 Loaded {len(file_contents)} file(s) into context")
            ]))
        else:
            final_prompt = processed_prompt.strip()
        
        return final_prompt

    def display_help(self):
        """Display help information about available commands."""
        help_text = """
🚀 TaskAutomator OpenCopilot Help

Available Commands:
  @<file_path>    - Include file content in your prompt
                   Example: @config.json analyze this configuration
                   Supports: relative paths, absolute paths, ~ for home directory
                   Multiple files: @file1.py @file2.txt compare these files
  
  quit           - Exit the application
  help           - Show this help message

File Path Completion:
  - Type @ followed by a file path
  - Use arrow keys to navigate suggestions
  - Press Tab or Enter to autocomplete
  - Supports directories (shows with /) and files
  - Case-insensitive matching

Examples:
  @src/main.py explain this code
  @~/documents/data.csv @analysis.py analyze this data using this script
  @config.json @logs/error.log debug the issue in these files
"""
        print_formatted_text(FormattedText([('class:info', help_text)]))

    def run(self):
        """Main conversation loop with enhanced @ command support."""
        print_formatted_text(FormattedText([
            ('class:title', '🚀 TaskAutomator OpenCopilot'),
            ('class:subtitle', '\nType "help" for available commands or start with your prompt.\nUse @<file_path> to include files in your context.\n')
        ]))
        
        try:
            # Get initial prompt
            user_input = self.session.prompt(HTML("<b>Please enter your prompt: </b>"))
            
            # Handle special commands
            if user_input.lower() == 'help':
                self.display_help()
                user_input = self.session.prompt(HTML("<b>Please enter your prompt: </b>"))
            elif user_input.lower() == 'quit':
                print("Goodbye!")
                return
            
            # Process the initial prompt
            final_prompt = self.extract_files_and_process_prompt(user_input)
            
            # Initialize executor with the processed prompt
            self.e1 = executor(final_prompt)
            self.e1.executor_prompt_init()
            self.e1.run()

            # Continue conversation loop
            while True:
                try:
                    user_input = self.session.prompt(HTML("<b>\nPlease enter your prompt (or 'quit' to exit): </b>"))
                    
                    # Handle special commands
                    if user_input.lower() == 'quit':
                        print("Goodbye!")
                        break
                    elif user_input.lower() == 'help':
                        self.display_help()
                        continue
                    
                    # Process the prompt and extract files
                    final_prompt = self.extract_files_and_process_prompt(user_input)
                    
                    # Add to conversation
                    self.e1.message.append({"role": "user", "content": final_prompt})
                    self.e1.run()
                    
                except KeyboardInterrupt:
                    print("\nGoodbye!")
                    break
                except Exception as e:
                    print_formatted_text(FormattedText([
                        ('class:error', f"An error occurred: {e}")
                    ]))
                    continue
                    
        except KeyboardInterrupt:
            print("\nGoodbye!")
        except Exception as e:
            print_formatted_text(FormattedText([
                ('class:error', f"Failed to start OpenCopilot: {e}")
            ]))

    def run_task(self, user_prompt, max_iter=10):
        """One-shot task execution with @ command support."""
        # Process @ commands in the prompt
        final_prompt = self.extract_files_and_process_prompt(user_prompt)
        
        e1 = executor(final_prompt, max_iter=max_iter)
        e1.executor_prompt_init()
        e1.run()

    @staticmethod
    def list_available_tools():
        """List all available tools."""
        try:
            tool_dir_path = os.path.join(os.path.dirname(__file__), 'Tools/tool_dir.json')
            with open(tool_dir_path, 'r') as f:
                tools = json.load(f)
            return tools
        except FileNotFoundError:
            print("Tools directory not found.")
            return {}
        except json.JSONDecodeError:
            print("Error reading tools configuration.")
            return {}

# To run the copilot
if __name__ == "__main__":
    copilot = OpenCopilot()
    copilot.run()



    
