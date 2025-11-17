"""
Outlook/Microsoft 365 Email Connector
Connects to Outlook using Microsoft Graph API and intelligently filters emails
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from msal import ConfidentialClientApplication
import requests

class OutlookConnector:
    def __init__(self, client_id: str, client_secret: str, tenant_id: str):
        """
        Initialize Outlook connector
        
        Args:
            client_id: Azure AD Application (client) ID
            client_secret: Azure AD Application secret
            tenant_id: Azure AD Directory (tenant) ID
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.scope = ["https://graph.microsoft.com/.default"]
        self.access_token = None
        
        # Initialize MSAL app
        self.app = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=self.authority
        )
    
    def authenticate(self) -> bool:
        """Authenticate and get access token"""
        try:
            result = self.app.acquire_token_for_client(scopes=self.scope)
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                return True
            else:
                print(f"Authentication failed: {result.get('error_description', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make API request to Microsoft Graph"""
        if not self.access_token:
            if not self.authenticate():
                return None
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"https://graph.microsoft.com/v1.0/{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request error: {e}")
            # Try to refresh token if expired
            if response.status_code == 401:
                if self.authenticate():
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    response = requests.get(url, headers=headers, params=params)
                    return response.json() if response.status_code == 200 else None
            return None
    
    def list_mailboxes(self) -> List[Dict]:
        """List available mailboxes"""
        result = self._make_request("users")
        if result and "value" in result:
            return [
                {
                    "id": user.get("id"),
                    "email": user.get("mail") or user.get("userPrincipalName"),
                    "displayName": user.get("displayName")
                }
                for user in result["value"]
            ]
        return []
    
    def list_folders(self, mailbox_email: str) -> List[Dict]:
        """List folders in a mailbox"""
        endpoint = f"users/{mailbox_email}/mailFolders"
        result = self._make_request(endpoint)
        if result and "value" in result:
            return [
                {
                    "id": folder.get("id"),
                    "name": folder.get("displayName"),
                    "totalItemCount": folder.get("totalItemCount", 0)
                }
                for folder in result["value"]
            ]
        return []
    
    def search_emails(
        self,
        mailbox_email: str,
        folder_id: Optional[str] = None,
        search_query: Optional[str] = None,
        from_address: Optional[str] = None,
        from_name: Optional[str] = None,
        to_address: Optional[str] = None,
        to_name: Optional[str] = None,
        cc_address: Optional[str] = None,
        cc_name: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        has_attachments: Optional[bool] = None,
        min_length: int = 50,
        max_results: int = 1000
    ) -> List[Dict]:
        """
        Search and filter emails intelligently
        
        Args:
            mailbox_email: Email address of the mailbox
            folder_id: Specific folder ID (None for Inbox)
            search_query: Search query (searches subject and body)
            from_address: Filter by sender email address
            from_name: Filter by sender name (partial match)
            to_address: Filter by recipient email address
            to_name: Filter by recipient name (partial match)
            cc_address: Filter by CC email address
            cc_name: Filter by CC name (partial match)
            date_from: Filter emails from this date
            date_to: Filter emails to this date
            has_attachments: Filter by attachment presence
            min_length: Minimum email body length (characters)
            max_results: Maximum number of results
            
        Returns:
            List of email dictionaries with metadata
        """
        # Build filter query
        filters = []
        
        if date_from:
            filters.append(f"receivedDateTime ge {date_from.isoformat()}")
        if date_to:
            filters.append(f"receivedDateTime le {date_to.isoformat()}")
        if from_address:
            filters.append(f"from/emailAddress/address eq '{from_address}'")
        if has_attachments is not None:
            filters.append(f"hasAttachments eq {str(has_attachments).lower()}")
        
        # Build endpoint
        if folder_id:
            endpoint = f"users/{mailbox_email}/mailFolders/{folder_id}/messages"
        else:
            endpoint = f"users/{mailbox_email}/messages"
        
        params = {
            "$top": min(max_results, 999),  # Graph API limit
            "$orderby": "receivedDateTime desc",
            "$select": "id,subject,from,toRecipients,ccRecipients,receivedDateTime,bodyPreview,body,hasAttachments,importance,isRead"
        }
        
        if filters:
            params["$filter"] = " and ".join(filters)
        
        if search_query:
            params["$search"] = f'"{search_query}"'
        
        emails = []
        result = self._make_request(endpoint, params=params)
        
        if result and "value" in result:
            for msg in result["value"]:
                # Get full body content
                email_id = msg.get("id")
                full_email = self._get_email_content(mailbox_email, email_id)
                
                if full_email:
                    body = full_email.get("body", {}).get("content", "")
                    body_preview = msg.get("bodyPreview", "")
                    
                    # Filter by minimum length
                    if len(body) < min_length and len(body_preview) < min_length:
                        continue
                    
                    from_addr = msg.get("from", {}).get("emailAddress", {}).get("address", "Unknown")
                    from_name = msg.get("from", {}).get("emailAddress", {}).get("name", "")
                    to_recipients = [r.get("emailAddress", {}).get("address", "") for r in msg.get("toRecipients", [])]
                    to_names = [r.get("emailAddress", {}).get("name", "") for r in msg.get("toRecipients", [])]
                    cc_recipients = [r.get("emailAddress", {}).get("address", "") for r in msg.get("ccRecipients", [])]
                    cc_names = [r.get("emailAddress", {}).get("name", "") for r in msg.get("ccRecipients", [])]
                    
                    email_data = {
                        "id": email_id,
                        "subject": msg.get("subject", "No Subject"),
                        "from": from_addr,
                        "from_name": from_name,
                        "to": to_recipients,
                        "to_names": to_names,
                        "cc": cc_recipients,
                        "cc_names": cc_names,
                        "date": msg.get("receivedDateTime"),
                        "body": body or body_preview,
                        "body_preview": body_preview,
                        "has_attachments": msg.get("hasAttachments", False),
                        "importance": msg.get("importance", "normal"),
                        "is_read": msg.get("isRead", False),
                        "relevance_score": self._calculate_relevance_score(msg, body)
                    }
                    emails.append(email_data)
        
        # Apply filters after fetching
        if from_name:
            from_name_lower = from_name.lower()
            emails = [
                email for email in emails
                if from_name_lower in email.get("from_name", "").lower() or 
                   from_name_lower in email.get("from", "").lower()
            ]
        
        if to_address:
            to_address_lower = to_address.lower()
            emails = [
                email for email in emails
                if any(to_address_lower in to_email.lower() for to_email in email.get("to", []))
            ]
        
        if to_name:
            to_name_lower = to_name.lower()
            emails = [
                email for email in emails
                if any(to_name_lower in to_email.lower() for to_email in email.get("to", [])) or
                   any(to_name_lower in to_name.lower() for to_name in email.get("to_names", []))
            ]
        
        if cc_address:
            cc_address_lower = cc_address.lower()
            emails = [
                email for email in emails
                if any(cc_address_lower in cc_email.lower() for cc_email in email.get("cc", []))
            ]
        
        if cc_name:
            cc_name_lower = cc_name.lower()
            emails = [
                email for email in emails
                if any(cc_name_lower in cc_email.lower() for cc_email in email.get("cc", [])) or
                   any(cc_name_lower in cc_name.lower() for cc_name in email.get("cc_names", []))
            ]
        
        # Sort by relevance score
        emails.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return emails[:max_results]
    
    def _get_email_content(self, mailbox_email: str, email_id: str) -> Optional[Dict]:
        """Get full email content"""
        endpoint = f"users/{mailbox_email}/messages/{email_id}"
        params = {"$select": "body,bodyPreview"}
        return self._make_request(endpoint, params=params)
    
    def _calculate_relevance_score(self, msg: Dict, body: str) -> float:
        """
        Calculate relevance score for email filtering
        Higher score = more relevant for customer service training
        """
        score = 0.0
        
        subject = msg.get("subject", "").lower()
        body_lower = body.lower()
        
        # Customer service keywords (positive)
        customer_service_keywords = [
            "support", "help", "question", "issue", "problem", "complaint",
            "request", "inquiry", "assistance", "service", "customer",
            "order", "refund", "return", "cancel", "payment", "billing",
            "account", "login", "password", "delivery", "shipping"
        ]
        
        for keyword in customer_service_keywords:
            if keyword in subject:
                score += 2.0
            if keyword in body_lower:
                score += 1.0
        
        # Marketing/automated emails (negative)
        marketing_keywords = [
            "unsubscribe", "newsletter", "promotion", "sale", "discount",
            "marketing", "advertisement", "spam"
        ]
        
        for keyword in marketing_keywords:
            if keyword in subject or keyword in body_lower:
                score -= 3.0
        
        # Length bonus (longer emails often more informative)
        if len(body) > 500:
            score += 1.0
        if len(body) > 1000:
            score += 1.0
        
        # Importance bonus
        importance = msg.get("importance", "normal")
        if importance == "high":
            score += 1.5
        elif importance == "low":
            score -= 0.5
        
        # Unread bonus (might indicate active issues)
        if not msg.get("isRead", False):
            score += 0.5
        
        return max(score, 0.0)  # Don't go negative
    
    def export_selected_emails(self, emails: List[Dict], output_dir: str) -> int:
        """
        Export selected emails to EML format files
        
        Args:
            emails: List of email dictionaries
            output_dir: Directory to save EML files
            
        Returns:
            Number of emails exported
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        count = 0
        for email in emails:
            try:
                # Create EML content
                eml_content = self._create_eml_content(email)
                
                # Save to file
                safe_subject = "".join(c for c in email["subject"] if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
                filename = f"{count:05d}_{safe_subject}.eml"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(eml_content)
                
                count += 1
            except Exception as e:
                print(f"Error exporting email {email.get('id')}: {e}")
        
        return count
    
    def _create_eml_content(self, email: Dict) -> str:
        """Create EML file content from email dictionary"""
        from email.mime.text import MIMEText
        from email.utils import formatdate
        
        body = email.get("body", email.get("body_preview", ""))
        is_html = "<html" in body.lower() or "<body" in body.lower()
        
        msg = MIMEText(body, "html" if is_html else "plain", "utf-8")
        msg["Subject"] = email.get("subject", "No Subject")
        
        from_addr = email.get("from", "Unknown")
        from_name = email.get("from_name", "")
        if from_name:
            msg["From"] = f"{from_name} <{from_addr}>"
        else:
            msg["From"] = from_addr
        
        to_addrs = email.get("to", [])
        if to_addrs:
            msg["To"] = ", ".join(to_addrs) if isinstance(to_addrs, list) else str(to_addrs)
        
        try:
            date_str = email.get("date", "")
            if date_str:
                # Handle ISO format dates
                if 'Z' in date_str:
                    date_str = date_str.replace('Z', '+00:00')
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                msg["Date"] = formatdate(dt.timestamp())
        except:
            msg["Date"] = formatdate()
        
        return msg.as_string()

def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Connect to Outlook and filter emails')
    parser.add_argument('--client-id', required=True, help='Azure AD Client ID')
    parser.add_argument('--client-secret', required=True, help='Azure AD Client Secret')
    parser.add_argument('--tenant-id', required=True, help='Azure AD Tenant ID')
    parser.add_argument('--mailbox', required=True, help='Mailbox email address')
    parser.add_argument('--output', default='./outlook_export', help='Output directory')
    parser.add_argument('--max-results', type=int, default=500, help='Maximum emails to export')
    parser.add_argument('--days', type=int, default=365, help='Number of days to look back')
    
    args = parser.parse_args()
    
    connector = OutlookConnector(args.client_id, args.client_secret, args.tenant_id)
    
    if not connector.authenticate():
        print("Failed to authenticate")
        return
    
    date_from = datetime.now() - timedelta(days=args.days)
    
    print(f"Searching emails in {args.mailbox}...")
    emails = connector.search_emails(
        mailbox_email=args.mailbox,
        date_from=date_from,
        max_results=args.max_results
    )
    
    print(f"Found {len(emails)} relevant emails")
    print(f"Top 10 by relevance:")
    for i, email in enumerate(emails[:10], 1):
        print(f"{i}. [{email['relevance_score']:.1f}] {email['subject'][:60]}")
    
    print(f"\nExporting to {args.output}...")
    count = connector.export_selected_emails(emails, args.output)
    print(f"Exported {count} emails")

if __name__ == '__main__':
    main()

