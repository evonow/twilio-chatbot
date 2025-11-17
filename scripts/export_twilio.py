"""
Twilio SMS Export Script
Exports SMS messages from Twilio account
"""

import os
from twilio.rest import Client
from datetime import datetime
import json
from dotenv import load_dotenv

load_dotenv()

class TwilioExporter:
    def __init__(self):
        """Initialize Twilio exporter"""
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        if not account_sid or not auth_token:
            raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in .env")
        
        self.client = Client(account_sid, auth_token)
    
    def export_messages(self, date_from=None, date_to=None, phone_number=None, output_file='twilio_messages.json'):
        """
        Export SMS messages from Twilio
        
        Args:
            date_from: Start date (datetime or string 'YYYY-MM-DD')
            date_to: End date (datetime or string 'YYYY-MM-DD')
            phone_number: Filter by phone number (optional)
            output_file: Output JSON file path
        """
        messages = []
        
        # Build query parameters
        params = {}
        if date_from:
            if isinstance(date_from, str):
                date_from = datetime.strptime(date_from, '%Y-%m-%d')
            params['date_sent_after'] = date_from
        if date_to:
            if isinstance(date_to, str):
                date_to = datetime.strptime(date_to, '%Y-%m-%d')
            params['date_sent_before'] = date_to
        if phone_number:
            params['from'] = phone_number
        
        print("Fetching messages from Twilio...")
        
        try:
            # Fetch messages
            twilio_messages = self.client.messages.list(**params)
            
            for msg in twilio_messages:
                message_data = {
                    'sid': msg.sid,
                    'from': msg.from_,
                    'to': msg.to,
                    'body': msg.body,
                    'date': msg.date_sent.isoformat() if msg.date_sent else None,
                    'status': msg.status,
                    'direction': msg.direction
                }
                messages.append(message_data)
            
            # Save to JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
            
            print(f"Exported {len(messages)} messages to {output_file}")
            return messages
        
        except Exception as e:
            print(f"Error exporting messages: {e}")
            return []

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Export SMS messages from Twilio')
    parser.add_argument('--from-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--to-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--phone', help='Filter by phone number')
    parser.add_argument('--output', default='twilio_messages.json', help='Output JSON file')
    
    args = parser.parse_args()
    
    exporter = TwilioExporter()
    exporter.export_messages(
        date_from=args.from_date,
        date_to=args.to_date,
        phone_number=args.phone,
        output_file=args.output
    )

if __name__ == '__main__':
    main()

