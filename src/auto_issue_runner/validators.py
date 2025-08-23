"""Input validation utilities for security."""

import re
from typing import Any, Dict


def sanitize_branch_name(name: str) -> str:
    """Sanitize a branch name to prevent injection attacks."""
    # Remove dangerous characters and limit length
    sanitized = re.sub(r'[^\w\-./]', '-', name)
    sanitized = re.sub(r'-+', '-', sanitized)  # Collapse multiple dashes
    sanitized = sanitized.strip('-')  # Remove leading/trailing dashes
    return sanitized[:100]  # Limit length


def validate_github_issue(issue: Dict[str, Any]) -> bool:
    """Validate GitHub issue data structure."""
    required_fields = ['number', 'title', 'html_url', 'user', 'labels']
    
    # Check required fields exist
    for field in required_fields:
        if field not in issue:
            return False
    
    # Validate types
    if not isinstance(issue['number'], int):
        return False
    
    if not isinstance(issue['title'], str) or len(issue['title']) > 500:
        return False
        
    if not isinstance(issue['html_url'], str) or not issue['html_url'].startswith('https://github.com/'):
        return False
    
    # Validate user structure
    if not isinstance(issue['user'], dict) or 'login' not in issue['user']:
        return False
    
    # Validate labels structure
    if not isinstance(issue['labels'], list):
        return False
    
    for label in issue['labels']:
        if not isinstance(label, dict) or 'name' not in label:
            return False
    
    return True


def sanitize_commit_message(message: str) -> str:
    """Sanitize commit message to prevent injection."""
    # Remove control characters and limit length
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', message)
    return sanitized[:500]  # Reasonable commit message length