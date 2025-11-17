"""
Outlook for Mac Local Connector
Uses AppleScript to interact with Outlook.app directly on macOS
"""

import subprocess
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

class OutlookLocalMac:
    def __init__(self):
        """Initialize local Outlook connector"""
        self.applescript_template = """
        tell application "Microsoft Outlook"
            try
                {script_content}
            on error errMsg
                return "ERROR: " & errMsg
            end try
        end tell
        """
    
    def _run_applescript(self, script: str, timeout: Optional[int] = None) -> str:
        """Execute AppleScript and return result"""
        # Clean up the script content - remove any tell/end tell if present
        script_content = script.strip()
        
        # Build the full script with proper error handling
        full_script = f"""
tell application "Microsoft Outlook"
    try
        {script_content}
    on error errMsg
        return "ERROR: " & errMsg
    end try
end tell
"""
        
        try:
            result = subprocess.run(
                ["osascript", "-e", full_script],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                raise Exception(f"AppleScript error: {error_msg}")
            
            output = result.stdout.strip()
            if output.startswith("ERROR:"):
                raise Exception(output)
            
            return output
        except subprocess.TimeoutExpired:
            raise Exception("AppleScript execution timed out")
        except Exception as e:
            raise Exception(f"Failed to execute AppleScript: {e}")
    
    def check_outlook_running(self) -> bool:
        """Check if Outlook is running"""
        script = """
if application "Microsoft Outlook" is running then
    return "true"
else
    return "false"
end if
"""
        result = self._run_applescript(script)
        return result.lower() == "true"
    
    def list_accounts(self) -> List[Dict]:
        """List all email accounts in Outlook by examining folders"""
        # Since Outlook doesn't expose accounts directly, we'll infer them from folders
        # Look for common folder patterns that indicate different accounts
        script = """
set accountList to {}
set seenAccounts to {}
try
    set folderCount to count of mail folders
    repeat with i from 1 to folderCount
        try
            set aFolder to mail folder i
            set folderName to name of aFolder
            set folderMsgCount to count of messages in aFolder
            if folderName is "Inbox" and folderMsgCount > 0 then
                try
                    set accountInfo to folderName & " (Inbox: " & folderMsgCount & " messages)"
                    if accountInfo is not in seenAccounts then
                        set end of accountList to accountInfo & "|" & folderMsgCount
                        set end of seenAccounts to accountInfo
                    end if
                end try
            end if
        on error
        end try
    end repeat
end try
if (count of accountList) is 0 then
    set end of accountList to "Default Account|0"
end if
return accountList
"""
        
        result = self._run_applescript(script)
        accounts = []
        
        if result and not result.startswith("ERROR"):
            if result:
                lines = result.replace(", ", ",").split(",")
                for line in lines:
                    line = line.strip()
                    if "|" in line:
                        parts = line.split("|", 1)
                        accounts.append({
                            "name": parts[0].strip(),
                            "email": ""
                        })
                    elif line and not line.startswith("ERROR"):
                        accounts.append({
                            "name": line,
                            "email": ""
                        })
        
        # If still no accounts, add a default
        if not accounts:
            accounts.append({"name": "Default Account", "email": ""})
        
        return accounts
    
    def list_folders(self, account_name: Optional[str] = None) -> List[Dict]:
        """List folders in Outlook - accesses all mail folders directly"""
        script = """
set folderList to {}
set seenFolders to {}
try
    set folderCount to count of mail folders
    repeat with i from 1 to folderCount
        try
            set aFolder to mail folder i
            set folderName to name of aFolder
            if folderName is not "" and folderName is not in seenFolders then
                set folderMsgCount to count of messages in aFolder
                set end of folderList to folderName & "|" & folderMsgCount
                set end of seenFolders to folderName
            end if
        on error
        end try
    end repeat
end try
return folderList
"""
        
        result = self._run_applescript(script)
        folders = []
        seen_names = set()
        
        if result and not result.startswith("ERROR"):
            if result:
                lines = result.replace(", ", ",").split(",")
                for line in lines:
                    line = line.strip()
                    if "|" in line:
                        parts = line.split("|", 1)
                        folder_name = parts[0].strip()
                        # Only add unique folder names
                        if folder_name and folder_name not in seen_names:
                            try:
                                count = int(parts[1].strip()) if parts[1].strip().isdigit() else 0
                            except:
                                count = 0
                            folders.append({
                                "name": folder_name,
                                "count": count
                            })
                            seen_names.add(folder_name)
                    elif line and not line.startswith("ERROR") and line not in seen_names:
                        folders.append({
                            "name": line,
                            "count": 0
                        })
                        seen_names.add(line)
        
        # Sort by name for easier browsing
        folders.sort(key=lambda x: x["name"])
        
        return folders
    
    def search_emails(
        self,
        folder_name: str = "Inbox",
        account_name: Optional[str] = None,
        search_query: Optional[str] = None,
        from_address: Optional[str] = None,
        from_name: Optional[str] = None,
        to_address: Optional[str] = None,
        to_name: Optional[str] = None,
        cc_address: Optional[str] = None,
        cc_name: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        max_results: int = 500,
        min_length: int = 50
    ) -> List[Dict]:
        """
        Search emails in Outlook
        
        Args:
            folder_name: Folder to search (default: "Inbox")
            account_name: Account name (None for default)
            search_query: Search text
            from_address: Filter by sender email
            from_name: Filter by sender name
            to_address: Filter by recipient email
            to_name: Filter by recipient name
            cc_address: Filter by CC email
            cc_name: Filter by CC name
            date_from: Filter from date
            date_to: Filter to date
            max_results: Maximum results
            min_length: Minimum email body length
            
        Returns:
            List of email dictionaries
        """
        # Build search script - access folder directly by name
        # Escape folder name in case it has special characters
        safe_folder_name = folder_name.replace('"', '\\"')
        
        script = f"""
set emailList to {{}}
set targetFolder to mail folder "{safe_folder_name}"

set messageCount to count of messages in targetFolder
set processedCount to 0
set maxCount to {max_results}

repeat with aMessage in messages of targetFolder
    if processedCount >= maxCount then exit repeat
    
    try
        set msgSubject to subject of aMessage
        set msgSender to sender of aMessage
        set senderName to name of msgSender
        set senderEmail to address of msgSender
        
        -- Extract TO recipients
        set msgToRecipients to every recipient of aMessage
        set toRecipientList to {{}}
        repeat with aRecipient in msgToRecipients
            try
                set recipientType to class of aRecipient
                -- Check if it's a TO recipient (not CC or BCC)
                -- In Outlook, we can check recipient type, but AppleScript may not expose this directly
                -- So we'll get all recipients and separate them later if possible
                set recipientName to name of aRecipient
                set recipientEmail to address of aRecipient
                set end of toRecipientList to recipientName & " <" & recipientEmail & ">"
            on error
            end try
        end repeat
        
        -- Extract CC recipients (try to access CC field if available)
        set ccRecipientList to {{}}
        try
            set msgCcRecipients to every CC recipient of aMessage
            repeat with aRecipient in msgCcRecipients
                try
                    set recipientName to name of aRecipient
                    set recipientEmail to address of aRecipient
                    set end of ccRecipientList to recipientName & " <" & recipientEmail & ">"
                on error
                end try
            end repeat
        on error
            -- If CC recipients aren't accessible separately, we'll parse from all recipients
        end try
        
        set msgDate to time received of aMessage
        set msgContent to content of aMessage
        set msgRead to read status of aMessage
        set msgImportance to importance of aMessage
        
        set AppleScript's text item delimiters to ", "
        set toRecipientStr to toRecipientList as string
        set ccRecipientStr to ccRecipientList as string
        set AppleScript's text item delimiters to ""
        
        set emailData to msgSubject & "|||" & senderName & "|||" & senderEmail & "|||" & toRecipientStr & "|||" & ccRecipientStr & "|||" & (msgDate as string) & "|||" & msgContent & "|||" & (msgRead as string) & "|||" & (msgImportance as string)
        set end of emailList to emailData
        set processedCount to processedCount + 1
    on error
    end try
end repeat

return emailList
"""
        
        # Use longer timeout for large result sets
        timeout = 120 if max_results > 100 else 60
        result = self._run_applescript(script, timeout=timeout)
        emails = []
        import re
        
        if result and not result.startswith("ERROR"):
            for line in result.split(", "):
                if "|||" in line:
                    parts = line.split("|||")
                    # New format: subject|||senderName|||senderEmail|||toRecipients|||ccRecipients|||date|||body|||isRead|||importance
                    if len(parts) >= 9:
                        try:
                            sender_name = parts[1].strip()
                            sender_email = parts[2].strip()
                            to_recipients_str = parts[3].strip()
                            cc_recipients_str = parts[4].strip()
                            date_str = parts[5].strip()
                            body = parts[6].strip()
                            is_read = parts[7].strip().lower() == "true"
                            importance = parts[8].strip()
                            
                            # Parse date
                            email_date = self._parse_date(date_str)
                            
                            # Check date filters
                            if date_from and email_date < date_from:
                                continue
                            if date_to and email_date > date_to:
                                continue
                            
                            # Check body length
                            if len(body) < min_length:
                                continue
                            
                            # Parse TO recipients
                            to_recipient_emails = []
                            to_recipient_names = []
                            if to_recipients_str:
                                recipient_pattern = r'([^<]+)\s*<([^>]+)>'
                                matches = re.findall(recipient_pattern, to_recipients_str)
                                for name, email in matches:
                                    to_recipient_emails.append(email.strip())
                                    to_recipient_names.append(name.strip())
                            
                            # Parse CC recipients
                            cc_recipient_emails = []
                            cc_recipient_names = []
                            if cc_recipients_str:
                                recipient_pattern = r'([^<]+)\s*<([^>]+)>'
                                matches = re.findall(recipient_pattern, cc_recipients_str)
                                for name, email in matches:
                                    cc_recipient_emails.append(email.strip())
                                    cc_recipient_names.append(name.strip())
                            
                            # Apply sender filters
                            if from_address and from_address.lower() not in sender_email.lower():
                                continue
                            if from_name and from_name.lower() not in sender_name.lower() and from_name.lower() not in sender_email.lower():
                                continue
                            
                            # Apply TO recipient filters
                            if to_address:
                                if not any(to_address.lower() in rec_email.lower() for rec_email in to_recipient_emails):
                                    continue
                            if to_name:
                                if not any(to_name.lower() in rec_name.lower() or to_name.lower() in rec_email.lower() 
                                         for rec_name, rec_email in zip(to_recipient_names, to_recipient_emails)):
                                    continue
                            
                            # Apply CC recipient filters
                            if cc_address:
                                if not any(cc_address.lower() in rec_email.lower() for rec_email in cc_recipient_emails):
                                    continue
                            if cc_name:
                                if not any(cc_name.lower() in rec_name.lower() or cc_name.lower() in rec_email.lower() 
                                         for rec_name, rec_email in zip(cc_recipient_names, cc_recipient_emails)):
                                    continue
                            
                            # Calculate relevance score
                            relevance = self._calculate_relevance_score(
                                parts[0], body, importance
                            )
                            
                            email_data = {
                                "id": f"local_{hash(line)}",
                                "subject": parts[0].strip(),
                                "from": sender_email,
                                "from_name": sender_name,
                                "to": to_recipient_emails,
                                "to_names": to_recipient_names,
                                "cc": cc_recipient_emails,
                                "cc_names": cc_recipient_names,
                                "date": email_date.isoformat(),
                                "body": body,
                                "body_preview": body[:200] + "..." if len(body) > 200 else body,
                                "is_read": is_read,
                                "importance": importance,
                                "relevance_score": relevance
                            }
                            emails.append(email_data)
                        except Exception as e:
                            print(f"Error parsing email: {e}")
                            continue
                    elif len(parts) >= 8:
                        # Fallback for old format (without CC)
                        try:
                            sender_name = parts[1].strip()
                            sender_email = parts[2].strip()
                            recipients_str = parts[3].strip()
                            date_str = parts[4].strip()
                            body = parts[5].strip()
                            is_read = parts[6].strip().lower() == "true"
                            importance = parts[7].strip()
                            
                            email_date = self._parse_date(date_str)
                            
                            if date_from and email_date < date_from:
                                continue
                            if date_to and email_date > date_to:
                                continue
                            if len(body) < min_length:
                                continue
                            
                            recipient_emails = []
                            recipient_names = []
                            if recipients_str:
                                recipient_pattern = r'([^<]+)\s*<([^>]+)>'
                                matches = re.findall(recipient_pattern, recipients_str)
                                for name, email in matches:
                                    recipient_emails.append(email.strip())
                                    recipient_names.append(name.strip())
                            
                            if from_address and from_address.lower() not in sender_email.lower():
                                continue
                            if from_name and from_name.lower() not in sender_name.lower() and from_name.lower() not in sender_email.lower():
                                continue
                            
                            if to_address:
                                if not any(to_address.lower() in rec_email.lower() for rec_email in recipient_emails):
                                    continue
                            if to_name:
                                if not any(to_name.lower() in rec_name.lower() or to_name.lower() in rec_email.lower() 
                                         for rec_name, rec_email in zip(recipient_names, recipient_emails)):
                                    continue
                            
                            relevance = self._calculate_relevance_score(parts[0], body, importance)
                            
                            email_data = {
                                "id": f"local_{hash(line)}",
                                "subject": parts[0].strip(),
                                "from": sender_email,
                                "from_name": sender_name,
                                "to": recipient_emails,
                                "to_names": recipient_names,
                                "cc": [],
                                "cc_names": [],
                                "date": email_date.isoformat(),
                                "body": body,
                                "body_preview": body[:200] + "..." if len(body) > 200 else body,
                                "is_read": is_read,
                                "importance": importance,
                                "relevance_score": relevance
                            }
                            emails.append(email_data)
                        except Exception as e:
                            print(f"Error parsing email (old format): {e}")
                            continue
        
        # Sort by relevance
        emails.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return emails[:max_results]
    
    def _build_filter_conditions(
        self,
        search_query: Optional[str],
        from_address: Optional[str],
        from_name: Optional[str],
        date_from: Optional[datetime],
        date_to: Optional[datetime]
    ) -> str:
        """Build AppleScript filter conditions"""
        conditions = []
        
        # Note: AppleScript filtering is done in Python after fetching
        # This is a placeholder for future optimization
        return ""
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse AppleScript date string to Python datetime"""
        # AppleScript dates are in format like "Monday, January 1, 2024 at 12:00:00 PM"
        try:
            # Try common formats
            formats = [
                "%A, %B %d, %Y at %I:%M:%S %p",
                "%B %d, %Y at %I:%M:%S %p",
                "%Y-%m-%d %H:%M:%S",
                "%m/%d/%Y %H:%M:%S"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue
            
            # Fallback to current date
            return datetime.now()
        except:
            return datetime.now()
    
    def _calculate_relevance_score(self, subject: str, body: str, importance: str) -> float:
        """Calculate relevance score for email"""
        score = 0.0
        
        subject_lower = subject.lower()
        body_lower = body.lower()
        
        # Customer service keywords
        customer_service_keywords = [
            "support", "help", "question", "issue", "problem", "complaint",
            "request", "inquiry", "assistance", "service", "customer",
            "order", "refund", "return", "cancel", "payment", "billing",
            "account", "login", "password", "delivery", "shipping"
        ]
        
        for keyword in customer_service_keywords:
            if keyword in subject_lower:
                score += 2.0
            if keyword in body_lower:
                score += 1.0
        
        # Marketing keywords (negative)
        marketing_keywords = [
            "unsubscribe", "newsletter", "promotion", "sale", "discount",
            "marketing", "advertisement"
        ]
        
        for keyword in marketing_keywords:
            if keyword in subject_lower or keyword in body_lower:
                score -= 3.0
        
        # Length bonus
        if len(body) > 500:
            score += 1.0
        if len(body) > 1000:
            score += 1.0
        
        # Importance
        if "high" in importance.lower():
            score += 1.5
        elif "low" in importance.lower():
            score -= 0.5
        
        return max(score, 0.0)
    
    def export_selected_emails(self, emails: List[Dict], output_dir: str) -> int:
        """Export emails to EML files"""
        import os
        from email.mime.text import MIMEText
        from email.utils import formatdate
        
        os.makedirs(output_dir, exist_ok=True)
        
        count = 0
        for email in emails:
            try:
                body = email.get("body", "")
                is_html = "<html" in body.lower() or "<body" in body.lower()
                
                msg = MIMEText(body, "html" if is_html else "plain", "utf-8")
                msg["Subject"] = email.get("subject", "No Subject")
                
                from_addr = email.get("from", "Unknown")
                from_name = email.get("from_name", "")
                if from_name:
                    msg["From"] = f"{from_name} <{from_addr}>"
                else:
                    msg["From"] = from_addr
                
                try:
                    dt = datetime.fromisoformat(email.get("date", ""))
                    msg["Date"] = formatdate(dt.timestamp())
                except:
                    msg["Date"] = formatdate()
                
                safe_subject = "".join(c for c in email["subject"] if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
                filename = f"{count:05d}_{safe_subject}.eml"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(msg.as_string())
                
                count += 1
            except Exception as e:
                print(f"Error exporting email: {e}")
        
        return count

def main():
    """Test the connector"""
    connector = OutlookLocalMac()
    
    if not connector.check_outlook_running():
        print("Outlook is not running. Please start Outlook first.")
        return
    
    print("Outlook is running!")
    print("\nAccounts:")
    accounts = connector.list_accounts()
    for acc in accounts:
        print(f"  - {acc['name']}: {acc['email']}")
    
    print("\nFolders:")
    folders = connector.list_folders()
    for folder in folders[:10]:  # Show first 10
        print(f"  - {folder['name']}: {folder['count']} messages")
    
    print("\nSearching emails...")
    emails = connector.search_emails(max_results=10)
    print(f"Found {len(emails)} emails")
    
    for i, email in enumerate(emails[:5], 1):
        print(f"\n{i}. [{email['relevance_score']:.1f}] {email['subject']}")
        print(f"   From: {email['from_name']} <{email['from']}>")

if __name__ == '__main__':
    main()

