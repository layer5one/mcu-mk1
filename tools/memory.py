# tools/memory.py
import os
import json
import datetime

MEMORY_FILE = "agent_memory.json"

TOOL_METADATA = {
    "name": "memory",
    "title": "Agent Memory",
    "description": "Store or retrieve key-value information from the agent's long-term memory."
}

def _load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def run(operation: str, key: str, value: str = None):
    memories = _load_memory()
    if operation == "store":
        if not value:
            return {"status": "error", "message": "Value is required for store operation."}
        memories[key] = {
            "value": value,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        with open(MEMORY_FILE, "w") as f:
            json.dump(memories, f, indent=2)
        return {"status": "success", "key": key}
    elif operation == "retrieve":
        return {"status": "success", "data": memories.get(key)}
    else:
        return {"status": "error", "message": "Unsupported operation. Use 'store' or 'retrieve'."}
