import socket

TOOL_METADATA = {
    "name": "get_network",
    "title": "Network Info",
    "description": "Get basic hostname and IP info"
}

def run():
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    return {"hostname": hostname, "ip": ip}
