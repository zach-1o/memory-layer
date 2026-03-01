import urllib.request
import json

# Using the endpoint from the successfully deployed API
URL = "https://dep-76fd1739-d3f2-4c76-9a21-6526c74e2b03.tyzo.nodeops.app/api/projects"
HEADERS = {
    "x-api-key": "skp_EBRved1N-UHnqhBOTcZwwMjQoIK9KVEnFZQ3lK1ZjRU",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def check_projects():
    req = urllib.request.Request(URL, headers=HEADERS, method="GET")
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("Projects on server:", json.dumps(data, indent=2))
            return data
    except Exception as e:
        print("Error checking projects:", e)
        if hasattr(e, 'read'):
            print(e.read().decode())
        return None

if __name__ == "__main__":
    check_projects()
