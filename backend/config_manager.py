"""Configuration management for the Project Finder application."""

import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env files in multiple locations
def load_env_files():
    """Load .env files from multiple possible locations."""
    # Get the current working directory (project root)
    project_root = Path.cwd()
    backend_dir = Path(__file__).parent

    # Possible .env file locations
    env_locations = [
        project_root / ".env",           # Project root
        backend_dir / ".env",            # Backend directory
        project_root / "backend" / ".env" # Alternative backend path
    ]

    # Load .env files in order (first found takes precedence)
    for env_path in env_locations:
        if env_path.exists():
            load_dotenv(env_path)
            logger = logging.getLogger(__name__)
            logger.info(f"Loaded environment variables from: {env_path}")
            break
    else:
        logger = logging.getLogger(__name__)
        logger.warning("No .env file found in any of the expected locations")

# Load environment variables
load_env_files()

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration from multiple sources."""

    def __init__(self, config_path: str = None):
        """Initialize configuration manager."""
        if config_path is None:
            # Get the directory where this file is located
            backend_dir = Path(__file__).parent
            config_path = backend_dir / "config.json"

        self.config_path = config_path
        self.config = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from config.json file."""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                logger.warning(f"Config file {self.config_path} not found, using defaults")
                self.config = self.get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            self.config = self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "websites": [],
            "database": {
                "url": "sqlite:///./project_finder.db"
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8000
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "app.log",
                "max_bytes": 10485760,
                "backup_count": 5
            },
            "distance_model": {
                "model": "euclidean"
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_websites(self) -> list:
        """Get websites configuration."""
        return self.config.get("websites", [])

    def get_database_url(self) -> str:
        """Get database URL with environment override."""
        env_url = os.getenv("DATABASE_URL")
        if env_url:
            return env_url
        return self.get("database.url", "sqlite:///./project_finder.db")

    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration with environment overrides."""
        server_config = self.get("server", {})

        # Environment overrides
        if os.getenv("HOST"):
            server_config["host"] = os.getenv("HOST")
        if os.getenv("PORT"):
            server_config["port"] = int(os.getenv("PORT"))

        return server_config

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration with environment overrides."""
        logging_config = self.get("logging", {})

        # Environment overrides
        if os.getenv("LOG_LEVEL"):
            logging_config["level"] = os.getenv("LOG_LEVEL")
        if os.getenv("LOG_FILE"):
            logging_config["file"] = os.getenv("LOG_FILE")

        return logging_config

    def get_distance_model(self) -> str:
        """Get distance model configuration."""
        return self.get("distance_model.model", "Euclidian")

    def get_matching_threshold(self) -> float:
        """Get matching threshold configuration."""
        return self.get("matching.threshold", 0.9)

    def get_api_keys(self) -> Dict[str, str]:
        """Get API keys from environment variables, robust to accidental quotes."""
        def clean_key(key):
            if key is None:
                return ''
            return key.strip('"\'')
        return {
            "openai": clean_key(os.getenv("OPENAI_API_KEY", "")),
            "mistral": clean_key(os.getenv("MISTRAL_API_KEY", ""))
        }

    def validate_config(self) -> bool:
        """Validate configuration."""
        required_keys = ["websites", "database", "server", "logging"]

        for key in required_keys:
            if key not in self.config:
                logger.error(f"Missing required config key: {key}")
                return False

        # Validate API keys
        api_keys = self.get_api_keys()
        if not api_keys["openai"]:
            logger.warning("OpenAI API key not found in environment")
        if not api_keys["mistral"]:
            logger.warning("Mistral API key not found in environment")

        return True


# Global configuration instance
config_manager = ConfigManager()