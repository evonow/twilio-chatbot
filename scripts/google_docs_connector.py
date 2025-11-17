"""
Google Docs Connector
Fetches and processes Google Docs for ingestion into the knowledge base
"""

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
from typing import List, Dict
import re

# Scopes required for Google Docs API
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

class GoogleDocsConnector:
    def __init__(self):
        """Initialize Google Docs connector"""
        self.service = None
        self.credentials = None
        
    def authenticate(self, credentials_file: str = 'credentials.json', token_file: str = 'token.pickle'):
        """
        Authenticate with Google Docs API
        
        Args:
            credentials_file: Path to OAuth2 credentials JSON file
            token_file: Path to store/load token
            
        Returns:
            True if authentication successful
        """
        creds = None
        
        # Load existing token if available
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file '{credentials_file}' not found. "
                        "Please download OAuth2 credentials from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next time
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.credentials = creds
        self.service = build('docs', 'v1', credentials=creds)
        return True
    
    def get_document(self, document_id: str) -> Dict:
        """
        Fetch a Google Doc by ID
        
        Args:
            document_id: Google Doc ID (from URL: docs.google.com/document/d/{DOCUMENT_ID}/edit)
            
        Returns:
            Dictionary with document content and metadata
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        try:
            # Get document metadata
            doc = self.service.documents().get(documentId=document_id).execute()
            
            # Extract text content
            text_content = self._extract_text_from_doc(doc)
            
            return {
                'title': doc.get('title', 'Untitled'),
                'document_id': document_id,
                'content': text_content,
                'modified_time': doc.get('modifiedTime', ''),
                'created_time': doc.get('createdTime', ''),
                'source': 'google_docs'
            }
        except HttpError as error:
            raise RuntimeError(f"Error fetching document: {error}")
    
    def _extract_text_from_doc(self, doc: Dict) -> str:
        """
        Extract plain text from Google Doc structure
        
        Args:
            doc: Google Doc API response
            
        Returns:
            Plain text content
        """
        text_parts = []
        
        if 'body' in doc and 'content' in doc['body']:
            for element in doc['body']['content']:
                if 'paragraph' in element:
                    para_text = self._extract_paragraph_text(element['paragraph'])
                    if para_text:
                        text_parts.append(para_text)
                elif 'table' in element:
                    table_text = self._extract_table_text(element['table'])
                    if table_text:
                        text_parts.append(table_text)
        
        return '\n\n'.join(text_parts)
    
    def _extract_paragraph_text(self, paragraph: Dict) -> str:
        """Extract text from a paragraph element"""
        text_parts = []
        
        if 'elements' in paragraph:
            for element in paragraph['elements']:
                if 'textRun' in element:
                    text = element['textRun'].get('content', '')
                    text_parts.append(text)
        
        return ''.join(text_parts).strip()
    
    def _extract_table_text(self, table: Dict) -> str:
        """Extract text from a table element"""
        rows_text = []
        
        if 'tableRows' in table:
            for row in table['tableRows']:
                if 'tableCells' in row:
                    cell_texts = []
                    for cell in row['tableCells']:
                        if 'content' in cell:
                            for element in cell['content']:
                                if 'paragraph' in element:
                                    cell_text = self._extract_paragraph_text(element['paragraph'])
                                    if cell_text:
                                        cell_texts.append(cell_text)
                    if cell_texts:
                        rows_text.append(' | '.join(cell_texts))
        
        return '\n'.join(rows_text)
    
    def list_documents(self, query: str = None, max_results: int = 10) -> List[Dict]:
        """
        List Google Docs (requires Drive API)
        
        Note: This requires additional Drive API scope and setup
        For now, use get_document() with specific document IDs
        """
        # This would require Drive API integration
        # For simplicity, we'll focus on fetching specific documents by ID
        raise NotImplementedError(
            "Use get_document() with specific document IDs. "
            "Document ID can be found in the Google Doc URL: "
            "docs.google.com/document/d/{DOCUMENT_ID}/edit"
        )

