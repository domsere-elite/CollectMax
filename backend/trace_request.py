import requests
import json

# Dummy token that might pass if the backend is not strictly validating against Supabase for simple checks
# Or I'll just use the mock logic I saw earlier in test_backend_error.py
# Wait, I'll just try to hit the endpoint with a dummy token to see if it even shows up in the backend console.

url = "http://localhost:8000/api/v1/debts/5/email"
payload = {"email": "dominic@eliteportfoliomgt.com"}
headers = {"Authorization": "Bearer MOCK_TOKEN"}

try:
    print(f"Sending request to {url}...")
    response = requests.put(url, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
