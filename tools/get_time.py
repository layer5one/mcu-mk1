import datetime

TOOL_METADATA = {
    "name": "get_time",
    "title": "Current Time",
    "description": "Get current UTC time"
}

def run():
    return {"utc": datetime.datetime.utcnow().isoformat()}
