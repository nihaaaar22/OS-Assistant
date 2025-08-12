import os
from PyPDF2 import PdfReader
from PyPDF2 import errors as PyPDF2Errors
import docx
from docx.opc import exceptions as DocxOpcExceptions

# Limits for file reading
MAX_FILE_SIZE_MB = 5
MAX_TOKENS = 50000  # rough estimate: ~4 chars/token
MAX_LINES = 1000
TEXTUAL_EXTENSIONS = {
    '.txt', '.md', '.csv', '.tsv', '.json', '.yaml', '.yml', '.ini', '.cfg', '.toml',
    '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rb', '.rs', '.c', '.cpp', '.h', '.hpp',
    '.css', '.scss', '.sass', '.html', '.xml', '.sh'
}


def _estimate_tokens(text: str) -> int:
    """Estimate token count from text length."""
    return max(0, len(text) // 4)


def _truncate_to_max_lines(text: str, max_lines: int) -> str:
    """Return only the first max_lines of text with an ellipsis footer."""
    lines = text.split('\n')
    if len(lines) <= max_lines:
        return text
    truncated = '\n'.join(lines[:max_lines])
    return truncated + f"\n\n... (truncated, showing {max_lines} of {len(lines)} lines) ..."


def _apply_content_limits(content: str, file_path: str, file_size_mb: float) -> str:
    """Truncate content if it exceeds token/line limits and add an informative header."""
    line_count = content.count('\n') + 1
    estimated_tokens = _estimate_tokens(content)
    if estimated_tokens > MAX_TOKENS or line_count > MAX_LINES:
        truncated = _truncate_to_max_lines(content, MAX_LINES)
        header = (
            f"=== Content of file: {file_path} (TRUNCATED) ===\n"
            f"File size: {file_size_mb:.2f} MB | Lines: {line_count} | Estimated tokens: {estimated_tokens}\n"
            f"Showing first {MAX_LINES} lines due to size limits.\n\n"
        )
        return header + truncated
    return content


def _read_text_preview(file_path: str, max_lines: int) -> str:
    """Stream-read and return the first max_lines lines from a text file."""
    lines = []
    line_count = 0
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            lines.append(line.rstrip('\n'))
            line_count += 1
            if line_count >= max_lines:
                break
    text = '\n'.join(lines)
    return text + f"\n\n... (preview only, showing first {max_lines} lines) ..."


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
        
        # Gather basic stats
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        # Read file content
        content = ""
        if file_extension == ".pdf":
            # Block very large PDFs to avoid heavy processing
            if file_size_mb > MAX_FILE_SIZE_MB:
                return {"success": True, "output": (
                    f"=== Large file detected: {file_path} ===\n"
                    f"File size: {file_size_mb:.2f} MB (exceeds {MAX_FILE_SIZE_MB} MB limit)\n"
                    f"Content not loaded to avoid exceeding context limits.\n"
                    f"Provide specific pages or request analysis instead.\n"
                    f"=== End of file info: {file_path} ===\n"
                )}
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
            # Apply content limits post-read
            content = _apply_content_limits(content, file_path, file_size_mb)
        elif file_extension == ".docx":
            # Block very large DOCX to avoid heavy processing
            if file_size_mb > MAX_FILE_SIZE_MB:
                return {"success": True, "output": (
                    f"=== Large file detected: {file_path} ===\n"
                    f"File size: {file_size_mb:.2f} MB (exceeds {MAX_FILE_SIZE_MB} MB limit)\n"
                    f"Content not loaded to avoid exceeding context limits.\n"
                    f"Provide specific sections or request analysis instead.\n"
                    f"=== End of file info: {file_path} ===\n"
                )}
            try:
                doc = docx.Document(file_path)
                for para in doc.paragraphs:
                    content += para.text + "\n"
            except DocxOpcExceptions.PackageNotFoundError:
                return {"success": False, "output": f"Error: File '{file_path}' is not a valid DOCX file, is corrupted, or is not a compatible OOXML package."}
            except Exception as e: # General fallback for other DOCX issues
                return {"success": False, "output": f"Error processing DOCX file '{file_path}': {str(e)}"}
            # Apply content limits post-read
            content = _apply_content_limits(content, file_path, file_size_mb)
        else: # Fallback to existing plain text reading
            try:
                # If the file is very large, stream a preview of the first MAX_LINES lines
                if file_size_mb > MAX_FILE_SIZE_MB and (file_extension in TEXTUAL_EXTENSIONS or file_extension == ""):
                    preview = _read_text_preview(file_path, MAX_LINES)
                    header = (
                        f"=== Content of file: {file_path} (PREVIEW) ===\n"
                        f"File size: {file_size_mb:.2f} MB (exceeds {MAX_FILE_SIZE_MB} MB limit)\n"
                        f"Showing first {MAX_LINES} lines.\n\n"
                    )
                    content = header + preview
                else:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    # Apply content limits post-read
                    content = _apply_content_limits(content, file_path, file_size_mb)
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