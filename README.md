# Ask GroupFund - Twilio Customer Service Chatbot

An intelligent chatbot built on Twilio SMS that answers questions using a knowledge base of past customer service interactions (emails and text messages). The system uses RAG (Retrieval Augmented Generation) with semantic search and LLM-powered responses.

> 📚 **For complete documentation, see [DOCUMENTATION.md](DOCUMENTATION.md)**

## Features

- **SMS Integration**: Receive and respond to SMS messages via Twilio
- **RAG System**: Retrieves relevant context from past interactions using semantic search
- **LLM-Powered**: Uses OpenAI GPT-4 for intelligent response generation
- **Knowledge Base Management**: Web GUI for uploading and processing training data
- **Multiple File Formats**: Supports .eml, .mbox, .txt, .json, .csv, .xml, .docx, .pdf
- **Audience Labeling**: Tag training data for Sales Reps, Customers, or Internal Use
- **Conversation History**: Maintains context across multiple messages
- **Source Attribution**: Shows which emails/messages were used to generate responses
- **FAQ Analysis**: Automatically extracts frequently asked questions from your data
- **GitLab Integration**: Ingest commits, READMEs, and release notes from GitLab repositories

## Architecture

1. **Chatbot Agent** (`chatbot.py`): Core RAG system with semantic search and LLM integration
2. **Data Processor** (`data_processor.py`): Processes emails, SMS, and documents into the knowledge base
3. **Web Application** (`web_app.py`): Flask server with GUI for data management and Twilio webhooks
4. **Twilio Webhook** (`/sms` endpoint): Receives SMS and responds via Twilio

## Installation

### Prerequisites

- Python 3.9+
- Twilio account with phone number
- OpenAI API key
- (Optional) GitLab access token for repository integration

### Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd twilio-chatbot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Required environment variables:**
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `TWILIO_ACCOUNT_SID`: Your Twilio Account SID
   - `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token
   - `TWILIO_PHONE_NUMBER`: Your Twilio phone number (format: +1234567890)

## Usage

### Start the Web Application

```bash
python3 web_app.py
```

The web interface will be available at `http://localhost:5001`

### Upload Training Data

1. Go to the "Upload Files" section
2. Drag and drop or select files (.eml, .mbox, .txt, .json, .csv, .xml, .docx, .pdf)
3. Select an audience label (Sales Reps, Customers, Internal Use, or None)
4. Click "Process Files"

### Test the Chatbot

1. Go to the "Test Chatbot" section
2. Enter a question
3. Optionally filter by audience
4. Click "Query" to see the response

### Configure Twilio Webhook

1. **For local testing**, use ngrok:
   ```bash
   ngrok http 5001
   ```

2. **In Twilio Console:**
   - Go to Phone Numbers → Your Number
   - Set "A MESSAGE COMES IN" webhook to: `https://your-ngrok-url.ngrok-free.app/sms`
   - Method: POST

3. **For production:**
   - Deploy your app to a server with HTTPS
   - Update Twilio webhook to your production URL

### US A2P 10DLC Registration (Required for US SMS)

To send SMS to US numbers, you must register for A2P 10DLC:

1. Go to: https://console.twilio.com/us1/develop/sms/a2p-messaging
2. Register your brand
3. Create a campaign (use "Customer Service" use case for highest approval)
4. Wait for approval (typically 1-3 business days)

**Recommended Campaign Details:**
- **Use Case**: Customer Service / Account Notifications
- **Description**: Automated customer service chatbot responding to customer inquiries
- **Opt-in**: Customer-initiated (customers send SMS first)
- **Sample Messages**: Include examples of helpful responses

## Project Structure

```
twilio-chatbot/
├── chatbot.py              # Core chatbot agent with RAG
├── data_processor.py        # Data ingestion and processing
├── web_app.py              # Flask web application and Twilio webhooks
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore            # Git ignore rules
├── templates/
│   └── index.html        # Web UI template
├── static/
│   ├── css/
│   │   └── style.css     # Styles
│   └── js/
│       └── app.js        # Frontend JavaScript
├── scripts/
│   ├── gitlab_connector.py      # GitLab integration
│   └── google_docs_connector.py # Google Docs integration (optional)
├── uploads/              # Uploaded files (gitignored)
└── chroma_db/            # Vector database (gitignored)
```

## API Endpoints

### Web Application
- `GET /` - Web interface
- `POST /api/upload` - Upload files
- `POST /api/process` - Process uploaded files
- `POST /api/query` - Query chatbot
- `GET /api/stats` - Get knowledge base statistics
- `GET /api/files` - List uploaded files
- `POST /api/gitlab/ingest` - Ingest GitLab repository

### Twilio Webhook
- `POST /sms` - Receive and respond to SMS messages

## Development

### Adding New File Types

1. Add processing method to `data_processor.py`
2. Update `ALLOWED_EXTENSIONS` in `web_app.py`
3. Add file type to upload UI in `templates/index.html`

### Adding New Integrations

1. Create connector script in `scripts/`
2. Add API endpoint in `web_app.py`
3. Add UI section in `templates/index.html`
4. Add JavaScript handlers in `static/js/app.js`

## Security Notes

- Never commit `.env` file (it's in `.gitignore`)
- Keep API keys secure
- Use environment variables for all secrets
- Review uploaded files before processing sensitive data

## Troubleshooting

### Twilio webhook not receiving messages
- Check webhook URL is correct and accessible
- Verify HTTPS is enabled (required for Twilio)
- Check Twilio logs for errors

### A2P 10DLC Error 30034
- Register for A2P 10DLC (see above)
- Use "Customer Service" use case for fastest approval
- Ensure brand registration is complete

### OpenAI API errors
- Verify `OPENAI_API_KEY` is set correctly
- Check API quota and billing
- Review error messages in logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Add your license here]

## Documentation

For complete documentation including:
- Detailed user guide
- API reference
- Architecture overview
- Deployment instructions
- Developer guide
- Troubleshooting

See **[DOCUMENTATION.md](DOCUMENTATION.md)**

## Support

For issues and questions:
- Email: hello@groupfund.us
- Phone: 888-390-7620
- Website: https://www.groupfund.us
