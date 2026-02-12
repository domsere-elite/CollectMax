import argparse
import os
from sendgrid.helpers.eventwebhook import EventWebhook


def main():
    parser = argparse.ArgumentParser(description="Verify SendGrid signed webhook payload")
    parser.add_argument("--body", required=True, help="Path to raw webhook payload file")
    parser.add_argument("--signature", required=True, help="Signature header value")
    parser.add_argument("--timestamp", required=True, help="Timestamp header value")
    args = parser.parse_args()

    secret = os.getenv("SENDGRID_EVENT_WEBHOOK_KEY")
    if not secret:
        raise SystemExit("SENDGRID_EVENT_WEBHOOK_KEY not set")

    with open(args.body, "rb") as f:
        body = f.read()

    verifier = EventWebhook()
    valid = verifier.verify_signature(body, args.signature, args.timestamp, secret)
    print("valid" if valid else "invalid")


if __name__ == "__main__":
    main()
