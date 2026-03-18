#!/usr/bin/env python3
"""
Script to locally regenerate a Google OAuth token.json with both Contacts and Calendar scopes.
Run this on your Mac with your `credentials.json` available.
"""
import os
import argparse
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Scopes for both Contacts and Calendar
SCOPES = [
    'https://www.googleapis.com/auth/contacts',
    'https://www.googleapis.com/auth/calendar'
]

def update_token(cred_file, token_file):
    if not os.path.exists(cred_file):
        print(f"ERROR: {cred_file} not found!")
        print("Please ensure credentials.json is in the expected path.")
        return

    # Delete existing token to force re-authentication with new scopes
    if os.path.exists(token_file):
        print(f"Removing old {token_file} to update scopes...")
        os.remove(token_file)

    print("Opening browser to authenticate with Google...")
    print(f"Scopes being requested: {', '.join(SCOPES)}")
    
    flow = InstalledAppFlow.from_client_secrets_file(cred_file, SCOPES)
    creds = flow.run_local_server(port=0)

    # Ensure parent directory exists
    os.makedirs(os.path.dirname(token_file), exist_ok=True)

    # Save credentials
    with open(token_file, 'w') as token:
        token.write(creds.to_json())
    
    print(f"\n✅ Successfully generated new {token_file} with updated scopes!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Refresh Google OAuth Token with Calendar Scopes')
    parser.add_argument('--credentials', default='oys_contacts/env_files/credentials.json', help='Path to your Google credentials file')
    parser.add_argument('--token', default='oys_contacts/env_files/token.json', help='Output path for the generated token file')
    args = parser.parse_args()
    
    # Resolve absolute paths if necessary (optional here but good for clarity)
    update_token(args.credentials, args.token)
