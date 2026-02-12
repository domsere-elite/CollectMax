import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Test with a mock token to see backend error
url = "http://localhost:8000/api/v1/debts/5/email"
headers = {
    "Authorization": "Bearer fake_token_to_trigger_backend_processing",
    "Content-Type": "application/json"
}
data = {"email": "test@example.com"}

print("Testing email update endpoint...")
print(f"URL: {url}")
print(f"Headers: {headers}")
print(f"Data: {data}")
print()

try:
    response = requests.put(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
