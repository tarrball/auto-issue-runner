"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from auto_issue_runner.config import Config


@pytest.fixture
def mock_config(tmp_path: Path) -> Config:
    """Create a mock configuration for testing.""" 
    working_dir = tmp_path / "test_repo"
    working_dir.mkdir()
    
    config = MagicMock(spec=Config)
    config.github_pat = "ghp_test_token"
    config.github_owner = "testowner"
    config.github_repo = "testrepo"
    config.github_repo_url = "https://github.com/testowner/testrepo.git"
    config.github_default_branch = "main"
    config.issue_label = "auto"
    config.claude_help_wanted_label = "claude-help-wanted"
    config.test_command = None
    config.build_command = None
    config.claude_timeout_ms = 300000
    config.claude_working_directory = str(working_dir)
    config.polling_interval_ms = 180000
    
    return config


@pytest.fixture
def mock_github_issue() -> dict:
    """Create a mock GitHub issue for testing."""
    return {
        'number': 123,
        'title': 'Test issue title',
        'body': 'Test issue body',
        'html_url': 'https://github.com/testowner/testrepo/issues/123',
        'created_at': '2024-01-01T00:00:00Z',
        'user': {'login': 'testuser'},
        'labels': [
            {'name': 'auto'},
            {'name': 'claude-help-wanted'}
        ]
    }