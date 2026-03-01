import requests
import json

URL = "http://localhost:8000/mcp"
HEADERS = {
    "x-api-key": "skp_5EXaSU0DA2uE53KrU0f7OKvyjtiITK6PbQmkBrUisZk",
    "Content-Type": "application/json",
}

def call_tool(name, arguments):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": name,
            "arguments": arguments
        }
    }
    response = requests.post(URL, headers=HEADERS, json=payload)
    return response.json()

print("--- Listing Entities for 'dashboard-test' ---")
# Use search_index to see what's in the semantic/graph index
result = call_tool("search_index", {"query": "Memory Layer", "project_id": "dashboard-test"})
print(f"Entities Found: {json.dumps(result, indent=2)}")
