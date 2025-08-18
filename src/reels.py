# ================================================================================
# FILE: reels.py (UPDATED WITH FIX)
# Description: Fixed reels scraper with proper JSON encoding
# ================================================================================

from instagrapi import Client
from instagrapi.exceptions import MediaNotFound, UserNotFound
from db import Session, Reel, SafeReelEncoder  # Use SafeReelEncoder
import json
from config import config
import os
from typing import List, Optional
from logger_config import logger
import helpers as Helper
from datetime import datetime


class ReelsScraper:
    """
    Handles scraping of Instagram Reels with robust error handling.
    """

    def __init__(self, api: Client):
        """
        Initialize scraper with authenticated client.

        Args:
            api: Authenticated Instagram client
        """
        self.api = api
        self.session = Session()

    def scrape_account(self, account: str) -> List:
        """
        Scrape reels from a single Instagram account.

        Args:
            account: Instagram username to scrape

        Returns:
            List of reel objects
        """
        try:
            logger.info(f"Starting to scrape account: {account}")

            # Get user ID
            user_id = self.api.user_id_from_username(account)
            logger.debug(f"User ID for {account}: {user_id}")

            # Fetch media
            medias = self.api.user_medias(user_id, config.FETCH_LIMIT)
            logger.debug(f"Fetched {len(medias)} media items from {account}")

            # Filter for reels
            reels = [
                item
                for item in medias
                if getattr(item, "product_type", None) == "clips"
                and getattr(item, "media_type", None) == 2
            ]

            logger.info(f"Found {len(reels)} reels from {account}")
            return reels

        except UserNotFound:
            logger.error(f"User not found: {account}")
            return []
        except Exception as e:
            logger.error(f"Error scraping {account}: {type(e).__name__}: {str(e)}")
            return []

    def download_and_save_reel(self, reel, account: str) -> bool:
        """
        Download a reel and save it to the database.

        Args:
            reel: Reel object from Instagram API
            account: Account username

        Returns:
            True if successful, False otherwise
        """
        try:
            video_url = getattr(reel, "video_url", None)
            code = getattr(reel, "code", None)

            if not video_url or not code:
                logger.warning(f"Missing video_url or code for reel from {account}")
                return False

            # Check if already exists
            if self.session.query(Reel).filter_by(code=code).first():
                logger.debug(f"Reel already exists: {code}")
                return False

            # Download video
            filename = self._get_filename_from_url(video_url)
            filepath = os.path.join(config.DOWNLOAD_DIR, filename)

            logger.info(f"Downloading reel {code} from {account}")
            self.api.video_download_by_url(video_url, folder=config.DOWNLOAD_DIR)

            # Verify download
            if not self._verify_download(filepath):
                logger.error(f"Download verification failed for {code}")
                return False

            # Save to database with safe JSON encoding
            self._save_to_database(reel, account, filename, filepath, code)
            logger.info(f"Successfully saved reel {code} to database")
            return True

        except Exception as e:
            logger.error(f"Error downloading reel {code}: {type(e).__name__}: {str(e)}")
            return False

    def _get_filename_from_url(self, url: str) -> str:
        """
        Extract filename from URL.

        Args:
            url: Video URL

        Returns:
            Filename string
        """
        path = url.split("/")
        filename = path[-1]
        return filename.split("?")[0]

    def _verify_download(self, filepath: str, min_size: int = 10000) -> bool:
        """
        Verify that a file was downloaded successfully.

        Args:
            filepath: Path to downloaded file
            min_size: Minimum acceptable file size in bytes

        Returns:
            True if file is valid, False otherwise
        """
        if not os.path.exists(filepath):
            logger.error(f"File does not exist: {filepath}")
            return False

        file_size = os.path.getsize(filepath)
        if file_size < min_size:
            logger.error(f"File too small ({file_size} bytes): {filepath}")
            return False

        logger.debug(f"File verified: {filepath} ({file_size} bytes)")
        return True

    def _save_to_database(
        self, reel, account: str, filename: str, filepath: str, code: str
    ):
        """
        Save reel information to database with safe JSON encoding.

        Args:
            reel: Reel object
            account: Account username
            filename: Downloaded filename
            filepath: Full file path
            code: Reel code
        """
        try:
            # Use SafeReelEncoder for JSON serialization
            reel_json = json.dumps(reel, cls=SafeReelEncoder)

            reel_db = Reel(
                post_id=getattr(reel, "id", None),
                code=code,
                account=account,
                caption=getattr(reel, "caption_text", ""),
                file_name=filename,
                file_path=filepath,
                data=reel_json,  # Safely serialized JSON
                is_posted=False,
                created_at=datetime.now(),
            )
            self.session.add(reel_db)
            self.session.commit()

            logger.debug(f"Reel {code} saved to database successfully")

        except Exception as e:
            logger.error(f"Database error saving reel {code}: {str(e)}")
            self.session.rollback()
            raise

    def run(self):
        """
        Main execution method for scraping all configured accounts.
        """
        Helper.load_all_config()

        total_downloaded = 0
        failed_accounts = []

        logger.info(f"Starting reels scraping for {len(config.ACCOUNTS)} accounts")

        for account in config.ACCOUNTS:
            try:
                reels = self.scrape_account(account)
                downloaded = 0

                for reel in reels:
                    if self.download_and_save_reel(reel, account):
                        downloaded += 1

                total_downloaded += downloaded
                logger.info(f"Downloaded {downloaded} new reels from {account}")

            except Exception as e:
                logger.error(f"Failed to process account {account}: {str(e)}")
                failed_accounts.append(account)

        logger.info(f"Scraping complete. Downloaded {total_downloaded} new reels")

        if failed_accounts:
            logger.warning(f"Failed accounts: {', '.join(failed_accounts)}")

        self.session.close()


def main(api: Client):
    """
    Legacy main function for backward compatibility.

    Args:
        api: Authenticated Instagram client
    """
    if not api:
        logger.error("No authenticated client provided")
        return

    scraper = ReelsScraper(api)
    scraper.run()
