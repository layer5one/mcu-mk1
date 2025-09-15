import os

TOOL_METADATA = {
    "name": "env_vars",
    "title": "Environment Variables",
    "description": "List environment variables"
}

def run():
    return {"env": dict(os.environ)}
