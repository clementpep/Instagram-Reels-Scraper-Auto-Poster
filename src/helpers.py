# ================================================================================
# FILE: db.py (FIXED VERSION)
# Description: Fixed database models with proper JSON serialization
# ================================================================================

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    select,
    update,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import json
from config import config
from datetime import datetime
from typing import Any, Dict

# Create the database engine
engine = create_engine("sqlite:///" + config.DB_PATH)

# Create a session factory
Session = sessionmaker(bind=engine)

# Create a base class for declarative models
Base = declarative_base()


# Define a Reels model
class Reel(Base):
    """
    Database model for Instagram Reels.
    """

    __tablename__ = "reels"

    id = Column(Integer, primary_key=True)
    post_id = Column(String)
    code = Column(String, unique=True, index=True)  # Add index for faster queries
    account = Column(String)
    file_name = Column(String)
    file_path = Column(String)
    caption = Column(Text)  # Changed to Text for longer captions
    data = Column(Text)  # Changed to Text for larger JSON data
    is_posted = Column(Boolean, default=False)
    posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)  # Track when scraped
    failed_attempts = Column(Integer, default=0)  # Track failed posting attempts


class Config(Base):
    """
    Database model for application configuration.
    """

    __tablename__ = "config"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text)  # Changed to Text for longer values
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# Create the database schema
Base.metadata.create_all(engine, checkfirst=True)


class SafeReelEncoder(json.JSONEncoder):
    """
    Enhanced JSON encoder that safely handles all Instagram media objects.
    Handles complex nested objects and avoids serialization errors.
    """

    def default(self, obj):
        """
        Convert Instagram media objects to JSON-serializable format.

        Args:
            obj: Object to serialize

        Returns:
            JSON-serializable representation
        """
        try:
            # Handle datetime objects
            if hasattr(obj, "isoformat"):
                return obj.isoformat()

            # Handle Location objects
            if hasattr(obj, "__class__") and obj.__class__.__name__ == "Location":
                return self._serialize_location(obj)

            # Handle User objects
            if hasattr(obj, "__class__") and obj.__class__.__name__ == "User":
                return self._serialize_user(obj)

            # Handle Media objects (Reels)
            if hasattr(obj, "pk") and hasattr(obj, "code"):
                return self._serialize_media(obj)

            # Handle other Instagram API objects with __dict__
            if hasattr(obj, "__dict__"):
                return self._safe_dict(obj.__dict__)

            # Default to string representation
            return str(obj)

        except Exception as e:
            # If all else fails, return a safe string representation
            return f"<{obj.__class__.__name__} - serialization failed>"

    def _serialize_location(self, location) -> Dict[str, Any]:
        """
        Safely serialize Location object.

        Args:
            location: Instagram Location object

        Returns:
            Dictionary with location data
        """
        try:
            return {
                "pk": getattr(location, "pk", None),
                "name": getattr(location, "name", None),
                "address": getattr(location, "address", None),
                "lng": getattr(location, "lng", None),
                "lat": getattr(location, "lat", None),
                "external_id": getattr(location, "external_id", None),
                "facebook_places_id": getattr(location, "facebook_places_id", None),
            }
        except:
            return {"name": str(location)}

    def _serialize_user(self, user) -> Dict[str, Any]:
        """
        Safely serialize User object.

        Args:
            user: Instagram User object

        Returns:
            Dictionary with user data
        """
        try:
            return {
                "pk": getattr(user, "pk", None),
                "username": getattr(user, "username", None),
                "full_name": getattr(user, "full_name", None),
                "is_private": getattr(user, "is_private", None),
                "is_verified": getattr(user, "is_verified", None),
            }
        except:
            return {"username": str(user)}

    def _serialize_media(self, media) -> Dict[str, Any]:
        """
        Safely serialize Media/Reel object.

        Args:
            media: Instagram Media object

        Returns:
            Dictionary with media data
        """
        try:
            return {
                "pk": getattr(media, "pk", None),
                "id": getattr(media, "id", None),
                "code": getattr(media, "code", None),
                "taken_at": (
                    getattr(media, "taken_at", None).isoformat()
                    if hasattr(media, "taken_at")
                    else None
                ),
                "media_type": getattr(media, "media_type", None),
                "product_type": getattr(media, "product_type", None),
                "thumbnail_url": (
                    str(getattr(media, "thumbnail_url", None))
                    if hasattr(media, "thumbnail_url")
                    else None
                ),
                "location": (
                    self._serialize_location(media.location)
                    if hasattr(media, "location") and media.location
                    else None
                ),
                "user": (
                    self._serialize_user(media.user)
                    if hasattr(media, "user") and media.user
                    else None
                ),
                "comment_count": getattr(media, "comment_count", None),
                "like_count": getattr(media, "like_count", None),
                "play_count": getattr(media, "play_count", None),
                "view_count": getattr(media, "view_count", None),
                "caption_text": getattr(media, "caption_text", None),
                "video_url": (
                    str(getattr(media, "video_url", None))
                    if hasattr(media, "video_url")
                    else None
                ),
                "video_duration": getattr(media, "video_duration", None),
            }
        except Exception as e:
            return {"code": getattr(media, "code", "unknown"), "error": str(e)}

    def _safe_dict(self, d: dict) -> dict:
        """
        Safely convert a dictionary, handling nested objects.

        Args:
            d: Dictionary to convert

        Returns:
            Safe dictionary
        """
        safe = {}
        for key, value in d.items():
            if key.startswith("_"):  # Skip private attributes
                continue
            try:
                # Recursively handle nested objects
                if hasattr(value, "__dict__"):
                    safe[key] = self._safe_dict(value.__dict__)
                elif isinstance(value, (list, tuple)):
                    safe[key] = [self.default(item) for item in value]
                elif isinstance(value, dict):
                    safe[key] = self._safe_dict(value)
                else:
                    safe[key] = value
            except:
                safe[key] = str(value)
        return safe


