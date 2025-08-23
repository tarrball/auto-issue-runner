"""Configuration management for the Auto Issue Runner."""

import os
from pathlib import Path
from typing import Optional

from pydantic import validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config(BaseSettings):
    """Configuration settings loaded from environment variables."""
    
    # GitHub settings
    github_pat: str
    github_owner: str
    github_repo: str
    github_repo_url: str
    github_default_branch: str = "main"
    
    # Issue labels
    issue_label: str = "auto"
    claude_help_wanted_label: str = "claude-help-wanted"
    
    # Commands
    test_command: Optional[str] = None
    build_command: Optional[str] = None
    
    # Claude settings
    claude_timeout_ms: int = 300000  # 5 minutes
    claude_working_directory: str
    
    # Polling settings
    polling_interval_ms: int = 180000  # 3 minutes
    
    @validator('claude_timeout_ms')
    def timeout_must_be_reasonable(cls, v):
        if v < 30000:  # 30 seconds minimum
            raise ValueError('Claude timeout must be at least 30000ms (30 seconds)')
        return v
    
    @validator('polling_interval_ms')
    def polling_must_be_reasonable(cls, v):
        if v < 60000:  # 1 minute minimum
            raise ValueError('Polling interval must be at least 60000ms (1 minute)')
        return v
    
    @validator('claude_working_directory')
    def working_directory_must_exist(cls, v):
        path = Path(v)
        if not path.exists():
            raise ValueError(f'Claude working directory does not exist: {v}')
        if not path.is_dir():
            raise ValueError(f'Claude working directory is not a directory: {v}')
        return str(path.absolute())
    
    class Config:
        env_file = '.env'
        case_sensitive = False


def load_config() -> Config:
    """Load and validate configuration from environment."""
    return Config()


def print_config_summary(config: Config) -> None:
    """Print a summary of the loaded configuration."""
    print("🔧 Configuration loaded successfully:")
    print(f"   Repository: {config.github_owner}/{config.github_repo}")
    print(f"   Working Directory: {config.claude_working_directory}")
    print(f"   Labels: {config.issue_label}, {config.claude_help_wanted_label}")
    print(f"   Polling Interval: {config.polling_interval_ms / 1000}s")
    print(f"   Claude Timeout: {config.claude_timeout_ms / 1000}s")
    
    if config.test_command:
        print(f"   Test Command: {config.test_command}")
    if config.build_command:
        print(f"   Build Command: {config.build_command}")