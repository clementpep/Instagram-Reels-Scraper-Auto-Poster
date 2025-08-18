# ================================================================================
# FILE: init_config.py (FIXED VERSION)
# Description: Complete configuration initialization script
# ================================================================================

"""
Script to initialize or verify database configuration.
Run this before starting the main application.
"""

from db import Session, Config
from logger_config import logger
from datetime import datetime
import sys
import os


def save_config(key: str, value: str) -> bool:
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
            logger.info(f"Created config: {key} = {value[:50]}...")
        else:
            # Update existing config
            session.query(Config).filter_by(key=key).update(
                {"value": value, "updated_at": datetime.now()}
            )
            logger.info(f"Updated config: {key} = {value[:50]}...")

        session.commit()
        return True

    except Exception as e:
        logger.error(f"Error saving config {key}: {str(e)}")
        session.rollback()
        return False

    finally:
        session.close()


def initialize_configuration():
    """
    Initialize all required configuration entries with defaults.
    """
    logger.info("=" * 60)
    logger.info("REELS AUTOPILOT - CONFIGURATION INITIALIZATION")
    logger.info("=" * 60)

    # Default configuration values
    default_configs = {
        # File Management
        "IS_REMOVE_FILES": "1",
        "REMOVE_FILE_AFTER_MINS": "120",
        # Instagram Scraper Settings
        "IS_ENABLED_REELS_SCRAPER": "1",
        "IS_ENABLED_AUTO_POSTER": "1",
        "IS_POST_TO_STORY": "0",  # Disabled by default for safety
        "FETCH_LIMIT": "5",
        "POSTING_INTERVAL_IN_MIN": "30",
        "SCRAPER_INTERVAL_IN_MIN": "720",
        # Instagram Accounts to Scrape
        "ACCOUNTS": "creustel,elouen_la_baleine,victorhabchy",
        # Instagram Post Settings
        "HASHTAGS": "#reels #shorts #viral #instagram #ReelsAutoPilot",
        "LIKE_AND_VIEW_COUNTS_DISABLED": "0",
        "DISABLE_COMMENTS": "0",
        # YouTube Settings
        "IS_ENABLED_YOUTUBE_SCRAPING": "0",  # Disabled by default
        "YOUTUBE_SCRAPING_INTERVAL_IN_MINS": "360",
        "CHANNEL_LINKS": "https://www.youtube.com/@SuprOrdinary,https://www.youtube.com/@DrexLee",
        # Credentials (empty by default - user must configure)
        "USERNAME": "",
        "PASSWORD": "",
        "YOUTUBE_API_KEY": "",
    }

    session = Session()
    initialized_count = 0
    updated_count = 0

    try:
        logger.info("Checking and initializing configuration...")

        for key, default_value in default_configs.items():
            config = session.query(Config).filter_by(key=key).first()

            if not config:
                # Create new config
                config_db = Config(
                    key=key,
                    value=default_value,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                session.add(config_db)
                logger.info(f"✅ Initialized: {key}")
                initialized_count += 1

            elif not config.value and default_value:
                # Update empty config with default
                config.value = default_value
                config.updated_at = datetime.now()
                logger.info(f"📝 Updated empty: {key}")
                updated_count += 1
            else:
                logger.debug(f"✓ Exists: {key}")

        session.commit()

        logger.info("=" * 60)
        logger.info(f"Configuration summary:")
        logger.info(f"  - Initialized: {initialized_count} new configs")
        logger.info(f"  - Updated: {updated_count} empty configs")
        logger.info("=" * 60)

        # Verify critical configs
        return verify_critical_configs(session)

    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}")
        session.rollback()
        return False

    finally:
        session.close()


def verify_critical_configs(session) -> bool:
    """
    Verify that critical configuration entries are set.

    Args:
        session: Database session

    Returns:
        True if all critical configs are set, False otherwise
    """
    logger.info("Verifying critical configuration...")

    critical_configs = {
        "USERNAME": "Instagram username",
        "PASSWORD": "Instagram password",
    }

    missing = []

    for key, description in critical_configs.items():
        config = session.query(Config).filter_by(key=key).first()
        if not config or not config.value:
            missing.append(f"{key} ({description})")

    if missing:
        logger.warning("=" * 60)
        logger.warning("⚠️  MISSING CRITICAL CONFIGURATION:")
        for item in missing:
            logger.warning(f"   - {item}")
        logger.warning("")
        logger.warning("Please configure these values by either:")
        logger.warning("  1. Running: python start.py")
        logger.warning("  2. Or manually updating the database")
        logger.warning("=" * 60)
        return False

    logger.info("✅ All critical configurations are set")
    return True


def display_current_config():
    """
    Display current configuration from database.
    """
    session = Session()
    try:
        configs = session.query(Config).order_by(Config.key).all()

        logger.info("")
        logger.info("=" * 60)
        logger.info("CURRENT CONFIGURATION:")
        logger.info("-" * 60)

        for config in configs:
            # Hide password for security
            if config.key == "PASSWORD" and config.value:
                value = "***hidden***"
            elif config.key == "YOUTUBE_API_KEY" and config.value:
                value = config.value[:10] + "***" if len(config.value) > 10 else "***"
            else:
                value = (
                    config.value[:50] + "..."
                    if len(config.value or "") > 50
                    else config.value
                )

            logger.info(f"{config.key:30} = {value}")

        logger.info("=" * 60)

    finally:
        session.close()


def quick_setup():
    """
    Quick setup for critical configurations.
    """
    logger.info("")
    logger.info("=" * 60)
    logger.info("QUICK SETUP - Enter Instagram Credentials")
    logger.info("-" * 60)

    username = input("Instagram Username: ").strip()
    password = input("Instagram Password: ").strip()

    if username and password:
        save_config("USERNAME", username)
        save_config("PASSWORD", password)
        logger.info("✅ Credentials saved successfully!")

        # Ask for accounts to scrape
        logger.info("")
        accounts = input(
            "Accounts to scrape (comma-separated, or press Enter for defaults): "
        ).strip()
        if accounts:
            save_config("ACCOUNTS", accounts)
            logger.info("✅ Accounts list updated!")

        # Ask for hashtags
        logger.info("")
        hashtags = input("Hashtags for posts (or press Enter for defaults): ").strip()
        if hashtags:
            save_config("HASHTAGS", hashtags)
            logger.info("✅ Hashtags updated!")

        return True
    else:
        logger.error("Username and password are required!")
        return False


def main():
    """
    Main execution function.
    """
    try:
        # Initialize configuration with defaults
        if initialize_configuration():
            logger.info("")
            logger.info("✅ Configuration initialization complete!")

            # Display current configuration
            display_current_config()

            logger.info("")
            logger.info("You can now run: python app.py")
            logger.info("")

        else:
            logger.info("")
            choice = (
                input("Would you like to do a quick setup now? (y/n): ").strip().lower()
            )

            if choice == "y":
                if quick_setup():
                    logger.info("")
                    logger.info("✅ Setup complete! You can now run: python app.py")
                else:
                    logger.error(
                        "Setup failed. Please run start.py for full configuration."
                    )
            else:
                logger.info("Please run start.py to configure the application.")

    except KeyboardInterrupt:
        logger.info("\n\nSetup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
