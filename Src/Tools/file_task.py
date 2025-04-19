import os

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
        
        # Security check: Prevent access to sensitive directories
        forbidden_dirs = ["/etc", "/root", "/sys", "/proc"]
        if any(file_path.startswith(d) for d in forbidden_dirs):
            return {"success": False, "output": "Error: Access to system directories is restricted."}
        
        # Check if file exists and is readable
        if not os.path.isfile(file_path):
            return {"success": False, "output": f"Error: File '{file_path}' does not exist."}
        if not os.access(file_path, os.R_OK):
            return {"success": False, "output": f"Error: No read permission for '{file_path}'."}
        
        # Read file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {"success": True, "output": content}
    
    except Exception as e:
        return {"success": False, "output": f"Error: {str(e)}"}

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
        
        dir_path = kwargs["dir_path"]
        
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