"""Tests for configuration management."""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from pydantic import ValidationError

from auto_issue_runner.config import Config


class TestConfig:
    """Test configuration loading and validation."""

    def test_valid_config(self, tmp_path: Path) -> None:
        """Test loading valid configuration."""
        working_dir = tmp_path / "test_repo"
        working_dir.mkdir()
        
        with patch.dict('os.environ', {
            'GITHUB_PAT': 'ghp_test_token',
            'GITHUB_OWNER': 'testowner',
            'GITHUB_REPO': 'testrepo',
            'GITHUB_REPO_URL': 'https://github.com/testowner/testrepo.git',
            'CLAUDE_WORKING_DIRECTORY': str(working_dir)
        }):
            config = Config()
            assert config.github_pat == 'ghp_test_token'
            assert config.github_owner == 'testowner'
            assert config.github_repo == 'testrepo'
            assert config.claude_working_directory == str(working_dir)

    def test_missing_required_field(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Config()
            assert 'github_pat' in str(exc_info.value)

    def test_invalid_timeout(self, tmp_path: Path) -> None:
        """Test that invalid timeout raises ValidationError."""
        working_dir = tmp_path / "test_repo"  
        working_dir.mkdir()
        
        with patch.dict('os.environ', {
            'GITHUB_PAT': 'ghp_test_token',
            'GITHUB_OWNER': 'testowner', 
            'GITHUB_REPO': 'testrepo',
            'GITHUB_REPO_URL': 'https://github.com/testowner/testrepo.git',
            'CLAUDE_WORKING_DIRECTORY': str(working_dir),
            'CLAUDE_TIMEOUT_MS': '1000'  # Too low
        }):
            with pytest.raises(ValidationError) as exc_info:
                Config()
            assert 'Claude timeout must be at least' in str(exc_info.value)

    def test_nonexistent_working_directory(self) -> None:
        """Test that nonexistent working directory raises ValidationError."""
        with patch.dict('os.environ', {
            'GITHUB_PAT': 'ghp_test_token',
            'GITHUB_OWNER': 'testowner',
            'GITHUB_REPO': 'testrepo', 
            'GITHUB_REPO_URL': 'https://github.com/testowner/testrepo.git',
            'CLAUDE_WORKING_DIRECTORY': '/nonexistent/path'
        }):
            with pytest.raises(ValidationError) as exc_info:
                Config()
            assert 'does not exist' in str(exc_info.value)