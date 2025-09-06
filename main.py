from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import importlib
import os, sys
import logging
import uuid
import json
from typing import Any, Dict

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCPServer")

class SessionManager:
    """Manages session identifiers for concurrent clients."""
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {}  # placeholder for session-specific data
        logger.info(f"Session created: {session_id}")
        return session_id
    def get_session(self, session_id: str) -> Dict:
        return self.sessions.get(session_id)
    def end_session(self, session_id: str) -> bool:
        """End a session. Returns True if ended, False if session ID was not found."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session ended: {session_id}")
            return True
        return False

class ToolsManager:
    """Dynamically loads and manages tools from the tools/ directory."""
    def __init__(self, tools_dir: str = "tools", schemas_dir: str = "schemas"):
        self.tools_dir = tools_dir
        self.schemas_dir = schemas_dir
        self.registry: Dict[str, Dict] = {}    # Maps tool name to tool metadata and callable
        self.modules: Dict[str, Any] = {}      # Maps tool name to imported module
        self.load_tools()
    def load_tools(self):
        """Import all tool modules and register their metadata and run functions."""
        logger.info("Loading tools...")
        if not os.path.isdir(self.tools_dir):
            logger.warning(f"Tools directory '{self.tools_dir}' not found.")
            return
        # Import each Python file in the tools directory (except dunder files)
        for filename in os.listdir(self.tools_dir):
            if not filename.endswith(".py") or filename.startswith("__"):
                continue
            tool_name = filename[:-3]
            module_name = f"{self.tools_dir.replace(os.sep, '.')}.{tool_name}"
            try:
                module = importlib.import_module(module_name)
            except ImportError as e:
                logger.error(f"Failed to import tool module '{tool_name}': {e}")
                continue
            # Prepare tool metadata
            meta: Dict[str, Any] = {}
            if hasattr(module, "TOOL_METADATA"):
                # Copy declared metadata (name, description, title, etc.)
                meta.update(module.TOOL_METADATA)
            # Ensure required metadata fields
            meta["name"] = meta.get("name", tool_name)
            meta["description"] = meta.get("description", "")
            meta["title"] = meta.get("title", meta["name"])
            # Load JSON schemas for input/output if available
            input_schema_file = os.path.join(self.schemas_dir, f"{tool_name}_input.json")
            output_schema_file = os.path.join(self.schemas_dir, f"{tool_name}_output.json")
            if os.path.isfile(input_schema_file):
                with open(input_schema_file, "r") as f:
                    meta["inputSchema"] = json.load(f)
            else:
                # Default to an empty object schema for no inputs
                meta["inputSchema"] = {"type": "object", "properties": {}, "required": []}
            if os.path.isfile(output_schema_file):
                with open(output_schema_file, "r") as f:
                    meta["outputSchema"] = json.load(f)
            # Get the tool's execution function
            if hasattr(module, "run"):
                meta["run"] = module.run
            else:
                logger.warning(f"Tool module '{tool_name}' has no run() function; skipping.")
                continue
            # Register tool
            self.registry[tool_name] = meta
            self.modules[tool_name] = module
            logger.info(f"Registered tool: {tool_name}")
    def refresh_tools(self):
        """Reload tool modules and update registry (supports hot-reloading new or changed tools)."""
        if not os.path.isdir(self.tools_dir):
            return
        logger.info("Refreshing tools...")
        current_tools = set(self.registry.keys())
        found_files = {f[:-3] for f in os.listdir(self.tools_dir) if f.endswith(".py") and not f.startswith("__")}
        # Reload existing tools
        for tool_name in found_files:
            module_name = f"{self.tools_dir.replace(os.sep, '.')}.{tool_name}"
            if tool_name in self.modules:
                try:
                    # Reload the module if already loaded
                    module = importlib.reload(self.modules[tool_name])
                    logger.info(f"Reloaded tool module: {tool_name}")
                except ImportError as e:
                    logger.error(f"Failed to reload tool '{tool_name}': {e}")
                    continue
            else:
                try:
                    module = importlib.import_module(module_name)
                    logger.info(f"Loaded new tool module: {tool_name}")
                except ImportError as e:
                    logger.error(f"Failed to import new tool '{tool_name}': {e}")
                    continue
                self.modules[tool_name] = module
            # Update tool metadata
            meta: Dict[str, Any] = {}
            if hasattr(module, "TOOL_METADATA"):
                meta.update(module.TOOL_METADATA)
            meta["name"] = meta.get("name", tool_name)
            meta["description"] = meta.get("description", "")
            meta["title"] = meta.get("title", meta["name"])
            # Load schemas (if present)
            input_schema_path = os.path.join(self.schemas_dir, f"{tool_name}_input.json")
            output_schema_path = os.path.join(self.schemas_dir, f"{tool_name}_output.json")
            if os.path.isfile(input_schema_path):
                with open(input_schema_path, "r") as f:
                    meta["inputSchema"] = json.load(f)
            else:
                meta["inputSchema"] = {"type": "object", "properties": {}, "required": []}
            if os.path.isfile(output_schema_path):
                with open(output_schema_path, "r") as f:
                    meta["outputSchema"] = json.load(f)
            # Verify run function
            if hasattr(module, "run"):
                meta["run"] = module.run
            else:
                logger.warning(f"Tool '{tool_name}' missing run() after reload; removing.")
                meta = None
            # Update registry entry if valid
            if meta:
                self.registry[tool_name] = meta
        # Remove tools that no longer exist in the directory
        removed_tools = current_tools - found_files
        for tool_name in removed_tools:
            logger.info(f"Removing tool (module no longer present): {tool_name}")
            if tool_name in self.registry:
                del self.registry[tool_name]
            if tool_name in self.modules:
                sys.modules.pop(f"{self.tools_dir.replace(os.sep, '.')}.{tool_name}", None)
                del self.modules[tool_name]

class NonMCPModelAdapter:
    """Stub adapter that translates a raw LLM output into an MCP-formatted tool call."""
    def translate(self, prompt: str) -> Dict:
        # In a real implementation, analyze the prompt and generate a tool call.
        # Here we return a dummy call to 'get_status' regardless of input.
        logger.info(f"Translating non-MCP prompt: {prompt!r}")
        return {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": "get_status",
                "arguments": {}
            }
        }

# Initialize managers
session_manager = SessionManager()
tools_manager = ToolsManager()

# Create FastAPI app
app = FastAPI(title="MCP Tool Server", version="0.1.0")

@app.post("/")
async def handle_mcp(request: Request):
    """
    Main endpoint for MCP interactions (JSON-RPC 2.0 messages).
    Accepts JSON payloads (single request or batch) and returns JSON-RPC responses.
    """
    payload = await request.json()
    result = process_request(payload)
    # If process_request returned a Response (e.g. already JSONResponse), return it directly
    if isinstance(result, JSONResponse):
        return result
    # Otherwise, convert result (dict or list) to JSONResponse
    return JSONResponse(result)

def process_request(payload: Any) -> Any:
    """Dispatch a JSON-RPC request or batch of requests."""
    # Hot-reload tools before processing each request to pick up changes
    tools_manager.refresh_tools()
    if isinstance(payload, list):
        # Batch of requests
        responses = []
        for req in payload:
            resp = handle_single_request(req)
            if resp is not None:  # omit responses for notifications
                responses.append(resp)
        return responses
    else:
        return handle_single_request(payload)

def handle_single_request(req: Dict) -> Dict:
    """Handle a single JSON-RPC request and return the response."""
    # Validate JSON-RPC base structure
    if req.get("jsonrpc") != "2.0":
        # Malformed request
        return {"jsonrpc": "2.0", "id": req.get("id"), "error": {"code": -32600, "message": "Invalid Request"}}
    method = req.get("method")
    params = req.get("params", {})
    req_id = req.get("id")
    # If no id is provided, it's a JSON-RPC notification (no response expected)
    if req_id is None:
        logger.info(f"Received notification: method={method}, params={params}")
        return None  # no response
    logger.info(f"Received request: id={req_id}, method={method}")
    # Session handling: verify or create sessions
    if isinstance(params, dict) and "session_id" in params:
        sid = params["session_id"]
        if sid and session_manager.get_session(sid) is None:
            # Unknown session ID provided
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": f"Unknown session_id: {sid}"}}
    # Built-in methods:
    if method in ("session/create", "create_session"):
        # Start a new session
        sid = session_manager.create_session()
        return {"jsonrpc": "2.0", "id": req_id, "result": {"session_id": sid}}
    if method in ("session/end", "end_session"):
        # End an existing session
        sid = params.get("session_id")
        success = session_manager.end_session(sid)
        return {"jsonrpc": "2.0", "id": req_id, "result": {"success": success}}
    if method == "tools/list":
        # Return list of available tools and their metadata (with schemas)
        tools_info = []
        for name, meta in tools_manager.registry.items():
            tool_entry = {
                "name": name,
                "title": meta.get("title", name),
                "description": meta.get("description", ""),
                "inputSchema": meta.get("inputSchema", {})
            }
            if "outputSchema" in meta:
                tool_entry["outputSchema"] = meta["outputSchema"]
            tools_info.append(tool_entry)
        result = {"tools": tools_info, "nextCursor": None}
        return {"jsonrpc": "2.0", "id": req_id, "result": result}
    if method == "tools/call":
        # Invoke a specific tool by name
        if not isinstance(params, dict):
            # params must be an object with "name" and "arguments"
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": "Invalid params"}}
        tool_name = params.get("name")
        args = params.get("arguments", {})
        if not tool_name or tool_name not in tools_manager.registry:
            # Unknown tool requested
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"}}
        tool_meta = tools_manager.registry[tool_name]
        # Validate arguments against the tool's input schema
        schema = tool_meta.get("inputSchema")
        if schema:
            try:
                import jsonschema
                jsonschema.validate(instance=args, schema=schema)
            except Exception as e:
                logger.warning(f"Input validation failed for tool '{tool_name}': {e}")
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": f"Invalid parameters: {e}"}}
        # Execute the tool function
        try:
            output = tool_meta["run"](**args)
        except Exception as e:
            logger.error(f"Exception while executing tool '{tool_name}': {e}")
            # Return tool execution error within result (not as a protocol error)
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": f"Tool execution error: {e}"}],
                "isError": True
            }}
        # Validate and format output
        result_payload: Dict[str, Any] = {}
        if "outputSchema" in tool_meta:
            # If an output schema is defined, validate the output
            try:
                import jsonschema
                jsonschema.validate(instance=output, schema=tool_meta["outputSchema"])
            except Exception as e:
                logger.error(f"Output validation failed for tool '{tool_name}': {e}")
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": "Tool output validation failed"}}
            # Provide structured content and text content
            result_payload["structuredContent"] = output
            result_payload["content"] = [{
                "type": "text",
                "text": json.dumps(output)
            }]
        else:
            # No structured schema – return output as text content only
            if isinstance(output, str):
                result_payload["content"] = [{"type": "text", "text": output}]
            else:
                result_payload["content"] = [{"type": "text", "text": json.dumps(output)}]
        # Mark successful execution
        result_payload["isError"] = False
        return {"jsonrpc": "2.0", "id": req_id, "result": result_payload}
    # If method is not recognized by this server:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}
