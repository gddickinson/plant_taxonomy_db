"""
Logging configuration for plant taxonomy database.

Provides centralized logging with different levels for different components.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_logging(log_level=logging.INFO, log_file=None, console=True):
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        console: Whether to log to console
        
    Returns:
        Root logger
    """
    # Create logs directory if logging to file
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler with colors
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_formatter = ColoredFormatter(
            '%(levelname)s - %(name)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler without colors
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name):
    """
    Get a logger for a specific module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Create default loggers for different components
def create_component_loggers():
    """Create loggers for different components."""
    loggers = {
        'database': get_logger('plant_taxonomy.database'),
        'api': get_logger('plant_taxonomy.api'),
        'itis': get_logger('plant_taxonomy.api.itis'),
        'gbif': get_logger('plant_taxonomy.api.gbif'),
        'models': get_logger('plant_taxonomy.models'),
        'utils': get_logger('plant_taxonomy.utils')
    }
    return loggers


# Quick setup function for common use cases
def setup_quick_logging(verbose=False):
    """
    Quick logging setup for scripts.
    
    Args:
        verbose: If True, use DEBUG level; otherwise INFO
    """
    level = logging.DEBUG if verbose else logging.INFO
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f"logs/plant_taxonomy_{timestamp}.log"
    
    return setup_logging(log_level=level, log_file=log_file, console=True)
