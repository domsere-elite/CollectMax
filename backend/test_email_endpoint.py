import requests
import json

# Test 1: Verify endpoint exists (should get 401 without auth)
print("=" * 60)
print("TEST 1: Verify endpoint exists")
print("=" * 60)
url = "http://localhost:8000/api/v1/debts/5/email"
try:
    response = requests.put(url, json={"email": "test@example.com"})
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 401:
        print("✓ Endpoint exists and requires authentication")
    elif response.status_code == 404:
        print("✗ Endpoint not found - routing issue")
    else:
        print(f"? Unexpected status code: {response.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Check if backend is running
print("\n" + "=" * 60)
print("TEST 2: Check backend health")
print("=" * 60)
try:
    response = requests.get("http://localhost:8000/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print("✓ Backend is running")
except Exception as e:
    print(f"✗ Backend not accessible: {e}")

# Test 3: Check OpenAPI spec
print("\n" + "=" * 60)
print("TEST 3: Verify route in OpenAPI spec")
print("=" * 60)
try:
    response = requests.get("http://localhost:8000/openapi.json")
    spec = response.json()
    paths = spec.get("paths", {})
    email_route = "/api/v1/debts/{debt_id}/email"
    if email_route in paths:
        print(f"✓ Route '{email_route}' found in OpenAPI spec")
        print(f"  Methods: {list(paths[email_route].keys())}")
        if "put" in paths[email_route]:
            print("  ✓ PUT method available")
            # Check if it requires auth
            put_spec = paths[email_route]["put"]
            if "security" in put_spec or any("security" in str(v) for v in put_spec.values()):
                print("  ✓ Endpoint requires authentication")
        else:
            print("  ✗ PUT method not found")
    else:
        print(f"✗ Route '{email_route}' NOT found in OpenAPI spec")
        print(f"Available routes with 'debts': {[p for p in paths if 'debts' in p]}")
except Exception as e:
    print(f"✗ Error checking OpenAPI: {e}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("If all tests pass, the issue is likely:")
print("1. Frontend not sending authentication token")
print("2. Token is invalid/expired")
print("3. CORS blocking the request")
