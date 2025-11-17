# Web Application Guide

The web application provides a user-friendly GUI for managing your email and SMS data processing.

## Starting the Web App

```bash
python web_app.py
```

The app will start on `http://localhost:5001` by default.

## Features

### 1. File Upload
- **Drag and Drop**: Simply drag files onto the upload area
- **Click to Browse**: Click the upload area to select files
- **Supported Formats**: `.eml`, `.mbox`, `.txt`, `.json`, `.csv`, `.xml`
- **Multiple Files**: Upload multiple files at once

### 2. Processing
- **Real-time Status**: See processing progress in real-time
- **Progress Bar**: Visual progress indicator
- **Error Handling**: View any errors that occur during processing
- **Document Count**: See how many documents were added to the knowledge base

### 3. Chatbot Testing
- **Query Interface**: Test your chatbot directly in the browser
- **Instant Responses**: Get immediate answers from your knowledge base
- **Query History**: View your queries and responses

### 4. File Management
- **View Uploaded Files**: See all files you've uploaded
- **File Details**: View file size and modification date
- **Delete Files**: Remove files you no longer need

### 5. Knowledge Base Management
- **Statistics**: See total documents in your knowledge base
- **Clear Database**: Reset the knowledge base (use with caution!)

## Usage Workflow

1. **Upload Files**
   - Drag and drop your email/SMS files onto the upload area
   - Or click to browse and select files
   - Files are stored temporarily in the `uploads/` directory

2. **Process Files**
   - Click "Process Files" button
   - Watch the progress bar and status updates
   - Wait for processing to complete

3. **Test Your Chatbot**
   - Enter a question in the query box
   - Click "Query" or press Ctrl+Enter
   - View the response from your knowledge base

4. **Manage Files**
   - View uploaded files in the "Uploaded Files" section
   - Delete files you no longer need
   - Refresh the list to see latest files

## Tips

- **Large Files**: Processing large files may take time. Be patient!
- **Multiple Files**: You can process multiple files at once
- **File Types**: The app automatically detects file types and processes accordingly
- **Errors**: Check the error section if processing fails
- **Testing**: Use the query interface to verify your data was processed correctly

## Troubleshooting

### Files Not Uploading
- Check file size (max 500MB per file)
- Ensure file extension is supported
- Check browser console for errors

### Processing Fails
- Verify OpenAI API key is set in `.env`
- Check that files are valid format
- Review error messages in the processing status

### No Responses from Chatbot
- Ensure data has been processed successfully
- Check knowledge base statistics (should show documents > 0)
- Try different queries

### Port Already in Use
- Change the PORT in `.env` file
- Or stop the process using port 5001

## Keyboard Shortcuts

- **Ctrl+Enter**: Submit query (in query box)
- **Click Upload Area**: Browse for files
- **Drag & Drop**: Upload files quickly

## API Endpoints

The web app uses these API endpoints (for reference):

- `POST /api/upload` - Upload files
- `POST /api/process` - Process uploaded files
- `GET /api/status` - Get processing status
- `POST /api/query` - Query the chatbot
- `GET /api/stats` - Get knowledge base statistics
- `GET /api/files` - List uploaded files
- `DELETE /api/files/<filename>` - Delete a file
- `POST /api/clear` - Clear knowledge base

## Next Steps

After processing your data:
1. Test queries to verify data quality
2. Start the Twilio SMS server (`python app.py`)
3. Configure Twilio webhook
4. Begin receiving SMS queries!

