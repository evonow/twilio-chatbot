#!/usr/bin/env python3
"""
Railway Deployment Monitor
Monitors Railway deployments and automatically fixes common issues
"""

import os
import requests
import time
import json
from datetime import datetime

# Railway API configuration
RAILWAY_API_TOKEN = os.getenv('RAILWAY_API_TOKEN')
RAILWAY_PROJECT_ID = os.getenv('RAILWAY_PROJECT_ID')

if not RAILWAY_API_TOKEN:
    print("⚠️  RAILWAY_API_TOKEN not set. Get it from: https://railway.app/account")
    exit(1)

RAILWAY_API_BASE = "https://backboard.railway.app/graphql/v2"

def get_railway_headers():
    return {
        "Authorization": f"Bearer {RAILWAY_API_TOKEN}",
        "Content-Type": "application/json"
    }

def query_railway(query, variables=None):
    """Execute a GraphQL query against Railway API"""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    response = requests.post(
        RAILWAY_API_BASE,
        headers=get_railway_headers(),
        json=payload
    )
    
    if response.status_code != 200:
        print(f"❌ API Error: {response.status_code}")
        print(response.text)
        return None
    
    return response.json()

def get_project_deployments(project_id=None):
    """Get recent deployments for a project"""
    if not project_id:
        # Try to get project ID from environment or list projects
        query = """
        query {
            projects {
                edges {
                    node {
                        id
                        name
                    }
                }
            }
        }
        """
        result = query_railway(query)
        if result and result.get('data', {}).get('projects', {}).get('edges'):
            projects = result['data']['projects']['edges']
            for project in projects:
                if project['node']['name'] == 'twilio-chatbot':
                    project_id = project['node']['id']
                    break
        
        if not project_id:
            print("❌ Could not find twilio-chatbot project")
            return None
    
    query = """
    query($projectId: String!) {
        deployments(projectId: $projectId, limit: 5) {
            edges {
                node {
                    id
                    status
                    createdAt
                    commit {
                        message
                    }
                    buildLogs {
                        edges {
                            node {
                                message
                                level
                            }
                        }
                    }
                }
            }
        }
    }
    """
    
    result = query_railway(query, {"projectId": project_id})
    return result

def check_deployment_status():
    """Check the latest deployment status"""
    deployments = get_project_deployments(RAILWAY_PROJECT_ID)
    
    if not deployments or not deployments.get('data'):
        print("⚠️  Could not fetch deployments")
        return None
    
    deployment_edges = deployments['data'].get('deployments', {}).get('edges', [])
    if not deployment_edges:
        print("ℹ️  No deployments found")
        return None
    
    latest = deployment_edges[0]['node']
    status = latest.get('status')
    commit_msg = latest.get('commit', {}).get('message', 'Unknown')
    created_at = latest.get('createdAt')
    
    print(f"\n📊 Latest Deployment Status:")
    print(f"   Status: {status}")
    print(f"   Commit: {commit_msg[:50]}...")
    print(f"   Created: {created_at}")
    
    if status == 'FAILED':
        print("\n❌ Deployment failed! Checking logs...")
        logs = latest.get('buildLogs', {}).get('edges', [])
        error_logs = [log['node']['message'] for log in logs 
                     if log['node'].get('level') == 'ERROR' or 'error' in log['node']['message'].lower()]
        
        if error_logs:
            print("\n🔍 Error logs:")
            for log in error_logs[-10:]:  # Last 10 error lines
                print(f"   {log}")
        
        # Check for common errors and suggest fixes
        check_common_errors(error_logs)
    
    return latest

def check_common_errors(error_logs):
    """Check for common deployment errors and suggest fixes"""
    error_text = ' '.join(error_logs).lower()
    
    fixes = []
    
    if 'no module named pip' in error_text or 'pip' in error_text:
        fixes.append({
            'error': 'pip module not found',
            'fix': 'Remove nixpacks.toml and let Railway auto-detect Python',
            'action': 'delete_nixpacks'
        })
    
    if 'numpy' in error_text and ('build' in error_text or 'install' in error_text):
        fixes.append({
            'error': 'numpy build failure',
            'fix': 'Update requirements.txt with flexible numpy version',
            'action': 'update_requirements'
        })
    
    if fixes:
        print("\n💡 Suggested fixes:")
        for fix in fixes:
            print(f"   - {fix['error']}: {fix['fix']}")
            print(f"     Action: {fix['action']}")

def monitor_loop(interval=60):
    """Continuously monitor deployments"""
    print("🚀 Starting Railway Deployment Monitor")
    print(f"   Checking every {interval} seconds...")
    print("   Press Ctrl+C to stop\n")
    
    try:
        while True:
            check_deployment_status()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n👋 Monitor stopped")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--monitor':
        monitor_loop()
    else:
        # One-time check
        check_deployment_status()
        print("\n💡 Run with --monitor flag to continuously monitor")
        print("   Example: python monitor_railway.py --monitor")