# For backward compatibility
ReelEncoder = SafeReelEncoder

# ================================================================================
# FILE: helpers.py (FIXED VERSION)
# Description: Fixed helpers with proper config retrieval
# ================================================================================

# DB
from db import Session, Reel, Config
from sqlalchemy import desc

# Date Time
from datetime import datetime

# Rich
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich import box
from rich.console import Console, Group

# Reels-AutoPilot Config
from config import config
from logger_config import logger
from typing import Optional, Any, List


def print(message):
    """Legacy print function for backward compatibility."""
    logger.info(message)


def get_config(key_name: str) -> Optional[str]:
    """
    Get configuration value from database.

    Args:
        key_name: Configuration key

    Returns:
        Configuration value or None if not found
    """
    session = Session()
    try:
        config_entry = session.query(Config).filter_by(key=key_name).first()
        if config_entry:
            logger.debug(f"Retrieved config {key_name}: {config_entry.value[:50]}...")
            return config_entry.value
        else:
            logger.warning(f"Config key not found: {key_name}")
            return None
    except Exception as e:
        logger.error(f"Error retrieving config {key_name}: {str(e)}")
        return None
    finally:
        session.close()


def get_all_config() -> List[Config]:
    """
    Get all configuration entries from database.

    Returns:
        List of Config objects
    """
    session = Session()
    try:
        config_values = session.query(Config).all()
        logger.debug(f"Retrieved {len(config_values)} config entries")
        return config_values
    except Exception as e:
        logger.error(f"Error retrieving all configs: {str(e)}")
        return []
    finally:
        session.close()


def load_all_config():
    """
    Load all configuration from database into config module.
    Updates the global config object with database values.
    """
    logger.debug("Loading configuration from database")
    config_entries = get_all_config()

    for config_val in config_entries:
        try:
            # Handle list configurations
            if config_val.key in ["ACCOUNTS", "CHANNEL_LINKS"]:
                # Split by comma and strip whitespace
                value = [
                    item.strip() for item in config_val.value.split(",") if item.strip()
                ]
                setattr(config, config_val.key, value)
                logger.debug(f"Loaded list config {config_val.key}: {len(value)} items")
            # Handle numeric configurations
            elif config_val.key in [
                "IS_REMOVE_FILES",
                "REMOVE_FILE_AFTER_MINS",
                "IS_ENABLED_REELS_SCRAPER",
                "IS_ENABLED_AUTO_POSTER",
                "IS_POST_TO_STORY",
                "FETCH_LIMIT",
                "POSTING_INTERVAL_IN_MIN",
                "SCRAPER_INTERVAL_IN_MIN",
                "LIKE_AND_VIEW_COUNTS_DISABLED",
                "DISABLE_COMMENTS",
                "IS_ENABLED_YOUTUBE_SCRAPING",
                "YOUTUBE_SCRAPING_INTERVAL_IN_MINS",
            ]:
                # Try to convert to int, fallback to string
                try:
                    value = int(config_val.value)
                except ValueError:
                    value = config_val.value
                setattr(config, config_val.key, value)
                logger.debug(f"Loaded numeric config {config_val.key}: {value}")
            # Handle string configurations
            else:
                setattr(config, config_val.key, config_val.value)
                logger.debug(f"Loaded string config {config_val.key}")

        except Exception as e:
            logger.error(f"Error loading config {config_val.key}: {str(e)}")

    logger.info("Configuration loaded successfully")


