import os

TOOL_METADATA = {
    "name": "list_dir",
    "title": "List Directory",
    "description": "List files in a directory"
}

def run(path: str = "."):
    return {"files": os.listdir(path)}
