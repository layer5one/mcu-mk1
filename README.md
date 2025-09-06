# MCP Model Control Server

This repository contains a scaffold for a **Model Context Protocol (MCP)**-compliant tool server. The server is designed to plug in different language models (local or remote) and expose a unified set of tools via the MCP standard. It uses JSON-RPC 2.0 over HTTP as the communication layer:contentReference[oaicite:7]{index=7}, implementing tool discovery and invocation methods as specified by MCP (version 2025-06-18).

## Features

- **JSON-RPC 2.0 API:** Communication between clients (LLM agents) and this server follows JSON-RPC 2.0 messaging:contentReference[oaicite:8]{index=8}. The server uses FastAPI to handle HTTP POST requests at the root endpoint (`/`) containing JSON-RPC payloads.
- **Tool Registration:** Tools are modular and reside in the `tools/` directory as separate Python modules. On startup and before each request, the server automatically loads or reloads these modules, registering any tool functions for availability.
- **Tool Discovery (`tools/list`):** Clients can query the server for available tools. The `tools/list` method responds with a list of tools, including each tool’s `name`, `title`, `description`, and JSON Schema definitions for its inputs and outputs:contentReference[oaicite:9]{index=9}. (Pagination support is stubbed with `nextCursor=None` since the tool list is small.)
- **Tool Invocation (`tools/call`):** The `tools/call` method allows a client to execute a specific tool by name. The request includes the tool name and an `arguments` object. The server will validate the `arguments` against the tool’s input schema, execute the tool’s `run` function, and return the result:contentReference[oaicite:10]{index=10}.
- **Structured Responses:** If a tool defines an output schema, the server returns structured data. The result includes both a machine-readable JSON object under `structuredContent` and a stringified version of the same data under `content` (as a Text block) for backward compatibility:contentReference[oaicite:11]{index=11}. This follows the MCP spec for structured tool outputs, allowing clients and LLMs to parse results reliably.
- **Session Management:** Basic session support is included. You can create new sessions via `session/create`, which returns a unique `session_id`. This `session_id` can be sent in subsequent requests (as a parameter) to partition conversations or tool usages by session. The server tracks session IDs but does not yet persist any session-specific context. A `session/end` method is provided to explicitly terminate a session (removing it from the server’s tracking).
- **Hot-Reloading Tools:** The server supports hot-reloading of tools. New Python files added to the `tools/` directory are automatically detected and loaded at runtime without restarting the server. Similarly, modifications to existing tool files are picked up on the fly. The server will also unload tools if their files are removed.
- **Logging & Error Handling:** All requests and tool invocations are logged. The server returns JSON-RPC error responses for protocol-level issues (e.g. invalid JSON-RPC format, unknown methods, invalid params). Tool execution errors (exceptions during tool run) are caught and returned within the JSON-RPC result with an `isError:true` flag, so the client/LLM can distinguish them from successful outputs:contentReference[oaicite:12]{index=12}.
- **Extensibility:** The project is structured for easy extension. New tools can be added by creating a module in `tools/` and a corresponding JSON schema in `schemas/`. The `NonMCPModelAdapter` stub (in `main.py`) shows how one might integrate non-MCP-speaking models by translating their outputs into MCP calls – this could be expanded to support local models that do not natively produce JSON tool calls.

## Running the Server

### Prerequisites

- Python 3.10+ (and pip) or Docker/Docker Compose.
- (If running locally) Install the Python dependencies listed in `requirements.txt`.

### Local Setup

1. **Install dependencies:**  
   ```bash
   pip install -r requirements.txt
