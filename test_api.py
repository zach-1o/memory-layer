import urllib.request
import json

URL = "https://dep-76fd1739-d3f2-4c76-9a21-6526c74e2b03.tyzo.nodeops.app/mcp"
HEADERS = {
    "x-api-key": "skp_EBRved1N-UHnqhBOTcZwwMjQoIK9KVEnFZQ3lK1ZjRU",
    "Content-Type": "application/json"
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
            resp_data = json.loads(response.read().decode("utf-8"))
            print(f"Tool {name} Response:", json.dumps(resp_data, indent=2))
            return resp_data
    except Exception as e:
        print(f"Error calling {name}:", e)
        if hasattr(e, 'read'):
            print(e.read().decode())
        return None

if __name__ == "__main__":
    search_resp = call_tool("search_index", {"project_id": "memory-layer", "query": "flappy bird"})
    
    if search_resp:
        try:
            results_str = search_resp["result"]["content"][0]["text"]
            results = json.loads(results_str)
            if isinstance(results, list) and len(results) > 0:
                obs_id = results[0]["id"]
                call_tool("retrieve_node", {"project_id": "memory-layer", "obs_id": obs_id})
            else:
                print("No search results found.")
        except Exception as e:
            print("Failed to parse or retrieve node:", e)
