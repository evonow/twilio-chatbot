"""
GitLab Connector
Fetches and processes GitLab repository content for ingestion into the knowledge base
"""

import os
import requests
from typing import List, Dict, Optional
from datetime import datetime
import base64

class GitLabConnector:
    def __init__(self, gitlab_url: str = None, access_token: str = None):
        """
        Initialize GitLab connector
        
        Args:
            gitlab_url: GitLab instance URL (e.g., 'https://gitlab.com' or 'https://gitlab.yourcompany.com')
            access_token: GitLab personal access token or project access token
        """
        self.gitlab_url = gitlab_url or os.getenv('GITLAB_URL', 'https://gitlab.com')
        self.access_token = access_token or os.getenv('GITLAB_ACCESS_TOKEN')
        
        if not self.access_token:
            raise ValueError(
                "GitLab access token required. Set GITLAB_ACCESS_TOKEN environment variable "
                "or pass access_token parameter."
            )
        
        # Remove trailing slash from URL
        self.gitlab_url = self.gitlab_url.rstrip('/')
        self.api_url = f"{self.gitlab_url}/api/v4"
        
        self.headers = {
            'PRIVATE-TOKEN': self.access_token,
            'Content-Type': 'application/json'
        }
    
    def get_project(self, project_id: str) -> Dict:
        """
        Get project information
        
        Args:
            project_id: Project ID (can be namespace/project-name or numeric ID)
            
        Returns:
            Project information dictionary
        """
        url = f"{self.api_url}/projects/{project_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_repository_tree(self, project_id: str, path: str = '', ref: str = 'main', recursive: bool = True) -> List[Dict]:
        """
        Get repository file tree
        
        Args:
            project_id: Project ID
            path: Path within repository (empty for root)
            ref: Branch or tag name (default: 'main')
            recursive: Whether to get files recursively
            
        Returns:
            List of file/directory information
        """
        url = f"{self.api_url}/projects/{project_id}/repository/tree"
        params = {
            'path': path,
            'ref': ref,
            'recursive': 'true' if recursive else 'false'
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_file_content(self, project_id: str, file_path: str, ref: str = 'main') -> Dict:
        """
        Get file content from repository
        
        Args:
            project_id: Project ID
            file_path: Path to file in repository
            ref: Branch or tag name (default: 'main')
            
        Returns:
            Dictionary with file content and metadata
        """
        url = f"{self.api_url}/projects/{project_id}/repository/files/{file_path}"
        params = {'ref': ref}
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        file_data = response.json()
        
        # Decode base64 content
        content = base64.b64decode(file_data['content']).decode('utf-8', errors='ignore')
        
        return {
            'file_path': file_path,
            'content': content,
            'encoding': file_data.get('encoding', 'base64'),
            'size': file_data.get('size', 0),
            'ref': ref,
            'source': 'gitlab'
        }
    
    def get_commits(self, project_id: str, ref: str = 'main', since: str = None, until: str = None, max_results: int = 50) -> List[Dict]:
        """
        Get commit history
        
        Args:
            project_id: Project ID
            ref: Branch name (default: 'main')
            since: Get commits since this date (ISO 8601 format)
            until: Get commits until this date (ISO 8601 format)
            max_results: Maximum number of commits to return
            
        Returns:
            List of commit dictionaries
        """
        url = f"{self.api_url}/projects/{project_id}/repository/commits"
        params = {
            'ref_name': ref,
            'per_page': min(max_results, 100)  # GitLab API limit
        }
        
        if since:
            params['since'] = since
        if until:
            params['until'] = until
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_commit_messages(self, project_id: str, ref: str = 'main', max_results: int = 100) -> List[Dict]:
        """
        Get commit messages formatted for knowledge base
        
        Args:
            project_id: Project ID
            ref: Branch name (default: 'main')
            max_results: Maximum number of commits
            
        Returns:
            List of formatted commit documents
        """
        commits = self.get_commits(project_id, ref=ref, max_results=max_results)
        
        documents = []
        for commit in commits:
            commit_message = commit.get('message', '')
            commit_id = commit.get('id', '')[:8]  # Short commit hash
            author = commit.get('author_name', 'Unknown')
            created_at = commit.get('created_at', '')
            
            # Format as release note entry
            formatted_text = f"""Commit: {commit_id}
Author: {author}
Date: {created_at}

{commit_message}
"""
            
            documents.append({
                'content': formatted_text,
                'metadata': {
                    'source': 'gitlab_commits',
                    'commit_id': commit_id,
                    'author': author,
                    'date': created_at,
                    'project_id': project_id,
                    'ref': ref
                }
            })
        
        return documents
    
    def get_readme_files(self, project_id: str, ref: str = 'main') -> List[Dict]:
        """
        Get README files from repository
        
        Args:
            project_id: Project ID
            ref: Branch name (default: 'main')
            
        Returns:
            List of README file documents
        """
        tree = self.get_repository_tree(project_id, ref=ref, recursive=True)
        
        readme_files = []
        for item in tree:
            if item['type'] == 'blob':  # It's a file
                file_path = item['name'].lower()
                # Look for README files
                if file_path.startswith('readme') or file_path.endswith('readme.md') or file_path.endswith('readme.txt'):
                    try:
                        file_content = self.get_file_content(project_id, item['path'], ref=ref)
                        readme_files.append({
                            'content': file_content['content'],
                            'metadata': {
                                'source': 'gitlab_readme',
                                'file_path': item['path'],
                                'project_id': project_id,
                                'ref': ref
                            }
                        })
                    except Exception as e:
                        print(f"Error reading {item['path']}: {e}")
                        continue
        
        return readme_files
    
    def get_release_notes(self, project_id: str, ref: str = 'main', file_patterns: List[str] = None) -> List[Dict]:
        """
        Get release notes files from repository
        
        Args:
            project_id: Project ID
            ref: Branch name (default: 'main')
            file_patterns: List of file patterns to search for (default: ['CHANGELOG', 'RELEASE', 'RELEASES'])
            
        Returns:
            List of release notes documents
        """
        if file_patterns is None:
            file_patterns = ['CHANGELOG', 'RELEASE', 'RELEASES']
        
        tree = self.get_repository_tree(project_id, ref=ref, recursive=True)
        
        release_files = []
        for item in tree:
            if item['type'] == 'blob':  # It's a file
                file_name = item['name'].upper()
                # Check if file matches any pattern
                if any(pattern in file_name for pattern in file_patterns):
                    try:
                        file_content = self.get_file_content(project_id, item['path'], ref=ref)
                        release_files.append({
                            'content': file_content['content'],
                            'metadata': {
                                'source': 'gitlab_release_notes',
                                'file_path': item['path'],
                                'project_id': project_id,
                                'ref': ref
                            }
                        })
                    except Exception as e:
                        print(f"Error reading {item['path']}: {e}")
                        continue
        
        return release_files
    
    def ingest_project_content(self, project_id: str, ref: str = 'main', 
                              include_commits: bool = True,
                              include_readmes: bool = True,
                              include_release_notes: bool = True,
                              max_commits: int = 100) -> List[Dict]:
        """
        Ingest all relevant content from a GitLab project
        
        Args:
            project_id: Project ID
            ref: Branch name (default: 'main')
            include_commits: Whether to include commit messages
            include_readmes: Whether to include README files
            include_release_notes: Whether to include release notes files
            max_commits: Maximum number of commits to include
            
        Returns:
            List of all documents ready for ingestion
        """
        all_documents = []
        
        if include_readmes:
            print(f"Fetching README files from {project_id}...")
            readmes = self.get_readme_files(project_id, ref=ref)
            all_documents.extend(readmes)
            print(f"Found {len(readmes)} README file(s)")
        
        if include_release_notes:
            print(f"Fetching release notes from {project_id}...")
            release_notes = self.get_release_notes(project_id, ref=ref)
            all_documents.extend(release_notes)
            print(f"Found {len(release_notes)} release notes file(s)")
        
        if include_commits:
            print(f"Fetching commits from {project_id}...")
            commits = self.get_commit_messages(project_id, ref=ref, max_results=max_commits)
            all_documents.extend(commits)
            print(f"Found {len(commits)} commit(s)")
        
        return all_documents

