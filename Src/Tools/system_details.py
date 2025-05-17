import platform
import psutil
import datetime
import json

def get_os_details():
    """Get operating system details"""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }

def get_datetime():
    """Get current date and time"""
    now = datetime.datetime.now()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "timezone": datetime.datetime.now().astimezone().tzname()
    }

def get_memory_usage():
    """Get memory usage details"""
    memory = psutil.virtual_memory()
    return {
        "total": f"{memory.total / (1024**3):.2f} GB",
        "available": f"{memory.available / (1024**3):.2f} GB",
        "used": f"{memory.used / (1024**3):.2f} GB",
        "percent": f"{memory.percent}%"
    }

def get_cpu_info():
    """Get CPU information"""
    return {
        "physical_cores": psutil.cpu_count(logical=False),
        "total_cores": psutil.cpu_count(logical=True),
        "cpu_freq": {
            "current": f"{psutil.cpu_freq().current:.2f} MHz",
            "min": f"{psutil.cpu_freq().min:.2f} MHz",
            "max": f"{psutil.cpu_freq().max:.2f} MHz"
        },
        "cpu_usage": f"{psutil.cpu_percent()}%"
    }

def system_details(detail_type="all"):
    """
    Get system details based on the requested type.
    
    Args:
        detail_type (str): Type of system detail to retrieve (os, datetime, memory, cpu, all)
    
    Returns:
        dict: Requested system details
    """
    detail_type = detail_type.lower()
    
    if detail_type == "all":
        return {
            "os": get_os_details(),
            "datetime": get_datetime(),
            "memory": get_memory_usage(),
            "cpu": get_cpu_info()
        }
    elif detail_type == "os":
        return get_os_details()
    elif detail_type == "datetime":
        return get_datetime()
    elif detail_type == "memory":
        return get_memory_usage()
    elif detail_type == "cpu":
        return get_cpu_info()
    else:
        raise ValueError(f"Invalid detail type: {detail_type}. Must be one of: os, datetime, memory, cpu, all")