# ================================================================================
# FILE: app.py (Enhanced version)
# Description: Main application loop with improved scheduling and error recovery
# ================================================================================

import time
import sys
from datetime import datetime, timedelta
import random
from typing import Optional
from logger_config import logger
from config import config
import helpers as Helper
import reels
import poster
import shorts
import remover
import auth
from instagrapi import Client


class ReelsAutoPilot:
    """
    Main application orchestrator with robust scheduling and error handling.
    """

    def __init__(self):
        """Initialize the application with configuration and scheduling."""
        self.api: Optional[Client] = None
        self.is_running = True

        # Load configuration
        Helper.load_all_config()

        # Initialize schedulers
        self.next_reels_scraper_run = datetime.now()
        self.next_poster_run = datetime.now()
        self.next_remover_run = datetime.now()
        self.next_youtube_run = datetime.now()

        # Error tracking
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5

        logger.info("ReelsAutoPilot initialized")

    def initialize_instagram(self) -> bool:
        """
        Initialize Instagram client if needed.

        Returns:
            True if successful, False otherwise
        """
        if config.IS_ENABLED_REELS_SCRAPER or config.IS_ENABLED_AUTO_POSTER:
            if not self.api:
                logger.info("Initializing Instagram client")
                self.api = auth.login()

                if not self.api:
                    logger.critical("Failed to initialize Instagram client")
                    return False

        return True

    def run_reels_scraper(self):
        """Execute reels scraping task with error handling."""
        try:
            logger.info("=" * 50)
            logger.info("Starting Reels Scraper")

            if not self.api:
                logger.error("Instagram client not initialized")
                return

            reels.main(self.api)

            # Schedule next run
            self.next_reels_scraper_run = datetime.now() + timedelta(
                seconds=int(config.SCRAPER_INTERVAL_IN_MIN) * 60
            )

            logger.info(
                f"Next scraping scheduled for: {self.next_reels_scraper_run.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            self.consecutive_errors = 0

        except Exception as e:
            logger.error(f"Reels scraper failed: {str(e)}", exc_info=True)
            self.handle_error()

    def run_poster(self):
        """Execute posting task with error handling."""
        try:
            logger.info("=" * 50)
            logger.info("Starting Reel Poster")

            if not self.api:
                logger.error("Instagram client not initialized")
                return

            poster.main(self.api)

            # Add random delay to avoid detection
            random_delay = random.randint(5, 20)

            # Schedule next run
            self.next_poster_run = datetime.now() + timedelta(
                seconds=(int(config.POSTING_INTERVAL_IN_MIN) * 60) + random_delay
            )

            logger.info(
                f"Next posting scheduled for: {self.next_poster_run.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            self.consecutive_errors = 0

        except Exception as e:
            logger.error(f"Poster failed: {str(e)}", exc_info=True)
            self.handle_error()

    def run_remover(self):
        """Execute file removal task with error handling."""
        try:
            logger.info("=" * 50)
            logger.info("Starting File Remover")

            remover.main()

            # Schedule next run
            self.next_remover_run = datetime.now() + timedelta(
                seconds=int(config.REMOVE_FILE_AFTER_MINS) * 60
            )

            logger.info(
                f"Next removal scheduled for: {self.next_remover_run.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        except Exception as e:
            logger.error(f"Remover failed: {str(e)}", exc_info=True)

    def run_youtube_scraper(self):
        """Execute YouTube scraping task with error handling."""
        try:
            logger.info("=" * 50)
            logger.info("Starting YouTube Scraper")

            shorts.main()

            # Schedule next run
            self.next_youtube_run = datetime.now() + timedelta(
                seconds=int(config.SCRAPER_INTERVAL_IN_MIN) * 60
            )

            logger.info(
                f"Next YouTube scraping scheduled for: {self.next_youtube_run.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        except Exception as e:
            logger.error(f"YouTube scraper failed: {str(e)}", exc_info=True)

    def handle_error(self):
        """Handle consecutive errors with exponential backoff."""
        self.consecutive_errors += 1

        if self.consecutive_errors >= self.max_consecutive_errors:
            logger.critical(
                f"Too many consecutive errors ({self.consecutive_errors}). Reinitializing..."
            )

            # Try to reinitialize Instagram client
            self.api = None
            self.initialize_instagram()

            # Reset error counter
            self.consecutive_errors = 0

            # Add longer delay
            time.sleep(60)

    def print_status(self):
        """Print current application status."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        status_lines = ["=" * 50, f"ReelsAutoPilot Status - {current_time}", "-" * 50]

        if config.IS_ENABLED_REELS_SCRAPER:
            status_lines.append(
                f"Next Reels Scrape: {self.next_reels_scraper_run.strftime('%H:%M:%S')}"
            )

        if config.IS_ENABLED_AUTO_POSTER:
            status_lines.append(
                f"Next Post: {self.next_poster_run.strftime('%H:%M:%S')}"
            )

        if config.IS_REMOVE_FILES:
            status_lines.append(
                f"Next File Removal: {self.next_remover_run.strftime('%H:%M:%S')}"
            )

        if config.IS_ENABLED_YOUTUBE_SCRAPING:
            status_lines.append(
                f"Next YouTube Scrape: {self.next_youtube_run.strftime('%H:%M:%S')}"
            )

        status_lines.append("=" * 50)

        for line in status_lines:
            logger.debug(line)

    def run(self):
        """Main application loop with scheduling."""
        logger.info("Starting ReelsAutoPilot main loop")

        # Initialize Instagram if needed
        if not self.initialize_instagram():
            logger.critical("Failed to start application")
            return

        # Main loop
        while self.is_running:
            try:
                current_time = datetime.now()

                # Check and run scheduled tasks
                if config.IS_ENABLED_REELS_SCRAPER == "1":
                    if current_time >= self.next_reels_scraper_run:
                        self.run_reels_scraper()

                if config.IS_ENABLED_AUTO_POSTER == "1":
                    if current_time >= self.next_poster_run:
                        self.run_poster()

                if config.IS_REMOVE_FILES == "1":
                    if current_time >= self.next_remover_run:
                        self.run_remover()

                if config.IS_ENABLED_YOUTUBE_SCRAPING == "1":
                    if current_time >= self.next_youtube_run:
                        self.run_youtube_scraper()

                # Print status every 5 minutes
                if current_time.minute % 5 == 0 and current_time.second < 2:
                    self.print_status()

                # Sleep to avoid high CPU usage
                time.sleep(1)

            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                self.is_running = False

            except Exception as e:
                logger.error(f"Unexpected error in main loop: {str(e)}", exc_info=True)
                self.handle_error()
                time.sleep(5)

        logger.info("ReelsAutoPilot stopped")


def main():
    """Entry point for the application."""
    try:
        app = ReelsAutoPilot()
        app.run()
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
