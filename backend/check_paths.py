import requests
import json

try:
    r = requests.get("http://localhost:8000/openapi.json")
    if r.status_code == 200:
        spec = r.json()
        paths = spec.get("paths", {})
        print("Paths found in openapi.json containing 'debts':")
        for p in paths:
            if "debts" in p:
                print(f"- {p} (Methods: {list(paths[p].keys())})")
    else:
        print(f"Failed to fetch openapi.json. Status: {r.status_code}")
except Exception as e:
    print(f"Error: {e}")
