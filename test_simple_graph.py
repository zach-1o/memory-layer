import requests
import json
import time

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

# 1. Store a very simple, direct observation
observation = "The Memory Layer uses FastAPI for its high-performance backend API."

print("--- STEP 1: Storing Simple Observation ---")
store_result = call_tool("add_observation", {"content": observation, "project_id": "dashboard-test", "entities": ["FastAPI", "Memory Layer"]})
print(f"Store Result: {json.dumps(store_result, indent=2)}")

# 2. Wait for processing
print("\nWaiting for extraction...")
time.sleep(3)

# 3. Retrieve Entity
print("\n--- STEP 2: Retrieving 'FastAPI' Entity ---")
retrieve_result = call_tool("get_entity", {"entity_name": "FastAPI", "project_id": "dashboard-test"})
print(f"Retrieve Result: {json.dumps(retrieve_result, indent=2)}")
