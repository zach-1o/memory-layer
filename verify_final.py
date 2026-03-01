import urllib.request
import json
import time

URL = "https://dep-1a79b239-1164-4426-a754-050885175f44.tyzo.nodeops.app/mcp"
HEADERS = {
    "x-api-key": "skp_EBRved1N-UHnqhBOTcZwwMjQoIK9KVEnFZQ3lK1ZjRU",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def call_tool(name, args):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": name,
            "arguments": args
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(URL, data=data, headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Error calling {name}: {e}")
        if hasattr(e, 'read'):
            print(f"Response Body: {e.read().decode()}")
        return None

if __name__ == "__main__":
    project_id = "final-test-proj-v2"
    
    print("Adding observation...")
    obs_resp = call_tool("add_observation", {
        "project_id": project_id,
        "content": "The CollisionManager class uses a quadtree to optimize collision detection between the Bird and Pipe objects. It imports the Quadtree module and triggers a 'collision' event on the EventBus.",
        "entities": ["CollisionManager", "Bird", "Pipe", "Quadtree", "EventBus"]
    })
    print("Add Observation Response:", json.dumps(obs_resp, indent=2))
    
    if obs_resp:
        print("Waiting for extraction (15s)...")
        time.sleep(15)
        
        print("Checking 'CollisionManager' in Graph...")
        graph_resp = call_tool("get_entity", {
            "project_id": project_id,
            "entity_name": "CollisionManager"
        })
        print("Graph Response:", json.dumps(graph_resp, indent=2))
