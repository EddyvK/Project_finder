"""Logging configuration for the Project Finder application."""

import logging
import logging.handlers
import os
from pathlib import Path
from backend.config_manager import config_manager


def setup_logging() -> None:
    """Setup logging configuration."""
    log_config = config_manager.get_logging_config()

    # Create logs directory if it doesn't exist
    log_file = log_config.get("file", "app.log")
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_config.get("level", "INFO")))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=log_config.get("max_bytes", 10485760),  # 10MB
        backupCount=log_config.get("backup_count", 5),
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_config.get("level", "INFO")))
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)

    logging.info("Logging configuration initialized")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)