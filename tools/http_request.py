import requests

TOOL_METADATA = {
    "name": "http_request",
    "title": "HTTP Request",
    "description": "Perform a GET request to a given URL"
}

def run(url: str):
    resp = requests.get(url, timeout=5)
    return {"status_code": resp.status_code, "body": resp.text[:500]}
