# ================================================================================
# FILE: monitoring.py (NEW)
# Description: Application monitoring and health checks
# ================================================================================

import os
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List
from config import config
from logger_config import logger
from db import Session, Reel


class ApplicationMonitor:
    """
    Monitors application health and performance metrics.
    """

    def __init__(self):
        """Initialize monitoring system."""
        self.metrics = {
            "total_reels_scraped": 0,
            "total_reels_posted": 0,
            "failed_posts": 0,
            "disk_usage": 0,
            "memory_usage": 0,
            "cpu_usage": 0,
            "last_successful_scrape": None,
            "last_successful_post": None,
            "uptime_start": datetime.now(),
        }

        self.alerts = []
        self.monitoring_thread = None
        self.is_running = False

    def start(self):
        """Start monitoring in a separate thread."""
        self.is_running = True
        self.monitoring_thread = threading.Thread(target=self._monitor_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        logger.info("Monitoring system started")

    def stop(self):
        """Stop monitoring."""
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        logger.info("Monitoring system stopped")

    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.is_running:
            try:
                self._update_metrics()
                self._check_alerts()
                threading.Event().wait(60)  # Check every minute
            except Exception as e:
                logger.error(f"Monitoring error: {str(e)}")

    def _update_metrics(self):
        """Update system and application metrics."""
        # System metrics
        self.metrics["cpu_usage"] = psutil.cpu_percent(interval=1)
        self.metrics["memory_usage"] = psutil.virtual_memory().percent

        # Disk usage for download directory
        if os.path.exists(config.DOWNLOAD_DIR):
            disk_stats = psutil.disk_usage(config.DOWNLOAD_DIR)
            self.metrics["disk_usage"] = disk_stats.percent

        # Database metrics
        session = Session()
        try:
            self.metrics["total_reels_scraped"] = session.query(Reel).count()
            self.metrics["total_reels_posted"] = (
                session.query(Reel).filter_by(is_posted=True).count()
            )

            # Get last successful operations
            last_posted = (
                session.query(Reel)
                .filter_by(is_posted=True)
                .order_by(Reel.posted_at.desc())
                .first()
            )

            if last_posted:
                self.metrics["last_successful_post"] = last_posted.posted_at

        finally:
            session.close()

    def _check_alerts(self):
        """Check for alert conditions."""
        alerts = []

        # High disk usage
        if self.metrics["disk_usage"] > 90:
            alerts.append(f"CRITICAL: Disk usage at {self.metrics['disk_usage']}%")

        # High memory usage
        if self.metrics["memory_usage"] > 85:
            alerts.append(f"WARNING: Memory usage at {self.metrics['memory_usage']}%")

        # No recent posts
        if self.metrics["last_successful_post"]:
            hours_since_last_post = (
                datetime.now() - self.metrics["last_successful_post"]
            ).total_seconds() / 3600
            if hours_since_last_post > 24:
                alerts.append(
                    f"WARNING: No posts in the last {hours_since_last_post:.1f} hours"
                )

        # Log new alerts
        for alert in alerts:
            if alert not in self.alerts:
                logger.warning(alert)
                self.alerts.append(alert)

    def get_status_report(self) -> Dict:
        """
        Get a comprehensive status report.

        Returns:
            Dictionary containing status information
        """
        uptime = datetime.now() - self.metrics["uptime_start"]

        return {
            "uptime": str(uptime),
            "system": {
                "cpu_usage": f"{self.metrics['cpu_usage']}%",
                "memory_usage": f"{self.metrics['memory_usage']}%",
                "disk_usage": f"{self.metrics['disk_usage']}%",
            },
            "application": {
                "total_scraped": self.metrics["total_reels_scraped"],
                "total_posted": self.metrics["total_reels_posted"],
                "success_rate": f"{(self.metrics['total_reels_posted'] / max(self.metrics['total_reels_scraped'], 1)) * 100:.1f}%",
                "last_post": (
                    self.metrics["last_successful_post"].strftime("%Y-%m-%d %H:%M:%S")
                    if self.metrics["last_successful_post"]
                    else "Never"
                ),
            },
            "alerts": self.alerts[-5:] if self.alerts else [],
        }


# Global monitor instance
monitor = ApplicationMonitor()
