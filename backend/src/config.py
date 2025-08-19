# ================================================================================
# FILE: config.py (Enhanced version)
# Description: Enhanced configuration management with validation and type hints
# ================================================================================

import os
from dotenv import load_dotenv
from typing import List, Optional
from dataclasses import dataclass, field
from backend.src.logger_config import logger
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class AppConfig:
    """
    Application configuration with validation and type safety.
    """

    # Paths
    CURRENT_DIR: str = str(BASE_DIR)
    DB_PATH: str = str(BASE_DIR / "database" / "sqlite.db")
    DOWNLOAD_DIR: str = str(BASE_DIR / "downloads")
    LOG_DIR: str = str(BASE_DIR / "database" / "logs")

    # File Management
    IS_REMOVE_FILES: int = 1
    REMOVE_FILE_AFTER_MINS: int = 120

    # Instagram Configuration
    IS_ENABLED_REELS_SCRAPER: int = 1
    IS_ENABLED_AUTO_POSTER: int = 1
    IS_POST_TO_STORY: int = 1
    FETCH_LIMIT: int = 5
    POSTING_INTERVAL_IN_MIN: int = 30
    SCRAPER_INTERVAL_IN_MIN: int = 720
    ACCOUNTS: List[str] = field(
        default_factory=lambda: [
            "karenxcheng",
            "kevinbparry",
            "creustel",
            "elouen_la_baleine",
            "victorhabchy",
        ]
    )
    LIKE_AND_VIEW_COUNTS_DISABLED: int = 0
    DISABLE_COMMENTS: int = 0
    HASHTAGS: str = "#reels #shorts #likes #follow #ReelsAutoPilot"

    # YouTube Configuration
    IS_ENABLED_YOUTUBE_SCRAPING: int = 1
    YOUTUBE_SCRAPING_INTERVAL_IN_MINS: int = 360
    CHANNEL_LINKS: List[str] = field(
        default_factory=lambda: [
            "https://www.youtube.com/@AlanChikinChow",
            "https://www.youtube.com/@SuprOrdinary",
            "https://www.youtube.com/@DrexLee",
        ]
    )

    # Authentication (will be loaded from database)
    USERNAME: str = os.getenv("USERNAME", "")
    PASSWORD: str = os.getenv("PASSWORD", "")
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")

    def __post_init__(self):
        """
        Validate configuration after initialization.
        """
        self._create_directories()
        self._validate_config()

    def _create_directories(self):
        """Create necessary directories if they don't exist."""
        for directory in [
            self.DOWNLOAD_DIR,
            self.LOG_DIR,
            os.path.dirname(self.DB_PATH),
        ]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"Created directory: {directory}")

    def _validate_config(self):
        """Validate configuration values."""
        validations = [
            (self.FETCH_LIMIT > 0, "FETCH_LIMIT must be positive"),
            (
                self.POSTING_INTERVAL_IN_MIN > 0,
                "POSTING_INTERVAL_IN_MIN must be positive",
            ),
            (
                self.SCRAPER_INTERVAL_IN_MIN > 0,
                "SCRAPER_INTERVAL_IN_MIN must be positive",
            ),
            (
                self.REMOVE_FILE_AFTER_MINS > 0,
                "REMOVE_FILE_AFTER_MINS must be positive",
            ),
        ]

        for condition, message in validations:
            if not condition:
                logger.error(f"Configuration validation failed: {message}")
                raise ValueError(message)


# Create global config instance
config = AppConfig()
