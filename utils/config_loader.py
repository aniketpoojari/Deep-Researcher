"""Configuration loader with environment and YAML support."""

import os
import yaml
from pathlib import Path
from typing import Any, Optional
from dotenv import load_dotenv

# Load .env from project root
_root = Path(__file__).parent.parent
for path in [_root / ".env", Path.cwd() / ".env"]:
    if path.exists():
        load_dotenv(dotenv_path=path, override=True)
        break

from logger.logging import get_logger
logger = get_logger(__name__)


class ConfigLoader:
    """Load configuration from YAML file and environment variables."""

    def __init__(self, config_file: str = "config/config.yaml"):
        self._config = self._load_yaml(config_file)
        logger.info("ConfigLoader initialized")

    def _load_yaml(self, path: str) -> dict:
        """Load YAML config file."""
        if Path(path).exists():
            with open(path) as f:
                return yaml.safe_load(f) or {}
        return {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value using dot notation (e.g., 'research.num_searches')."""
        value = self._config
        for k in key.split('.'):
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def get_env(self, key: str, default: str = None) -> Optional[str]:
        """Get environment variable."""
        return os.getenv(key, default)