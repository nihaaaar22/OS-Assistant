import os
from PyPDF2 import PdfReader
from PyPDF2 import errors as PyPDF2Errors
import docx
from docx.opc import exceptions as DocxOpcExceptions

def file_reader(**kwargs) -> dict:
    """Reads the content of a specified file and returns it.
    
    Args:
        **kwargs: Keyword arguments with 'file_path' specifying the file to read.
    
    Returns:
        Dictionary with 'success' (bool), 'output' (file content or error message).
    """
    try:
        # Validate input
        if "file_path" not in kwargs:
            return {"success": False, "output": "Error: 'file_path' is required."}
        
        file_path = kwargs["file_path"]
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
        # Enhanced Security Checks (Primary Change Area)
        abs_file_path = os.path.abspath(file_path)
        normalized_abs_path = abs_file_path.lower()

        # Expanded and normalized forbidden directories
        # Ensure trailing slashes for directory checks and all lowercase
        forbidden_dirs = [
            "/etc/", "/root/", "/sys/", "/proc/", "/dev/", "/boot/", "/sbin/", "/usr/sbin/",
            "c:\\windows\\", "c:\\program files\\", "c:\\program files (x86)\\",
            "c:\\users\\default\\", # Added default user for windows
            "/system/", "/library/", "/private/", "/applications/", "/usr/bin/"
        ]

        if any(normalized_abs_path.startswith(d) for d in forbidden_dirs):
            return {"success": False, "output": f"Error: Access to system or restricted directory '{abs_file_path}' is not allowed."}

        # Check for sensitive files/directories in user's home directory
        try:
            user_home = os.path.expanduser("~").lower()
            # Define sensitive files and directories relative to user_home
            sensitive_home_files = [
                os.path.join(user_home, ".gitconfig").lower(),
                os.path.join(user_home, ".bash_history").lower(),
                os.path.join(user_home, ".zsh_history").lower(),
                os.path.join(user_home, ".python_history").lower(), # Added from previous patterns
                os.path.join(user_home, ".npmrc").lower(),        # Added from previous patterns
                os.path.join(user_home, ".yarnrc").lower(),       # Added from previous patterns
                os.path.join(user_home, ".gemrc").lower()         # Added from previous patterns
                # Add other specific sensitive *files* here
            ]
            sensitive_home_dirs = [
                os.path.join(user_home, ".ssh").lower(),
                os.path.join(user_home, ".aws").lower(),
                os.path.join(user_home, ".gcloud").lower(), # Changed from .config/gcloud as per request
                os.path.join(user_home, ".gnupg").lower(),       # Added from previous patterns
                os.path.join(user_home, ".docker").lower(),      # Added from previous patterns
                os.path.join(user_home, ".kube").lower()         # Added from previous patterns
                # Add other specific sensitive *directories* here
            ]

            if normalized_abs_path in sensitive_home_files:
                return {"success": False, "output": f"Error: Access to sensitive user configuration file '{normalized_abs_path}' is restricted."}

            if any(normalized_abs_path.startswith(d + os.sep) for d in sensitive_home_dirs): # Check if path starts with any sensitive dir + separator
                return {"success": False, "output": f"Error: Access to files within sensitive user directory '{os.path.dirname(normalized_abs_path)}' is restricted."}

            # Also, if the path *is* one of the sensitive_home_dirs itself (e.g. trying to read ~/.ssh as a file)
            if normalized_abs_path in sensitive_home_dirs:
                return {"success": False, "output": f"Error: Direct access to sensitive user directory '{normalized_abs_path}' is restricted."}

        except Exception: # Broad exception catch
            # In case of error determining home directory or paths (e.g., os.path.expanduser fails),
            # proceed with caution. For now, we'll let it pass, but logging this would be advisable.
            # This means sensitive home path checks might be bypassed if an error occurs here.
            pass

        # Determine file extension (moved after security checks)
        _, file_extension = os.path.splitext(file_path)
        file_extension = file_extension.lower()

        # Check if file exists and is readable (after security checks)
        if not os.path.isfile(file_path):
            return {"success": False, "output": f"Error: File '{file_path}' does not exist."}
        if not os.access(file_path, os.R_OK):
            return {"success": False, "output": f"Error: No read permission for '{file_path}'."}
        
        # Read file content
        content = ""
        if file_extension == ".pdf":
            try:
                with open(file_path, "rb") as f:
                    reader = PdfReader(f)
                    if reader.is_encrypted:
                        # Attempt to decrypt with an empty password, or handle if not possible.
                        # For now, we'll assume most encrypted files without passwords are not readable by default.
                        return {"success": False, "output": f"Error: PDF file '{file_path}' is encrypted and cannot be read without a password."}
                    for page in reader.pages:
                        content += page.extract_text() or ""
            except PyPDF2Errors.FileNotDecryptedError:
                return {"success": False, "output": f"Error: PDF file '{file_path}' is encrypted and cannot be read."}
            except PyPDF2Errors.PdfReadError as pe:
                return {"success": False, "output": f"Error: Could not read PDF file '{file_path}'. It may be corrupted, not a valid PDF, or an unsupported format. Details: {str(pe)}"}
            except Exception as e: # General fallback for other PDF issues
                return {"success": False, "output": f"Error processing PDF file '{file_path}': {str(e)}"}
        elif file_extension == ".docx":
            try:
                doc = docx.Document(file_path)
                for para in doc.paragraphs:
                    content += para.text + "\n"
            except DocxOpcExceptions.PackageNotFoundError:
                return {"success": False, "output": f"Error: File '{file_path}' is not a valid DOCX file, is corrupted, or is not a compatible OOXML package."}
            except Exception as e: # General fallback for other DOCX issues
                return {"success": False, "output": f"Error processing DOCX file '{file_path}': {str(e)}"}
        else: # Fallback to existing plain text reading
            # Ensure this part also has robust error handling, though it's simpler
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError as ude:
                return {"success": False, "output": f"Error: Could not decode file '{file_path}' using UTF-8. It might be a binary file or use a different text encoding. Details: {str(ude)}"}
            except Exception as e: # General fallback for text files
                return {"success": False, "output": f"Error reading text file '{file_path}': {str(e)}"}
        
        return {"success": True, "output": content}
    
    except FileNotFoundError: # Specific exception for file not found
        return {"success": False, "output": f"Error: File '{file_path}' does not exist."} # Redundant if isfile check is perfect, but good practice
    except PermissionError: # Specific exception for permission issues
        return {"success": False, "output": f"Error: No read permission for '{file_path}'."} # Redundant if os.access check is perfect
    except Exception as e:
        return {"success": False, "output": f"An unexpected error occurred while trying to read '{file_path}': {str(e)}"}

