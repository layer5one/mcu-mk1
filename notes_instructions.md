## Running the Server

### Prerequisites

- Python 3.10+ (and pip) or Docker/Docker Compose.
- (If running locally) Install the Python dependencies listed in `requirements.txt`.

### Local Setup

1. **Install dependencies:**  
   ```bash
   pip install -r requirements.txt
Start the server:
You can launch the FastAPI server with Uvicorn:
bash
Copy code
uvicorn main:app --host 0.0.0.0 --port 8000
This will start the MCP server on port 8000.
Verify health:
The server provides a basic health check at GET /health. Visit http://localhost:8000/health in a browser or use curl:
bash
Copy code
curl http://localhost:8000/health
You should get a response {"status": "ok"}.
Docker Setup
Build the image:
bash
Copy code
docker build -t mcp-server .
Run the container:
bash
Copy code
docker run -p 8000:8000 mcp-server
This will run the server inside a container, listening on port 8000. Alternatively, use Docker Compose:
bash
Copy code
docker-compose up
This will build the image (if not already built) and start the container as defined in docker-compose.yml.
Usage Examples
Once the server is running, you can send JSON-RPC requests to it. The HTTP endpoint is the root (/), expecting a JSON body. Below are examples of using curl with JSON payloads:
List available tools:
Request:
bash
Copy code
curl -X POST http://localhost:8000/ \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
Response (example):
json
Copy code
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "get_status",
        "title": "System Status",
        "description": "Get current CPU and memory usage of the system",
        "inputSchema": { ... },
        "outputSchema": { ... }
      }
    ],
    "nextCursor": null
  }
}
This shows that the server has one tool (get_status) available. The inputSchema and outputSchema are included (shown as { ... } above for brevity) – these define the expected input parameters and output format for the tool.
Call a tool (get_status):
Request:
bash
Copy code
curl -X POST http://localhost:8000/ \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_status","arguments":{"verbose":false}}}'
Response (example):
json
Copy code
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"cpu_percent\": 12.5, \"memory_percent\": 45.8}"
      }
    ],
    "structuredContent": {
      "cpu_percent": 12.5,
      "memory_percent": 45.8
    },
    "isError": false
  }
}
In this example, the get_status tool was invoked. The result contains a structuredContent object with the CPU and memory usage, and a corresponding text block in content (the JSON string)
modelcontextprotocol.io
. The isError: false indicates the tool executed successfully. If the verbose flag were true, the output would include an additional field (e.g., cpu_count).
Session usage:
To use sessions, first obtain a session ID:
bash
Copy code
curl -X POST http://localhost:8000/ \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":3,"method":"session/create","params":{}}'
Response:
json
Copy code
{ "jsonrpc": "2.0", "id": 3, "result": { "session_id": "<your-session-uuid>" } }
You can then include this session_id in subsequent calls under the "params" for tool requests, for example:
json
Copy code
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "get_status",
    "arguments": { "verbose": false },
    "session_id": "<your-session-uuid>"
  }
}
The server will recognize the session (or return an error if the session ID is not known). Ending a session can be done via session/end with the session_id.
Adding New Tools
You can extend this MCP server by adding new tools:
Create the tool code: Write a new Python module in the tools/ directory (e.g., tools/my_tool.py). In that module, define a run(...) function that implements your tool’s functionality. Optionally, include a TOOL_METADATA dict with fields like "name", "description", and "title". If TOOL_METADATA is not provided, the server will use defaults or attributes NAME/DESCRIPTION if present.
Define JSON Schemas: For inputs and outputs of the tool, create schema files under schemas/ named <toolname>_input.json and <toolname>_output.json. Follow JSON Schema standards to describe the expected structure of the tool’s arguments and result. These schemas will be loaded by the server and provided to clients (and used for validation).
No server restart needed: The next time a request hits the server (e.g., a tools/list or tools/call), the ToolsManager will auto-detect the new module. The tool will appear in the tools/list output and become invokable via tools/call. (The server logs will indicate that a new tool module was loaded.)
Note: Removing or renaming tool files will likewise be detected – the server will stop listing removed tools. During runtime, tools are refreshed before each request; for a high-throughput scenario, you might want to refine this (e.g., refresh on a timed interval or via a specific admin command) to avoid unnecessary overhead.
Next Steps
This scaffold provides the foundation for a full-featured MCP server:
Model Integration: You can integrate actual LLMs (local or API-based) by extending the NonMCPModelAdapter to interpret model outputs and by routing model requests to this server. For example, a wrapper could take an LLM’s raw reply and use NonMCPModelAdapter.translate() to produce a JSON-RPC call, then feed it to the server and return the tool’s result back to the model.
Tool Security & Permissions: In a real deployment, consider adding permission checks for certain tools (especially those that perform file or network operations) and user confirmations as recommended by the MCP spec’s security guidelines.
Persistent Session Context: The session mechanism can be expanded to store conversation or tool usage context (e.g., caching previous results or user-specific data) to truly isolate sessions.
Feel free to use this project as a starting point for building a robust multi-tool AI assistant system. With MCP as the backbone, you can ensure your tools are exposed in a standardized way to any compliant AI clients
forgecode.dev
, making it easier to orchestrate complex workflows across different models and data sources.