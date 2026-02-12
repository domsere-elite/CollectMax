import requests

url = "http://localhost:8000/api/v1/debts/5/email"
response = requests.put(url, json={"email": "test@example.com"})
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")
