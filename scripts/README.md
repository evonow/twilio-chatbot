# Export Scripts

Helper scripts to export emails and text messages from various platforms.

## Available Scripts

### `export_gmail.py`
Exports emails from Gmail using Gmail API.

**Setup:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project or select existing
3. Enable Gmail API
4. Create OAuth2 credentials (Desktop app)
5. Download as `credentials.json` in the scripts directory

**Usage:**
```bash
python scripts/export_gmail.py --query "label:customer-service" --max 1000 --output ./gmail_export
```

**Options:**
- `--query`: Gmail search query (e.g., "from:support@example.com", "label:customer-service")
- `--max`: Maximum number of emails to export (default: 1000)
- `--output`: Output directory (default: ./gmail_export)
- `--credentials`: Path to credentials.json (default: credentials.json)
- `--token`: Path to token.json (default: token.json)

### `export_twilio.py`
Exports SMS messages from your Twilio account.

**Setup:**
Ensure `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` are set in `.env`

**Usage:**
```bash
python scripts/export_twilio.py --from-date 2024-01-01 --to-date 2024-12-31 --output twilio_messages.json
```

**Options:**
- `--from-date`: Start date (YYYY-MM-DD)
- `--to-date`: End date (YYYY-MM-DD)
- `--phone`: Filter by phone number
- `--output`: Output JSON file (default: twilio_messages.json)

### `mbox_to_eml.py`
Converts MBOX files to individual EML files.

**Usage:**
```bash
python scripts/mbox_to_eml.py gmail_export.mbox ./eml_output
```

**Options:**
- `mbox_file`: Path to MBOX file
- `output_dir`: Output directory for EML files

## Installation

Install additional dependencies for export scripts:

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Notes

- Gmail export requires OAuth2 authentication (one-time setup)
- Twilio export uses your existing Twilio credentials
- MBOX converter uses Python's built-in mailbox module
- All scripts output files compatible with the main data processor

