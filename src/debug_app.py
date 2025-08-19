# ================================================================================
# FILE: debug_app.py - Version debug pour diagnostiquer le problème
# Description: Version avec logs détaillés pour comprendre ce qui bloque
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


class DebugReelsAutoPilot:
    """
    Version debug de ReelsAutoPilot avec logs détaillés.
    """

    def __init__(self):
        """Initialize the application with configuration and scheduling."""
        logger.info("🚀 Initializing DebugReelsAutoPilot...")

        self.api: Optional[Client] = None
        self.is_running = True
        self.iteration_count = 0

        # Load configuration
        logger.info("📄 Loading configuration...")
        Helper.load_all_config()

        # Log current config values
        logger.info(f"📊 Config check:")
        logger.info(
            f"   - IS_ENABLED_REELS_SCRAPER: {config.IS_ENABLED_REELS_SCRAPER} (type: {type(config.IS_ENABLED_REELS_SCRAPER)})"
        )
        logger.info(
            f"   - IS_ENABLED_AUTO_POSTER: {config.IS_ENABLED_AUTO_POSTER} (type: {type(config.IS_ENABLED_AUTO_POSTER)})"
        )
        logger.info(
            f"   - IS_REMOVE_FILES: {config.IS_REMOVE_FILES} (type: {type(config.IS_REMOVE_FILES)})"
        )
        logger.info(
            f"   - IS_ENABLED_YOUTUBE_SCRAPING: {config.IS_ENABLED_YOUTUBE_SCRAPING} (type: {type(config.IS_ENABLED_YOUTUBE_SCRAPING)})"
        )

        # Initialize schedulers
        current_time = datetime.now()
        logger.info(f"⏰ Current time: {current_time}")

        self.next_reels_scraper_run = current_time
        self.next_poster_run = current_time
        self.next_remover_run = current_time
        self.next_youtube_run = current_time

        logger.info(f"📅 Scheduled times:")
        logger.info(f"   - Next reels scraper: {self.next_reels_scraper_run}")
        logger.info(f"   - Next poster: {self.next_poster_run}")
        logger.info(f"   - Next remover: {self.next_remover_run}")
        logger.info(f"   - Next YouTube: {self.next_youtube_run}")

        # Error tracking
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5

        logger.info("✅ DebugReelsAutoPilot initialized")

    def initialize_instagram(self) -> bool:
        """Initialize Instagram client if needed."""
        logger.info("🔐 Checking if Instagram client needed...")

        needs_instagram = (
            str(config.IS_ENABLED_REELS_SCRAPER) == "1"
            or str(config.IS_ENABLED_AUTO_POSTER) == "1"
        )

        logger.info(f"   - Needs Instagram: {needs_instagram}")

        if needs_instagram:
            if not self.api:
                logger.info("🔑 Initializing Instagram client...")
                self.api = auth.login()

                if not self.api:
                    logger.critical("❌ Failed to initialize Instagram client")
                    return False
                else:
                    logger.info("✅ Instagram client initialized successfully")
            else:
                logger.info("♻️ Instagram client already initialized")

        return True

    def check_conditions(self):
        """Check what conditions are met in the main loop."""
        current_time = datetime.now()

        logger.info(f"🔍 Checking conditions at {current_time.strftime('%H:%M:%S')}:")

        # Check reels scraper
        reels_enabled = str(config.IS_ENABLED_REELS_SCRAPER) == "1"
        reels_time_ok = current_time >= self.next_reels_scraper_run
        logger.info(
            f"   - Reels scraper: enabled={reels_enabled}, time_ok={reels_time_ok}"
        )

        # Check poster
        poster_enabled = str(config.IS_ENABLED_AUTO_POSTER) == "1"
        poster_time_ok = current_time >= self.next_poster_run
        logger.info(
            f"   - Auto poster: enabled={poster_enabled}, time_ok={poster_time_ok}"
        )

        # Check remover
        remover_enabled = str(config.IS_REMOVE_FILES) == "1"
        remover_time_ok = current_time >= self.next_remover_run
        logger.info(
            f"   - File remover: enabled={remover_enabled}, time_ok={remover_time_ok}"
        )

        # Check YouTube
        youtube_enabled = str(config.IS_ENABLED_YOUTUBE_SCRAPING) == "1"
        youtube_time_ok = current_time >= self.next_youtube_run
        logger.info(
            f"   - YouTube scraper: enabled={youtube_enabled}, time_ok={youtube_time_ok}"
        )

        return {
            "reels": reels_enabled and reels_time_ok,
            "poster": poster_enabled and poster_time_ok,
            "remover": remover_enabled and remover_time_ok,
            "youtube": youtube_enabled and youtube_time_ok,
        }

    def run_reels_scraper(self):
        """Execute reels scraping task with error handling."""
        try:
            logger.info("🎬 Starting Reels Scraper")

            if not self.api:
                logger.error("❌ Instagram client not initialized")
                return

            reels.main(self.api)

            # Schedule next run
            self.next_reels_scraper_run = datetime.now() + timedelta(
                seconds=int(config.SCRAPER_INTERVAL_IN_MIN) * 60
            )

            logger.info(
                f"📅 Next scraping scheduled for: {self.next_reels_scraper_run.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        except Exception as e:
            logger.error(f"❌ Reels scraper failed: {str(e)}", exc_info=True)

    def run_poster(self):
        """Execute posting task with error handling."""
        try:
            logger.info("📤 Starting Reel Poster")

            if not self.api:
                logger.error("❌ Instagram client not initialized")
                return

            poster.main(self.api)

            # Schedule next run
            self.next_poster_run = datetime.now() + timedelta(
                seconds=int(config.POSTING_INTERVAL_IN_MIN) * 60
            )

            logger.info(
                f"📅 Next posting scheduled for: {self.next_poster_run.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        except Exception as e:
            logger.error(f"❌ Poster failed: {str(e)}", exc_info=True)

    def run_remover(self):
        """Execute file removal task with error handling."""
        try:
            logger.info("🗑️ Starting File Remover")
            remover.main()

            # Schedule next run
            self.next_remover_run = datetime.now() + timedelta(
                seconds=int(config.REMOVE_FILE_AFTER_MINS) * 60
            )

            logger.info(
                f"📅 Next removal scheduled for: {self.next_remover_run.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        except Exception as e:
            logger.error(f"❌ Remover failed: {str(e)}")

    def run_youtube_scraper(self):
        """Execute YouTube scraping task with error handling."""
        try:
            logger.info("🎥 Starting YouTube Scraper")
            shorts.main()

            # Schedule next run
            self.next_youtube_run = datetime.now() + timedelta(
                seconds=int(config.SCRAPER_INTERVAL_IN_MIN) * 60
            )

            logger.info(
                f"📅 Next YouTube scraping scheduled for: {self.next_youtube_run.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        except Exception as e:
            logger.error(f"❌ YouTube scraper failed: {str(e)}")

    def run(self):
        """Main application loop with detailed debugging."""
        logger.info("🚀 Starting DebugReelsAutoPilot main loop")

        # Initialize Instagram if needed
        if not self.initialize_instagram():
            logger.critical("💥 Failed to start application")
            return

        logger.info("🔄 Entering main loop...")

        # Run for max 10 iterations in debug mode
        max_iterations = 10

        while self.is_running and self.iteration_count < max_iterations:
            try:
                self.iteration_count += 1
                logger.info(f"\n{'='*50}")
                logger.info(f"🔄 Main loop iteration #{self.iteration_count}")
                logger.info(f"{'='*50}")

                # Check what conditions are met
                conditions = self.check_conditions()

                # Execute tasks based on conditions
                if conditions["reels"]:
                    logger.info("▶️ Executing reels scraper...")
                    self.run_reels_scraper()

                if conditions["poster"]:
                    logger.info("▶️ Executing poster...")
                    self.run_poster()

                if conditions["remover"]:
                    logger.info("▶️ Executing remover...")
                    self.run_remover()

                if conditions["youtube"]:
                    logger.info("▶️ Executing YouTube scraper...")
                    self.run_youtube_scraper()

                # If no tasks executed
                if not any(conditions.values()):
                    logger.info("😴 No tasks to execute in this iteration")

                logger.info(f"⏱️ Sleeping for 3 seconds...")
                time.sleep(3)

            except KeyboardInterrupt:
                logger.info("🛑 Received interrupt signal, shutting down...")
                self.is_running = False

            except Exception as e:
                logger.error(
                    f"💥 Unexpected error in main loop: {str(e)}", exc_info=True
                )
                time.sleep(5)

        logger.info(
            f"🏁 Debug session completed after {self.iteration_count} iterations"
        )
        logger.info(
            "💡 If this helped identify the issue, you can now fix app.py accordingly"
        )


def main():
    """Entry point for the debug application."""
    try:
        logger.info("🐛 Starting DEBUG version of ReelsAutoPilot")
        app = DebugReelsAutoPilot()
        app.run()
    except Exception as e:
        logger.critical(f"💥 Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
