import shutil

TOOL_METADATA = {
    "name": "get_disk",
    "title": "Disk Usage",
    "description": "Get disk usage statistics for the root filesystem"
}

def run(path: str = "/"):
    usage = shutil.disk_usage(path)
    return {
        "total": usage.total,
        "used": usage.used,
        "free": usage.free
    }
