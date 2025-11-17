# Quick Start: Export & Ingest Guide

## Best Methods Summary

### For Emails

**Recommended: Google Takeout (Gmail)**
1. Go to https://takeout.google.com/
2. Select "Mail" → Choose MBOX format
3. Download and extract
4. Process: `python data_processor.py /path/to/extracted/Mail`

**Alternative: Thunderbird**
1. Install Thunderbird
2. Add your email account (IMAP)
3. Export mailbox as MBOX
4. Process: `python data_processor.py /path/to/mbox/file.mbox`

**For Outlook:**
- Use Outlook's export feature → Save as PST
- Convert PST to MBOX using tools like `readpst`
- Or use Microsoft Account Export

### For Text Messages

**iPhone:**
- Use [iMazing](https://imazing.com/) → Export as CSV/JSON
- Or use iTunes backup extraction tools

**Android:**
- Use [SMS Backup & Restore](https://play.google.com/store/apps/details?id=com.riteshsahu.SMSBackupRestore)
- Backup to XML format
- Process: `python data_processor.py /path/to/backup.xml`

**WhatsApp:**
- Open chat → Menu → Export chat (without media)
- Saves as `.txt` file
- Process directly

**Twilio SMS:**
- Use provided script: `python scripts/export_twilio.py --from-date 2024-01-01`
- Exports as JSON
- Process: `python data_processor.py ./twilio_messages.json`

## Supported Formats

✅ **Emails:**
- `.eml` - Individual email files
- `.mbox` - Email archive files
- `.txt` - Plain text emails

✅ **Text Messages:**
- `.json` - JSON formatted (Twilio, Signal, Telegram)
- `.csv` - CSV formatted (iPhone exports)
- `.xml` - XML format (Android SMS Backup)
- `.txt` - Plain text (WhatsApp, manual exports)

## Processing Your Data

### Step 1: Organize Your Files
```
data/
  emails/
    gmail_export.mbox
    individual_emails/
      email1.eml
  sms/
    iphone_messages.csv
    android_backup.xml
    twilio_messages.json
```

### Step 2: Process All Data
```bash
python data_processor.py ./data
```

### Step 3: Process Specific Types
```bash
# Only emails
python data_processor.py ./data/emails --pattern "*.eml"

# Only SMS
python data_processor.py ./data/sms --pattern "*.json"
```

## Helper Scripts

Located in `scripts/` directory:

1. **`export_gmail.py`** - Export from Gmail API
2. **`export_twilio.py`** - Export from Twilio account
3. **`mbox_to_eml.py`** - Convert MBOX to individual EML files

See `scripts/README.md` for detailed usage.

## Tips

1. **Start Small**: Test with a small subset first
2. **Filter Data**: Export only relevant customer service interactions
3. **Date Range**: Focus on recent/relevant time periods
4. **Privacy**: Remove sensitive info before processing
5. **Format**: Prefer structured formats (JSON, EML) over plain text

## Need Help?

- See `EXPORT_GUIDE.md` for detailed platform-specific instructions
- Check `scripts/README.md` for export script usage
- Review `README.md` for full system documentation

