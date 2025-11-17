"""
Gmail Export Script
Exports emails from Gmail using Gmail API
Requires: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
"""

import os
import base64
import json
from email import message_from_bytes
from email.utils import parsedate_to_datetime
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailExporter:
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        """
        Initialize Gmail exporter
        
        Args:
            credentials_file: Path to OAuth2 credentials JSON file
            token_file: Path to store/load OAuth2 token
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        
    def authenticate(self):
        """Authenticate with Gmail API"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    print(f"Error: {self.credentials_file} not found!")
                    print("Please download OAuth2 credentials from Google Cloud Console:")
                    print("1. Go to https://console.cloud.google.com/")
                    print("2. Create a project or select existing")
                    print("3. Enable Gmail API")
                    print("4. Create OAuth2 credentials (Desktop app)")
                    print("5. Download as credentials.json")
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
        return True
    
    def export_emails(self, query='', max_results=1000, output_dir='./gmail_export'):
        """
        Export emails from Gmail
        
        Args:
            query: Gmail search query (e.g., 'from:support@example.com', 'label:customer-service')
            max_results: Maximum number of emails to export
            output_dir: Directory to save EML files
        """
        if not self.service:
            print("Not authenticated. Call authenticate() first.")
            return
        
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # List messages
            results = self.service.users().messages().list(
                userId='me', q=query, maxResults=max_results).execute()
            messages = results.get('messages', [])
            
            print(f"Found {len(messages)} messages. Exporting...")
            
            for i, msg in enumerate(messages):
                try:
                    # Get full message
                    message = self.service.users().messages().get(
                        userId='me', id=msg['id'], format='raw').execute()
                    
                    # Decode message
                    msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
                    email_msg = message_from_bytes(msg_str)
                    
                    # Generate filename
                    subject = email_msg.get('Subject', 'No Subject')
                    date = email_msg.get('Date', '')
                    safe_subject = "".join(c for c in subject if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
                    filename = f"{i:05d}_{safe_subject}.eml"
                    filepath = os.path.join(output_dir, filename)
                    
                    # Save as EML
                    with open(filepath, 'wb') as f:
                        f.write(msg_str)
                    
                    if (i + 1) % 10 == 0:
                        print(f"Exported {i + 1}/{len(messages)} messages...")
                
                except Exception as e:
                    print(f"Error exporting message {msg['id']}: {e}")
                    continue
            
            print(f"\nExport complete! Saved {len(messages)} emails to {output_dir}")
            
        except HttpError as error:
            print(f"An error occurred: {error}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Export emails from Gmail')
    parser.add_argument('--query', default='', help='Gmail search query (e.g., "label:customer-service")')
    parser.add_argument('--max', type=int, default=1000, help='Maximum number of emails to export')
    parser.add_argument('--output', default='./gmail_export', help='Output directory')
    parser.add_argument('--credentials', default='credentials.json', help='OAuth2 credentials file')
    parser.add_argument('--token', default='token.json', help='OAuth2 token file')
    
    args = parser.parse_args()
    
    exporter = GmailExporter(args.credentials, args.token)
    
    if exporter.authenticate():
        exporter.export_emails(query=args.query, max_results=args.max, output_dir=args.output)
    else:
        print("Authentication failed. Please check your credentials.")

if __name__ == '__main__':
    main()

