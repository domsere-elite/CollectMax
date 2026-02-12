import requests

url = "http://localhost:8000/api/v1/debts/5/email"
# We need an auth token. I'll try to get it from .env or just see if I get a 401 vs 404.
# If I get a 404 without a token, it might be uvicorn. 
# But the route has require_auth dependency.

try:
    # First, just test if the route exists (GET might 405, but 404 means it's not there)
    r = requests.get(url)
    print(f"GET status: {r.status_code}") # Should be 405 or 401
    
    # Try PUT without token
    r = requests.put(url, json={"email": "test@example.com"})
    print(f"PUT (no token) status: {r.status_code}") # Should be 401
except Exception as e:
    print(f"Error: {e}")
