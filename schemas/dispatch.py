# Save this as dispatch.py

import ollama
import requests
import json
import re

# --- Configuration ---
MCP_URL = "http://localhost:8000/"
# Use the custom agent model with baked-in instructions
MODEL = "mcu-agent:0.1" 

class DispatcherAgent:
    def __init__(self, mcp_url, model):
        self.mcp_url = mcp_url
        self.model = model
        self.conversation_history = []
        self.tools = self._discover_tools()
        if not self.tools:
            raise ConnectionError("Could not discover tools. Is the MCP server running?")
        self.tool_definitions_text = self._format_tools_for_prompting()
        print(f"✅ Dispatcher Agent initialized. Discovered {len(self.tools)} tools.")
        print("-" * 50)

    def _discover_tools(self):
        payload = {"jsonrpc": "2.0", "method": "tools/list", "id": "discover"}
        try:
            return requests.post(self.mcp_url, json=payload).json().get("result", {}).get("tools", [])
        except requests.RequestException as e:
            return []

    def _format_tools_for_prompting(self):
        """Creates a string block describing the available tools for the LLM."""
        text_block = "You have access to the following tools. To use a tool, you must respond with a JSON object in the format: {\"tool_to_call\": {\"name\": \"<tool_name>\", \"arguments\": {<args>}}}. Do not add any other text.\n\n"
        for tool in self.tools:
            text_block += f"- Tool: {tool['name']}\n"
            text_block += f"  Description: {tool['description']}\n"
            if "inputSchema" in tool and tool["inputSchema"].get("properties"):
                text_block += f"  Arguments Schema: {json.dumps(tool['inputSchema']['properties'])}\n"
        return text_block

    def _invoke_mcp(self, tool_name, args):
        print(f"  ⚙️  Dispatcher: Calling tool '{tool_name}'...")
        payload = {
            "jsonrpc": "2.0", "method": "tools/call",
            "params": {"name": tool_name, "arguments": args}, "id": f"call_{tool_name}"
        }
        try:
            resp = requests.post(self.mcp_url, json=payload).json()
            result = resp.get("result", {})
            if result.get("isError"):
                return {"status": "error", "message": result.get("content", "Unknown error")}
            return result.get("structuredContent", result.get("content", "No output"))
        except requests.RequestException as e:
            return {"status": "error", "message": f"MCP call failed: {e}"}

    def _get_next_llm_response(self):
        """Sends the current history to the LLM and gets its next action or final answer."""
        response = ollama.chat(model=self.model, messages=self.conversation_history)
        return response['message']['content']

    def _parse_llm_response(self, response_text):
        """Tries to find and parse a JSON tool call from the model's text response."""
        try:
            # Using a more robust regex to find JSON, even with leading/trailing text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                if "tool_to_call" in data and "name" in data["tool_to_call"]:
                    return data["tool_to_call"]
        except (json.JSONDecodeError, KeyError):
            return None # Not a valid tool call
        return None # Not a tool call

    def run_task(self, task):
        print(f"🎯 Dispatcher: Received new task: {task}\n")
        
        # We construct the initial prompt with the tool definitions and the task.
        initial_prompt = f"{self.tool_definitions_text}\n--- CURRENT TASK ---\n{task}"
        
        self.conversation_history = [{"role": "user", "content": initial_prompt}]

        # The main agent loop
        for i in range(10): # Add a max turn limit to prevent infinite loops
            print(f"--- Turn {i+1} ---")
            print("  🤔 Dispatcher: Asking model for next action...")
            
            llm_response_text = self._get_next_llm_response()
            self.conversation_history.append({"role": "assistant", "content": llm_response_text})
            
            print(f"  🤖 Model Output: {llm_response_text}")

            tool_call = self._parse_llm_response(llm_response_text)

            if tool_call:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("arguments", {})
                tool_output = self._invoke_mcp(tool_name, tool_args)
                
                print(f"  ↪️  Dispatcher: Got tool output: {tool_output}")
                
                # Append the result to the history for the model's context
                self.conversation_history.append({
                    "role": "tool",
                    "content": json.dumps({"result": tool_output})
                })
            else:
                print("\n✅ Dispatcher: Model provided a final answer. Task complete.")
                print("-" * 50)
                return llm_response_text
        
        print("\n⚠️ Dispatcher: Reached max turns. Task may be incomplete.")
        return "Agent reached its turn limit."

def setup_test_files():
    """Creates dummy files for the agent to work with."""
    with open("user_profile.txt", "w") as f:
        f.write("- My favorite color is blue.\n- I live in Phoenix.")
    print("✅ Test file 'user_profile.txt' created.")

if __name__ == "__main__":
    setup_test_files()
    
    # Define the "Bootstrap Brain" task
    bootstrap_task = """
    Learn about the user.
    1. Read the file 'user_profile.txt'.
    2. Extract the user's favorite color.
    3. Store this fact using the 'memory' tool with the key 'favorite_color'.
    4. To confirm, retrieve the fact you just stored.
    """
    
    # Remember to add the `memory` tool to your MCU server!
    
    try:
        agent = DispatcherAgent(MCP_URL, MODEL)
        final_answer = agent.run_task(bootstrap_task)
        print("\n--- FINAL AGENT RESPONSE ---")
        print(final_answer)
    except Exception as e:
        print(f"❌ An error occurred: {e}")
