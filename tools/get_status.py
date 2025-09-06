import psutil

# Metadata for the tool (name, description, etc.)
TOOL_METADATA = {
    "name": "get_status",
    "title": "System Status",
    "description": "Get current CPU and memory usage of the system"
}

def run(verbose: bool = False):
    """
    Example tool function that returns system status.
    If 'verbose' is True, additional details are included.
    """
    # Gather system metrics
    cpu_percentage = psutil.cpu_percent(interval=0.1)    # CPU utilization in percentage
    memory_percentage = psutil.virtual_memory().percent  # Memory utilization in percentage
    result = {
        "cpu_percent": cpu_percentage,
        "memory_percent": memory_percentage
    }
    if verbose:
        # Include extra information when verbose flag is set
        result["cpu_count"] = psutil.cpu_count(logical=True)
    return result
