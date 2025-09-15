import ollama
import requests
import json

MCP_URL = "http://192.168.0.29:8000/"
MODEL = "qwen3:4b-instruct"

def discover_tools():
    payload = {"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1}
    try:
        resp = requests.post(MCP_URL, json=payload).json()
        return resp.get("result", {}).get("tools", [])
    except Exception as e:
        print(f"Tool discovery failed: {e}")
        return []

def invoke_mcp(tool_name, args):
    if isinstance(args, str):
        args = json.loads(args)
    payload = {"jsonrpc": "2.0", "method": "tools/call", "params": {"name": tool_name, "arguments": args}, "id": 2}
    try:
        resp = requests.post(MCP_URL, json=payload).json()
        if "error" in resp:
            return f"Server error: {resp['error']['message']}"
        return resp.get("result", {}).get("structuredContent", "No structured output")
    except Exception as e:
        return f"MCP call failed: {e}"

tools = discover_tools()
ollama_tools = [{"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["inputSchema"]}} for t in tools]

while True:
    user_input = input("You: ")
    messages = [
        {"role": "system", "content": "You are a concise assistant. Use tools directly and return only the tool output or a brief summary. No extra commentary."},
        {"role": "user", "content": user_input}
    ]

    try:
        response = ollama.chat(model=MODEL, messages=messages, tools=ollama_tools)

        if "tool_calls" in response.get("message", {}):
            for call in response["message"]["tool_calls"]:
                func = call["function"]
                result = invoke_mcp(func["name"], func["arguments"])
                messages.append({"role": "tool", "content": json.dumps(result)})

            response = ollama.chat(model=MODEL, messages=messages)

        print("AI:", response["message"]["content"])
    except Exception as e:
        print(f"Chat error: {e}")
