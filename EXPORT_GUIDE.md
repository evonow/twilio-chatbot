# Email & Text Message Export Guide

This guide covers the best methods to export emails and text messages from various platforms for use with the chatbot.

## Email Export Methods

### Gmail

#### Method 1: Google Takeout (Recommended)
1. Go to [Google Takeout](https://takeout.google.com/)
2. Select "Mail" from the list
3. Choose format: **MBOX** (recommended) or **EML**
4. Select date range and labels/folders
5. Click "Create export"
6. Download the ZIP file when ready
7. Extract and point the processor to the `Mail` folder

**Note**: MBOX files can be processed directly, or you can convert them to individual EML files.

#### Method 2: Thunderbird (Best for Large Exports)
1. Install [Thunderbird](https://www.thunderbird.net/)
2. Add your Gmail account via IMAP
3. Let it sync all emails
4. Use Thunderbird's export tools or the `export_emails.py` script (see below)

#### Method 3: Gmail API (For Programmatic Access)
Use the provided `export_gmail.py` script (see below) to export via Gmail API.

### Outlook / Microsoft 365

#### Method 1: Outlook Desktop App
1. Open Outlook
2. Select emails you want to export
3. File → Save As → Choose "Text Only" or "Outlook Message Format"
4. Or use: File → Open & Export → Import/Export → Export to a file → Outlook Data File (.pst)

**Note**: PST files need conversion. Use `libpst` tools or Outlook's built-in export.

#### Method 2: Outlook.com Web
1. Use Microsoft's export tool: [Account Export](https://account.microsoft.com/privacy/export)
2. Select "Mail" and download
3. Files will be in MBOX or EML format

#### Method 3: Outlook API
Use Microsoft Graph API with the provided `export_outlook.py` script.

### Apple Mail (macOS)

#### Method 1: Mail App Export
1. Open Mail app
2. Select emails or folders
3. File → Export Mailbox
4. Choose location and format (Mail format is fine)
5. The exported folder contains `.emlx` files (similar to EML)

**Note**: `.emlx` files are Apple's format but can be converted to EML.

#### Method 2: Direct Mailbox Access
Apple Mail stores emails in: `~/Library/Mail/V*/Mailboxes/`
You can copy these directly, but they're in a proprietary format.

### Thunderbird

1. Open Thunderbird
2. Select mailbox/folder
3. Tools → Export
4. Choose format (MBOX recommended)
5. Save to desired location

### Yahoo Mail

1. Use [Yahoo Account Export](https://help.yahoo.com/kb/SLN4075.html)
2. Request email export
3. Download when ready (usually MBOX format)

### Other Email Providers

Most email providers offer:
- **IMAP access**: Use Thunderbird or similar to sync and export
- **Export tools**: Check provider's account settings
- **API access**: Use provider-specific APIs

## Text Message Export Methods

### iPhone (iOS)

#### Method 1: iTunes Backup Extraction
1. Create iTunes backup
2. Use tools like:
   - [iMazing](https://imazing.com/) (paid, easiest)
   - [iExplorer](https://macroplant.com/iexplorer) (paid)
   - [iPhone Backup Extractor](https://www.iphonebackupextractor.com/) (free/paid)
3. Export messages as CSV or JSON

#### Method 2: iCloud Sync & Export
1. Enable Messages in iCloud
2. Use [iMazing](https://imazing.com/) to access iCloud messages
3. Export as CSV/JSON

#### Method 3: Manual Copy (Small Volumes)
1. Open Messages app
2. Long-press message → Copy
3. Paste into text file
4. Format: `Date: [date]\nFrom: [sender]\nMessage: [text]`

### Android

#### Method 1: SMS Backup & Restore App
1. Install [SMS Backup & Restore](https://play.google.com/store/apps/details?id=com.riteshsahu.SMSBackupRestore)
2. Backup messages to XML or JSON
3. Transfer file to computer
4. Process with the data processor

#### Method 2: Google Messages Export
1. Use Google Messages web interface
2. Export via Takeout (if synced to Google)
3. Download from Google Takeout

#### Method 3: ADB Backup (Advanced)
```bash
adb backup -f messages.ab com.android.providers.telephony
```
Then extract using tools like `android-backup-extractor`.

### WhatsApp

#### Method 1: Built-in Export
1. Open WhatsApp
2. Open chat → Menu (3 dots) → More → Export chat
3. Choose "Without Media"
4. Sends as `.txt` file via email or saves to device
5. Process the text file

#### Method 2: WhatsApp Web Export
1. Use browser extensions like [WhatsApp Chat Export](https://chrome.google.com/webstore)
2. Export conversations as JSON or CSV

### Telegram

1. Open Telegram Desktop
2. Right-click conversation → Export chat history
3. Choose format: JSON or HTML
4. Process the exported file

### Signal

1. Use Signal Desktop
2. File → Export chat
3. Exports as JSON format
4. Process directly

### Twilio SMS (If Using Twilio)

Use Twilio API to export:
```python
# See export_twilio.py script below
```

## Recommended File Formats

### For Emails:
- **EML** (`.eml`) - Individual email files, best compatibility
- **MBOX** (`.mbox`) - Single file with multiple emails, efficient
- **CSV** (`.csv`) - Structured data, easy to process

### For Text Messages:
- **JSON** (`.json`) - Structured, preserves metadata
- **CSV** (`.csv`) - Easy to read and process
- **TXT** (`.txt`) - Simple format, requires parsing

## Processing Your Exported Data

Once you have your data exported:

### 1. Organize Your Files
```
data/
  emails/
    gmail_export.mbox
    outlook_emails/
      email1.eml
      email2.eml
  sms/
    iphone_messages.json
    android_backup.xml
    whatsapp_chat.txt
```

### 2. Run the Processor
```bash
# Process all files in a directory
python data_processor.py ./data

# Process only emails
python data_processor.py ./data/emails --pattern "*.eml"

# Process only SMS
python data_processor.py ./data/sms --pattern "*.json"
```

### 3. Supported Formats

The processor automatically handles:
- `.eml` - Email files
- `.mbox` - MBOX email archives
- `.txt` - Plain text emails or messages
- `.json` - JSON formatted messages
- `.csv` - CSV formatted data
- `.xml` - XML backups (Android SMS)

## Tips for Best Results

1. **Include Metadata**: Export with dates, senders, recipients when possible
2. **Clean Data**: Remove auto-replies, out-of-office messages if not relevant
3. **Date Range**: Export relevant time periods (e.g., last 2 years)
4. **Filter**: Focus on customer service interactions, exclude marketing emails
5. **Privacy**: Remove or anonymize sensitive information before processing

## Common Issues & Solutions

### Issue: MBOX file not processing
**Solution**: Convert MBOX to individual EML files using `mb2eml.py` script (see below)

### Issue: Large file sizes
**Solution**: Split large files or process in batches. The processor handles large files but may take time.

### Issue: Encoding errors
**Solution**: The processor handles encoding errors gracefully, but ensure UTF-8 when possible.

### Issue: Missing metadata
**Solution**: Use export methods that preserve metadata (JSON, EML) rather than plain text.

## Next Steps

After exporting:
1. Review the export guide above for your platform
2. Use the helper scripts provided (see `scripts/` folder)
3. Run the data processor
4. Test queries to verify data quality

