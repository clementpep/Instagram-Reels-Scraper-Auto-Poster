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
    Main application orchestrator with enhanced visibility and scheduling.
    """

    def __init__(self, dev_mode: bool = False):
        """
        Initialize the application with configuration and scheduling.

        Args:
            dev_mode: If True, runs with shorter intervals for testing
        """
        self.api: Optional[Client] = None
        self.is_running = True
        self.dev_mode = dev_mode

        # Load configuration
        Helper.load_all_config()

        # Set intervals based on mode
        if dev_mode:
            logger.info("🔧 DEV MODE: Using shorter intervals")
            self.scraper_interval = 5  # 5 minutes instead of 12 hours
            self.poster_interval = 2  # 2 minutes instead of 30 minutes
            self.remover_interval = 10  # 10 minutes instead of 2 hours
            self.youtube_interval = 15  # 15 minutes instead of 6 hours
        else:
            self.scraper_interval = int(getattr(config, "SCRAPER_INTERVAL_IN_MIN", 720))
            self.poster_interval = int(getattr(config, "POSTING_INTERVAL_IN_MIN", 30))
            self.remover_interval = int(getattr(config, "REMOVE_FILE_AFTER_MINS", 120))
            self.youtube_interval = int(
                getattr(config, "YOUTUBE_SCRAPING_INTERVAL_IN_MINS", 360)
            )

        # Initialize schedulers with staggered start times
        current_time = datetime.now()
        self.next_reels_scraper_run = current_time
        self.next_poster_run = current_time + timedelta(minutes=1)
        self.next_remover_run = current_time + timedelta(minutes=2)
        self.next_youtube_run = current_time + timedelta(minutes=3)

        # Status tracking
        self.last_status_print = datetime.now()
        self.status_interval = 300 if not dev_mode else 60  # 5 min normal, 1 min dev
        self.last_activity = "Application started"

        # Error tracking
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5

        logger.info("ReelsAutoPilot initialized")
        self._log_initial_status()

    def _log_initial_status(self):
        """Log initial configuration and schedule."""
        mode = "🔧 DEVELOPMENT" if self.dev_mode else "🚀 PRODUCTION"
        logger.info(f"Running in {mode} mode")

        logger.info("📊 Configuration:")
        logger.info(
            f"   - Reels scraper: {'✅ ON' if self._is_enabled('IS_ENABLED_REELS_SCRAPER') else '❌ OFF'} (every {self.scraper_interval} min)"
        )
        logger.info(
            f"   - Auto poster: {'✅ ON' if self._is_enabled('IS_ENABLED_AUTO_POSTER') else '❌ OFF'} (every {self.poster_interval} min)"
        )
        logger.info(
            f"   - File remover: {'✅ ON' if self._is_enabled('IS_REMOVE_FILES') else '❌ OFF'} (every {self.remover_interval} min)"
        )
        logger.info(
            f"   - YouTube scraper: {'✅ ON' if self._is_enabled('IS_ENABLED_YOUTUBE_SCRAPING') else '❌ OFF'} (every {self.youtube_interval} min)"
        )

        logger.info("📅 Next execution times:")
        logger.info(
            f"   - Reels scraper: {self.next_reels_scraper_run.strftime('%H:%M:%S')}"
        )
        logger.info(f"   - Auto poster: {self.next_poster_run.strftime('%H:%M:%S')}")
        logger.info(f"   - File remover: {self.next_remover_run.strftime('%H:%M:%S')}")
        logger.info(
            f"   - YouTube scraper: {self.next_youtube_run.strftime('%H:%M:%S')}"
        )

    def _is_enabled(self, config_key: str) -> bool:
        """Safely check if a configuration is enabled."""
        value = getattr(config, config_key, 0)

        if isinstance(value, str):
            return value.strip() == "1"
        elif isinstance(value, int):
            return value == 1
        else:
            return False

    def initialize_instagram(self) -> bool:
        """Initialize Instagram client if needed."""
        if self._is_enabled("IS_ENABLED_REELS_SCRAPER") or self._is_enabled(
            "IS_ENABLED_AUTO_POSTER"
        ):
            if not self.api:
                logger.info("🔑 Initializing Instagram client...")
                self.api = auth.login()

                if not self.api:
                    logger.critical("❌ Failed to initialize Instagram client")
                    return False

                logger.info("✅ Instagram client ready")

        return True

    def run_reels_scraper(self):
        """Execute reels scraping task."""
        try:
            logger.info("🎬 === REELS SCRAPER STARTING ===")
            self.last_activity = "Scraping reels"

            if not self.api:
                logger.error("❌ Instagram client not initialized")
                return

            reels.main(self.api)

            # Schedule next run
            self.next_reels_scraper_run = datetime.now() + timedelta(
                minutes=self.scraper_interval
            )
            logger.info(
                f"📅 Next scraping: {self.next_reels_scraper_run.strftime('%H:%M:%S')}"
            )
            self.consecutive_errors = 0

        except Exception as e:
            logger.error(f"❌ Reels scraper failed: {str(e)}", exc_info=True)
            self.handle_error()

    def run_poster(self):
        """Execute posting task."""
        try:
            logger.info("📤 === AUTO POSTER STARTING ===")
            self.last_activity = "Posting reel"

            if not self.api:
                logger.error("❌ Instagram client not initialized")
                return

            poster.main(self.api)

            # Schedule next run with random delay
            random_delay = random.randint(5, 20)
            self.next_poster_run = datetime.now() + timedelta(
                minutes=self.poster_interval, seconds=random_delay
            )
            logger.info(f"📅 Next posting: {self.next_poster_run.strftime('%H:%M:%S')}")
            self.consecutive_errors = 0

        except Exception as e:
            logger.error(f"❌ Poster failed: {str(e)}", exc_info=True)
            self.handle_error()

    def run_remover(self):
        """Execute file removal task."""
        try:
            logger.info("🗑️ === FILE REMOVER STARTING ===")
            self.last_activity = "Removing files"

            remover.main()

            # Schedule next run
            self.next_remover_run = datetime.now() + timedelta(
                minutes=self.remover_interval
            )
            logger.info(
                f"📅 Next cleanup: {self.next_remover_run.strftime('%H:%M:%S')}"
            )

        except Exception as e:
            logger.error(f"❌ Remover failed: {str(e)}")

    def run_youtube_scraper(self):
        """Execute YouTube scraping task."""
        try:
            logger.info("🎥 === YOUTUBE SCRAPER STARTING ===")
            self.last_activity = "Scraping YouTube"

            shorts.main()

            # Schedule next run
            self.next_youtube_run = datetime.now() + timedelta(
                minutes=self.youtube_interval
            )
            logger.info(
                f"📅 Next YouTube scraping: {self.next_youtube_run.strftime('%H:%M:%S')}"
            )

        except Exception as e:
            logger.error(f"❌ YouTube scraper failed: {str(e)}")

    def handle_error(self):
        """Handle consecutive errors."""
        self.consecutive_errors += 1

        if self.consecutive_errors >= self.max_consecutive_errors:
            logger.critical(
                f"🚨 Too many consecutive errors ({self.consecutive_errors}). Reinitializing..."
            )
            self.api = None
            self.initialize_instagram()
            self.consecutive_errors = 0
            time.sleep(60)

    def print_heartbeat(self):
        """Print regular heartbeat to show the app is alive."""
        current_time = datetime.now()

        logger.info("💓 === HEARTBEAT ===")
        logger.info(f"   ⏰ Current time: {current_time.strftime('%H:%M:%S')}")
        logger.info(f"   🎯 Last activity: {self.last_activity}")
        logger.info(f"   📊 Consecutive errors: {self.consecutive_errors}")

        # Show countdown to next tasks
        tasks = [
            (
                "🎬 Scraper",
                self.next_reels_scraper_run,
                self._is_enabled("IS_ENABLED_REELS_SCRAPER"),
            ),
            (
                "📤 Poster",
                self.next_poster_run,
                self._is_enabled("IS_ENABLED_AUTO_POSTER"),
            ),
            ("🗑️ Remover", self.next_remover_run, self._is_enabled("IS_REMOVE_FILES")),
            (
                "🎥 YouTube",
                self.next_youtube_run,
                self._is_enabled("IS_ENABLED_YOUTUBE_SCRAPING"),
            ),
        ]

        logger.info("   📅 Next tasks:")
        for name, next_time, enabled in tasks:
            if enabled:
                diff = next_time - current_time
                if diff.total_seconds() > 0:
                    minutes = int(diff.total_seconds() // 60)
                    seconds = int(diff.total_seconds() % 60)
                    logger.info(
                        f"      {name}: {next_time.strftime('%H:%M:%S')} (in {minutes}m {seconds}s)"
                    )
                else:
                    logger.info(f"      {name}: Ready to run!")

        logger.info("================")

    def run(self):
        """Main application loop."""
        logger.info("🚀 Starting ReelsAutoPilot main loop")

        # Initialize Instagram if needed
        if not self.initialize_instagram():
            logger.critical("💥 Failed to start application")
            return

        if self.dev_mode:
            logger.info("🔧 Development mode: Will show regular heartbeats")
        else:
            logger.info("🔄 Production mode: Entering background operation")
            logger.info("💡 Tip: Press Ctrl+C to stop gracefully")

        loop_count = 0

        # Main loop
        while self.is_running:
            try:
                loop_count += 1
                current_time = datetime.now()

                # Check and run scheduled tasks
                tasks_executed = 0

                if (
                    self._is_enabled("IS_ENABLED_REELS_SCRAPER")
                    and current_time >= self.next_reels_scraper_run
                ):
                    self.run_reels_scraper()
                    tasks_executed += 1

                if (
                    self._is_enabled("IS_ENABLED_AUTO_POSTER")
                    and current_time >= self.next_poster_run
                ):
                    self.run_poster()
                    tasks_executed += 1

                if (
                    self._is_enabled("IS_REMOVE_FILES")
                    and current_time >= self.next_remover_run
                ):
                    self.run_remover()
                    tasks_executed += 1

                if (
                    self._is_enabled("IS_ENABLED_YOUTUBE_SCRAPING")
                    and current_time >= self.next_youtube_run
                ):
                    self.run_youtube_scraper()
                    tasks_executed += 1

                # Print status periodically
                if (
                    current_time - self.last_status_print
                ).total_seconds() >= self.status_interval:
                    if tasks_executed == 0:
                        self.last_activity = "Waiting for next scheduled task"
                    self.print_heartbeat()
                    self.last_status_print = current_time

                # Sleep to avoid high CPU usage
                time.sleep(1)

            except KeyboardInterrupt:
                logger.info("🛑 Graceful shutdown requested...")
                self.is_running = False

            except Exception as e:
                logger.error(
                    f"💥 Unexpected error in main loop: {str(e)}", exc_info=True
                )
                self.handle_error()
                time.sleep(5)

        logger.info("🏁 ReelsAutoPilot stopped gracefully")


def main():
    """Entry point for the application."""
    try:
        # Check for dev mode
        dev_mode = "--dev" in sys.argv or "-d" in sys.argv

        if dev_mode:
            logger.info("🔧 Starting in DEVELOPMENT mode (shorter intervals)")

        app = ReelsAutoPilot(dev_mode=dev_mode)
        app.run()

    except Exception as e:
        logger.critical(f"💥 Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
