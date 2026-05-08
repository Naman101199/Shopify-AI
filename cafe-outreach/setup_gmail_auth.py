"""
Run this ONCE to authorize Gmail access and create pipeline labels.

Steps:
1. Download credentials.json from Google Cloud Console
   (APIs & Services > Credentials > OAuth 2.0 Client ID > Desktop App)
2. Place credentials.json in this directory
3. Run: python setup_gmail_auth.py
4. A browser window opens - log in and grant access
5. token.json is saved automatically for future unattended runs
"""

import os
from dotenv import load_dotenv
from pipeline.gmail_client import GmailClient

load_dotenv()

if __name__ == "__main__":
    creds_path = os.environ.get("GMAIL_CREDS_PATH", "credentials.json")
    token_path = os.environ.get("GMAIL_TOKEN_PATH", "token.json")

    if not os.path.exists(creds_path):
        print(f"ERROR: {creds_path} not found.")
        print("Download it from: Google Cloud Console > APIs & Services > Credentials")
        print("Create an OAuth 2.0 Client ID (Desktop App) and download the JSON.")
        exit(1)

    print("Opening browser for Gmail authorization...")
    client = GmailClient(token_path=token_path, creds_path=creds_path)
    client.ensure_labels()
    print()
    print("Authorization complete. token.json saved.")
    print("Gmail pipeline labels created successfully.")
    print()
    print("You can now run the daily pipeline:")
    print("  python pipeline.py")
    print()
    print("To schedule it daily at 9am:")
    print("  bash cron_setup.sh")