def save_config(key: str, value: Any) -> bool:
    """
    Save or update configuration in database.

    Args:
        key: Configuration key
        value: Configuration value

    Returns:
        True if successful, False otherwise
    """
    session = Session()
    try:
        # Convert lists to comma-separated strings
        if isinstance(value, (list, tuple)):
            value = ",".join(str(item) for item in value)
        else:
            value = str(value)

        # Check if config exists
        exists = session.query(Config).filter_by(key=key).first()

        if not exists:
            # Create new config entry
            config_db = Config(
                key=key,
                value=value,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            session.add(config_db)
            logger.info(f"Created new config: {key}")
        else:
            # Update existing config
            session.query(Config).filter_by(key=key).update(
                {"value": value, "updated_at": datetime.now()}
            )
            logger.info(f"Updated config: {key}")

        session.commit()
        return True

    except Exception as e:
        logger.error(f"Error saving config {key}: {str(e)}")
        session.rollback()
        return False

    finally:
        session.close()


def init_default_config():
    """
    Initialize default configuration if not exists.
    This ensures all required configs are present in the database.
    """
    default_configs = {
        "IS_REMOVE_FILES": "1",
        "REMOVE_FILE_AFTER_MINS": "120",
        "IS_ENABLED_REELS_SCRAPER": "1",
        "IS_ENABLED_AUTO_POSTER": "1",
        "IS_POST_TO_STORY": "1",
        "FETCH_LIMIT": "5",
        "POSTING_INTERVAL_IN_MIN": "30",
        "SCRAPER_INTERVAL_IN_MIN": "720",
        "LIKE_AND_VIEW_COUNTS_DISABLED": "0",
        "DISABLE_COMMENTS": "0",
        "HASHTAGS": "#reels #shorts #likes #follow #ReelsAutoPilot",
        "IS_ENABLED_YOUTUBE_SCRAPING": "1",
        "YOUTUBE_SCRAPING_INTERVAL_IN_MINS": "360",
    }

    for key, default_value in default_configs.items():
        if get_config(key) is None:
            save_config(key, default_value)
            logger.info(f"Initialized default config: {key} = {default_value}")


# Rest of the helper functions remain the same...
def make_my_information() -> Panel:
    """Display developer information panel."""
    sponsor_message = Table.grid(padding=0)
    sponsor_message.add_column(style="green", justify="center")
    sponsor_message.add_row(
        "[red]▄▀█ █░█ █ █▄░█ ▄▀█ █▀ █░█  █▀█ ▄▀█ ▀█▀ █░█ █▀█ █▀▄[/red]"
    )
    sponsor_message.add_row(
        "[red]█▀█ ▀▄▀ █ █░▀█ █▀█ ▄█ █▀█  █▀▄ █▀█ ░█░ █▀█ █▄█ █▄▀[/red]"
    )
    sponsor_message.add_row("")
    sponsor_message.add_row(
        "I'm a highly motivated and dedicated developer, open-source contributor, "
        "and a never-ending learner with a strong passion for cutting-edge technologies "
        "and innovative solutions."
    )
    sponsor_message.add_row("")
    sponsor_message.add_row(
        "[u bright_blue link=https://github.com/Avnsh1111/]Github : https://github.com/Avnsh1111/"
    )
    message_panel = Panel(
        Align.center(
            Group("\n", Align.center(sponsor_message)),
            vertical="middle",
        ),
        box=box.ROUNDED,
        padding=(1, 2),
        title="[b red]About Me!",
        border_style="bright_blue",
    )
    return message_panel


def make_sponsor_message() -> Panel:
    """Display sponsor/application information panel."""
    sponsor_message = Table.grid(padding=0)
    sponsor_message.add_column(style="green", justify="center")
    sponsor_message.add_row(
        "[blue] █▀█ █▀▀ █▀▀ █░░ █▀ ▄▄ ▄▀█ █░█ ▀█▀ █▀█ █▀█ █ █░░ █▀█ ▀█▀[/blue]"
    )
    sponsor_message.add_row(
        "[blue] █▀▄ ██▄ ██▄ █▄▄ ▄█ ░░ █▀█ █▄█ ░█░ █▄█ █▀▀ █ █▄▄ █▄█ ░█░[/blue]"
    )
    sponsor_message.add_row("")
    sponsor_message.add_row(
        "Reels-AutoPilot is a powerful GitHub repository that scrapes reels from "
        "specified Instagram accounts and shorts from YouTube channels, and automatically "
        "posts them to your Instagram account."
    )
    message_panel = Panel(
        Align.center(
            Group("\n", Align.center(sponsor_message)),
            vertical="top",
        ),
        box=box.ROUNDED,
        padding=(1, 2),
        title="[b red]Thanks for using Reels-AutoPilot!",
        border_style="bright_blue",
    )
    return message_panel


def get_latest_ten_reels() -> List[Reel]:
    """Get the latest 10 reels from database."""
    session = Session()
    try:
        reels = session.query(Reel).order_by(desc(Reel.posted_at)).limit(10).all()
        return reels
    except Exception as e:
        logger.error(f"Error getting latest reels: {str(e)}")
        return []
    finally:
        session.close()


def get_reels() -> List[Reel]:
    """Get all reels from database."""
    session = Session()
    try:
        reels = session.query(Reel).order_by(desc(Reel.posted_at)).all()
        return reels
    except Exception as e:
        logger.error(f"Error getting reels: {str(e)}")
        return []
    finally:
        session.close()