def file_maker(**kwargs) -> dict:
    """Creates an empty file at the specified path.
    
    Args:
        **kwargs: Keyword arguments with 'file_path' specifying the file to create.
    
    Returns:
        Dictionary with 'success' (bool), 'output' (confirmation or error message).
    """
    try:
        # Validate input
        if "file_path" not in kwargs:
            return {"success": False, "output": "Error: 'file_path' is required."}
        
        file_path = kwargs["file_path"]
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
        
        # Security check: Prevent creation in sensitive directories
        forbidden_dirs = ["/etc", "/root", "/sys", "/proc"]
        if any(file_path.startswith(d) for d in forbidden_dirs):
            return {"success": False, "output": "Error: Creation in system directories is restricted."}
        
        # Check if file already exists
        if os.path.exists(file_path):
            return {"success": False, "output": f"Error: File '{file_path}' already exists."}
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Create empty file
        with open(file_path, "w", encoding="utf-8"):
            pass
        
        return {"success": True, "output": f"File '{file_path}' created successfully."}
    
    except Exception as e:
        return {"success": False, "output": f"Error: {str(e)}"}

def file_writer(**kwargs) -> dict:
    """Writes or appends content to a specified file.
    
    Args:
        **kwargs: Keyword arguments with 'file_path' (str), 'content' (str), and optional 'append' (bool).
    
    Returns:
        Dictionary with 'success' (bool), 'output' (confirmation or error message).
    """
    try:
        # Validate input
        if "file_path" not in kwargs or "content" not in kwargs:
            return {"success": False, "output": "Error: 'file_path' and 'content' are required."}
        
        file_path = kwargs["file_path"]
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
        content = kwargs["content"]
        append_mode = kwargs.get("append", False)
        
        # Security check: Prevent writing to sensitive directories
        forbidden_dirs = ["/etc", "/root", "/sys", "/proc"]
        if any(file_path.startswith(d) for d in forbidden_dirs):
            return {"success": False, "output": "Error: Writing to system directories is restricted."}
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write or append to file
        mode = "a" if append_mode else "w"
        with open(file_path, mode, encoding="utf-8") as f:
            f.write(content)
        
        action = "appended to" if append_mode else "written to"
        return {"success": True, "output": f"Content {action} '{file_path}' successfully."}
    
    except Exception as e:
        return {"success": False, "output": f"Error: {str(e)}"}

def directory_maker(**kwargs) -> dict:
    """Creates a directory at the specified path.
    
    Args:
        **kwargs: Keyword arguments with 'dir_path' specifying the directory to create.
    
    Returns:
        Dictionary with 'success' (bool), 'output' (confirmation or error message).
    """
    try:
        # Validate input
        if "dir_path" not in kwargs:
            return {"success": False, "output": "Error: 'dir_path' is required."}
        
        # Convert to absolute path if not already absolute
        dir_path = kwargs["dir_path"]
        if not os.path.isabs(dir_path):
            dir_path = os.path.abspath(dir_path)
        
        # Security check: Prevent creation in sensitive directories
        forbidden_dirs = ["/etc", "/root", "/sys", "/proc"]
        if any(dir_path.startswith(d) for d in forbidden_dirs):
            return {"success": False, "output": "Error: Creation in system directories is restricted."}
        
        # Check if directory already exists
        if os.path.exists(dir_path):
            return {"success": False, "output": f"Error: Directory '{dir_path}' already exists."}
        
        # Create directory
        os.makedirs(dir_path)
        
        return {"success": True, "output": f"Directory '{dir_path}' created successfully."}
    
    except Exception as e:
        return {"success": False, "output": f"Error: {str(e)}"}