import psutil

TOOL_METADATA = {
    "name": "list_processes",
    "title": "List Processes",
    "description": "List running processes"
}

def run(limit: int = 10):
    procs = []
    for p in psutil.process_iter(attrs=["pid", "name"]):
        if len(procs) >= limit:
            break
        procs.append(p.info)
    return {"processes": procs}
