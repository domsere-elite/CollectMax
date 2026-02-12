import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
url = f"{os.getenv('SUPABASE_URL')}/auth/v1/.well-known/jwks.json"
api_key = os.getenv('SUPABASE_ANON_KEY')
print(f"Fetching from: {url}")
r = requests.get(url, headers={'apikey': api_key, 'Authorization': f'Bearer {api_key}'})
print(f"Status: {r.status_code}")
try:
    print(json.dumps(r.json(), indent=2))
except:
    print(r.text)
