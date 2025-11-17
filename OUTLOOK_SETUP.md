# Outlook Integration Setup Guide

This guide will help you set up Microsoft Graph API access to connect to your Outlook/Office 365 mailbox.

## Step 1: Register an Application in Azure AD

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Fill in:
   - **Name**: `Twilio Chatbot Email Connector` (or any name)
   - **Supported account types**: Choose based on your needs
   - **Redirect URI**: Leave blank for now
5. Click **Register**

## Step 2: Create a Client Secret

1. In your app registration, go to **Certificates & secrets**
2. Click **New client secret**
3. Add a description (e.g., "Chatbot connector")
4. Choose expiration (recommend 24 months)
5. Click **Add**
6. **IMPORTANT**: Copy the secret value immediately (you won't see it again!)
7. Save it securely

## Step 3: Configure API Permissions

1. In your app registration, go to **API permissions**
2. Click **Add a permission**
3. Select **Microsoft Graph**
4. Select **Application permissions** (not Delegated)
5. Add these permissions:
   - `Mail.Read` - Read mail in all mailboxes
   - `User.Read.All` - Read all users' profiles (to list mailboxes)
6. Click **Add permissions**
7. Click **Grant admin consent** (requires admin rights)
   - This is required for application permissions

## Step 4: Get Your Credentials

From your app registration page, you'll need:

1. **Application (client) ID**: Found on the Overview page
2. **Directory (tenant) ID**: Found on the Overview page
3. **Client Secret**: The value you copied in Step 2

## Step 5: Using in the Web App

1. Open the web app at `http://localhost:5001`
2. Scroll to the **"Connect to Outlook"** section
3. Enter your credentials:
   - **Azure Client ID**: Your Application (client) ID
   - **Client Secret**: Your client secret value
   - **Tenant ID**: Your Directory (tenant) ID
   - **Mailbox Email**: The email address of the mailbox (e.g., `groupfund@yourdomain.com`)
4. Configure search options:
   - **Days to Search**: How far back to search (default: 365)
   - **Max Results**: Maximum emails to retrieve (default: 500)
   - **Search Query**: Optional search terms
   - **From Address**: Optional sender filter
5. Click **"Search & Filter Emails"**

## Intelligent Filtering

The system automatically scores emails by relevance:

- **High Score (5+)**: Emails with customer service keywords (support, help, issue, etc.)
- **Medium Score (2-5)**: Emails with some relevant content
- **Low Score (<2)**: Marketing/automated emails or less relevant content

### Scoring Factors:
- ✅ Customer service keywords: +2 points (subject), +1 point (body)
- ✅ Email length: Bonus for longer, informative emails
- ✅ High importance flag: +1.5 points
- ✅ Unread emails: +0.5 points (may indicate active issues)
- ❌ Marketing keywords: -3 points (unsubscribe, newsletter, etc.)
- ❌ Low importance: -0.5 points

## Selecting Emails

After searching:
1. Review the results sorted by relevance score
2. Use checkboxes to select emails you want to include
3. Options:
   - **Select All**: All emails
   - **Select Top 100**: Top 100 by relevance score
   - **Manual Selection**: Check individual emails
4. Click **"Export Selected"** to download as EML files
5. The exported emails will appear in the Upload Files section
6. Process them normally using the "Process Files" button

## Troubleshooting

### "Failed to authenticate"
- Verify your Client ID, Secret, and Tenant ID are correct
- Ensure admin consent was granted for API permissions
- Check that the secret hasn't expired

### "No emails found"
- Check the mailbox email address is correct
- Try increasing the "Days to Search" value
- Verify the mailbox has emails in the specified date range
- Check if you have permission to access that mailbox

### "Permission denied"
- Ensure `Mail.Read` permission is granted
- Verify admin consent was granted (not just added)
- Check that you're using Application permissions (not Delegated)

### Rate Limiting
- Microsoft Graph API has rate limits
- If you hit limits, wait a few minutes and try again
- Consider reducing "Max Results" for large mailboxes

## Security Notes

- **Never commit credentials to version control**
- Store credentials securely (consider using environment variables)
- Rotate client secrets regularly
- Use the minimum required permissions
- Consider using Azure Key Vault for production

## Alternative: Using Delegated Permissions

If you prefer user-based authentication (OAuth2 flow):

1. Use **Delegated permissions** instead of Application permissions
2. Implement OAuth2 authorization code flow
3. User will need to sign in and consent
4. This allows access only to the signed-in user's mailbox

The current implementation uses Application permissions for server-to-server access without user interaction.

## Next Steps

After exporting emails:
1. They'll be saved as `.eml` files in the `uploads/outlook_export/` directory
2. Process them using the normal file upload/processing workflow
3. They'll be added to your knowledge base for the chatbot

