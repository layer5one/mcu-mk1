TOOL_METADATA = {
    "name": "read_file",
    "title": "Read File",
    "description": "Read text content from a file"
}

def run(path: str):
    with open(path, "r") as f:
        return {"content": f.read()}
