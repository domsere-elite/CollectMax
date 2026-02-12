import os
from sendgrid import SendGridAPIClient
import sys

# Load from .env manually to be sure
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("SENDGRID_API_KEY")
from_email = os.getenv("SENDGRID_FROM_EMAIL")

print(f"Testing SendGrid API Key: {api_key[:10]}...")
print(f"From Email: {from_email}")

sg = SendGridAPIClient(api_key)

try:
    # Try to fetch account details or something simple
    response = sg.client.scopes.get()
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✓ SendGrid API Key is VALID")
    else:
        print(f"✗ SendGrid API Key returned status {response.status_code}")
        print(response.body)
except Exception as e:
    print(f"✗ SendGrid error: {e}")
    sys.exit(1)
