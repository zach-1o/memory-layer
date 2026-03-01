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

# 1. Store a huge observation
observation = """
The Memory Layer Dashboard is a complex React application built with Vite. 
It features a high-performance Knowledge Graph visualization using React Force Graph. 
The system architecture follows a decoupled pattern where the FastAPI backend (Memory Layer API) 
manages three distinct memory layers: Episodic (handled by ChromaDB), Semantic (handled by Vector Embeddings), 
and Graph (handled by entity relation extraction). 
The project uses HSL-based CSS variables for a premium 'Midnight' dark theme. 
Key components include GraphView for 3D/2D visualization, MemoryList for chronological streams, 
and ProjectDetail for granular tenant management. 
The authentication system supports dynamic API key registration via environment variables.
"""

print("--- STEP 1: Storing Large Observation ---")
store_result = call_tool("add_observation", {"content": observation, "project_id": "dashboard-test"})
print(f"Store Result: {json.dumps(store_result, indent=2)}")

# 2. Wait for processing
print("\nWaiting for extraction...")
time.sleep(10)

# 3. Retrieve Entity
print("\n--- STEP 2: Retrieving 'FastAPI' Entity ---")
retrieve_result = call_tool("get_entity", {"entity_name": "FastAPI", "project_id": "dashboard-test"})
print(f"Retrieve Result: {json.dumps(retrieve_result, indent=2)}")
