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
