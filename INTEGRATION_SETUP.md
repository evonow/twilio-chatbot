# Integration Setup Guide

This guide explains how to set up Google Docs and GitLab integrations for ingesting release notes and documentation.

## Google Docs Integration

### Setup Steps:

1. **Create Google Cloud Project** (if you don't have one):
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable Google Docs API**:
   - Navigate to "APIs & Services" → "Library"
   - Search for "Google Docs API"
   - Click "Enable"

3. **Create OAuth2 Credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop app" as application type
   - Name it (e.g., "Chatbot Integration")
   - Click "Create"
   - Download the JSON file and save it as `credentials.json` in your project root

4. **Use the Integration**:
   - Open the web app
   - Navigate to "Google Docs Integration" section
   - Paste your Google Doc URL or Document ID
   - Click "Ingest Google Doc"
   - On first use, you'll be prompted to authenticate in your browser

### Finding Document ID:

The Document ID is in the Google Doc URL:
```
https://docs.google.com/document/d/DOCUMENT_ID_HERE/edit
```

You can paste either:
- The full URL: `https://docs.google.com/document/d/1ABC123.../edit`
- Just the ID: `1ABC123...`

## GitLab Integration

### Setup Steps:

1. **Create GitLab Access Token**:
   - Log into GitLab
   - Go to User Settings → Access Tokens (or Project Settings → Access Tokens)
   - Create a new token with `read_api` scope
   - Copy the token (you won't see it again!)

2. **Set Environment Variable** (Recommended):
   ```bash
   export GITLAB_ACCESS_TOKEN="your-token-here"
   ```
   
   Or add to your `.env` file:
   ```
   GITLAB_ACCESS_TOKEN=your-token-here
   ```

3. **Optional: Set GitLab URL**:
   - For GitLab.com, no configuration needed
   - For self-hosted GitLab, set:
     ```bash
     export GITLAB_URL="https://gitlab.yourcompany.com"
     ```
     Or in `.env`:
     ```
     GITLAB_URL=https://gitlab.yourcompany.com
     ```

4. **Use the Integration**:
   - Open the web app
   - Navigate to "GitLab Integration" section
   - Enter your GitLab URL (or leave default for gitlab.com)
   - Enter Project ID (e.g., `namespace/project-name` or numeric ID)
   - Optionally enter access token (if not set in environment)
   - Select branch/tag (default: `main`)
   - Choose what to include:
     - ✅ Commit Messages
     - ✅ README Files
     - ✅ Release Notes (CHANGELOG, RELEASE files)
   - Set max commits (default: 100)
   - Click "Ingest GitLab Repository"

### Finding Project ID:

The Project ID can be:
- **Namespace/Project Name**: `groupfund/groupfund-app`
- **Numeric ID**: Found in project settings → General

### What Gets Ingested:

- **Commits**: Recent commit messages (up to max_commits)
- **README Files**: All README.md, README.txt files in the repository
- **Release Notes**: Files matching CHANGELOG*, RELEASE*, RELEASES* patterns

## Best Practices

### For Sales Reps:

1. **Google Docs**: Use for curated release notes and documentation
   - Keep release notes in a single Google Doc
   - Update it regularly with new features
   - The chatbot will answer questions based on this content

2. **GitLab**: Use for comprehensive technical information
   - Automatically pulls latest commits
   - Includes README files for feature documentation
   - Great for staying up-to-date with latest changes

3. **Both Together**: 
   - Google Docs for customer-facing release notes
   - GitLab for technical details and commit history
   - Sales reps can ask questions and get answers from both sources

### Example Questions Sales Reps Can Ask:

- "What's new in the latest release?"
- "How does the donation feature work?"
- "What was fixed in the last update?"
- "Can users add multiple payment methods?"
- "What are the top 10 questions customers ask?"

## Troubleshooting

### Google Docs:

- **"Credentials file not found"**: Make sure `credentials.json` is in the project root
- **"Authentication failed"**: Re-authenticate by deleting `token.pickle` and trying again
- **"Document not found"**: Check that the document ID is correct and the document is accessible

### GitLab:

- **"Access token required"**: Set `GITLAB_ACCESS_TOKEN` environment variable or enter in UI
- **"Project not found"**: Verify project ID format (namespace/project-name or numeric ID)
- **"Permission denied"**: Check that your token has `read_api` scope
- **"Rate limit exceeded"**: GitLab has API rate limits; wait a few minutes and try again

## Security Notes

- **Never commit credentials.json or token.pickle** to version control
- Add to `.gitignore`:
  ```
  credentials.json
  token.pickle
  ```
- **Access tokens**: Store in environment variables, not in code
- **Token scope**: Use minimum required scope (`read_api` for GitLab, read-only for Google Docs)

