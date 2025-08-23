"""Logging configuration for the auto issue runner."""

import logging
import sys
from pathlib import Path

import colorlog


def setup_logging(level: str = "INFO", log_file: Path = None) -> None:
    """Set up colorful logging with optional file output."""
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter with colors for console
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s %(levelname)-8s%(reset)s %(blue)s%(name)s%(reset)s %(message)s',
        datefmt='%H:%M:%S',
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green', 
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()  # Remove existing handlers
    root_logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_file:
        file_formatter = logging.Formatter(
            '%(asctime)s %(levelname)-8s %(name)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging.getLogger(name)