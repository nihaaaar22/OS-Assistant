import platform
import psutil
import datetime

def get_os_details():
    """Get operating system details"""
    os_info = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }
    
    return f"""Operating System Details:
System: {os_info['system']}
Release: {os_info['release']}
Version: {os_info['version']}
Machine: {os_info['machine']}
Processor: {os_info['processor']}"""

def get_datetime():
    """Get current date and time"""
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    timezone = datetime.datetime.now().astimezone().tzname()
    
    return f"""Date and Time:
Date: {date}
Time: {time}
Timezone: {timezone}"""

def get_memory_usage():
    """Get memory usage details"""
    memory = psutil.virtual_memory()
    total = f"{memory.total / (1024**3):.2f} GB"
    available = f"{memory.available / (1024**3):.2f} GB"
    used = f"{memory.used / (1024**3):.2f} GB"
    percent = f"{memory.percent}%"
    
    return f"""Memory Usage:
Total: {total}
Available: {available}
Used: {used}
Usage Percent: {percent}"""

def get_cpu_info():
    """Get CPU information"""
    cpu_freq = psutil.cpu_freq()
    current_freq = f"{cpu_freq.current:.2f} MHz" if cpu_freq else "N/A"
    min_freq = f"{cpu_freq.min:.2f} MHz" if cpu_freq and cpu_freq.min else "N/A"
    max_freq = f"{cpu_freq.max:.2f} MHz" if cpu_freq and cpu_freq.max else "N/A"
    
    return f"""CPU Information:
Physical Cores: {psutil.cpu_count(logical=False)}
Total Cores: {psutil.cpu_count(logical=True)}
Current Frequency: {current_freq}
Min Frequency: {min_freq}
Max Frequency: {max_freq}
CPU Usage: {psutil.cpu_percent()}%"""

def system_details(detail_type="all"):
    """
    Get system details based on the requested type.
    
    Args:
        detail_type (str): Type of system detail to retrieve (os, datetime, memory, cpu, all)
    
    Returns:
        str: Requested system details as formatted string
    """
    detail_type = detail_type.lower()
    
    if detail_type == "all":
        return f"""{get_os_details()}

{get_datetime()}

{get_memory_usage()}

{get_cpu_info()}"""
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