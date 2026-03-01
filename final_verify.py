import urllib.request
import json
import time

URL = "http://localhost:8000/mcp"
HEADERS = {
    "x-api-key": "skp_tvEr5wZhTxx-TIU7CkeE1lrPOflp0tEvywNM6geSRcY",
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
            print(f"Response: {e.read().decode()}")
        return None

if __name__ == "__main__":
    project_id = "final_graph_verify"
    
    print("--- STEP 1: Adding Observation ---")
    observation = "The Bird class uses its physics_constants.py module for gravity calculation. It imports Vector2 from pygame.math and depends on the GameLoop to trigger update()."
    entities = ["Bird", "physics_constants.py", "Vector2", "pygame.math", "GameLoop"]
    
    res = call_tool("add_observation", {
        "project_id": project_id,
        "content": observation,
        "entities": entities
    })
    print("Result:", json.dumps(res, indent=2))
    
    if res and "result" in res:
        print("\n--- STEP 2: Waiting for Gemini extraction (10s) ---")
        time.sleep(10)
        
        print("\n--- STEP 3: Checking Graph for extracted relations ---")
        graph_res = call_tool("get_entity", {
            "project_id": project_id,
            "entity_name": "Bird"
        })
        print("Bird Graph Result:", json.dumps(graph_res, indent=2))
    else:
        print("Failed to add observation.")
