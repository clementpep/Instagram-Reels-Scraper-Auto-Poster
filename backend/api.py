# ================================================================================
# FILE: backend/api.py - Flask API for ReelsAutoPilot Dashboard
# Description: RESTful API to serve dashboard data to React frontend
# ================================================================================

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import sys
import os
import json
from typing import Dict, List, Any

# Add the src directory to Python path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from db import Session, Reel, Config
from config import config
import helpers as Helper
from logger_config import logger

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend


class DashboardAPI:
    """
    Dashboard API class to handle all dashboard-related operations.
    Provides real-time data about the ReelsAutoPilot application.
    """

    def __init__(self):
        """Initialize the Dashboard API."""
        self.session = Session()
        Helper.load_all_config()

    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive system statistics.

        Returns:
            Dict containing system performance metrics
        """
        try:
            # Database statistics
            total_reels = self.session.query(Reel).count()
            posted_reels = self.session.query(Reel).filter_by(is_posted=True).count()
            pending_reels = self.session.query(Reel).filter_by(is_posted=False).count()

            # Success rate calculation
            success_rate = (posted_reels / max(total_reels, 1)) * 100

            # Recent activity (last 24 hours)
            yesterday = datetime.now() - timedelta(days=1)
            recent_posts = (
                self.session.query(Reel)
                .filter(Reel.posted_at >= yesterday, Reel.is_posted == True)
                .count()
            )

            recent_scrapes = (
                self.session.query(Reel).filter(Reel.created_at >= yesterday).count()
            )

            return {
                "total_reels": total_reels,
                "posted_reels": posted_reels,
                "pending_reels": pending_reels,
                "success_rate": round(success_rate, 1),
                "recent_posts_24h": recent_posts,
                "recent_scrapes_24h": recent_scrapes,
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting system stats: {str(e)}")
            return {"error": str(e)}

    def get_configuration(self) -> Dict[str, Any]:
        """
        Get current application configuration.

        Returns:
            Dict containing configuration settings
        """
        try:
            return {
                "reels_scraper_enabled": getattr(config, "IS_ENABLED_REELS_SCRAPER", 0)
                == 1,
                "auto_poster_enabled": getattr(config, "IS_ENABLED_AUTO_POSTER", 0)
                == 1,
                "file_remover_enabled": getattr(config, "IS_REMOVE_FILES", 0) == 1,
                "youtube_scraper_enabled": getattr(
                    config, "IS_ENABLED_YOUTUBE_SCRAPING", 0
                )
                == 1,
                "posting_interval": getattr(config, "POSTING_INTERVAL_IN_MIN", 30),
                "scraper_interval": getattr(config, "SCRAPER_INTERVAL_IN_MIN", 720),
                "fetch_limit": getattr(config, "FETCH_LIMIT", 5),
                "accounts": getattr(config, "ACCOUNTS", []),
                "username": getattr(config, "USERNAME", ""),
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting configuration: {str(e)}")
            return {"error": str(e)}

    def get_recent_reels(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recently scraped reels.

        Args:
            limit: Maximum number of reels to return

        Returns:
            List of recent reels with metadata
        """
        try:
            reels = (
                self.session.query(Reel)
                .order_by(Reel.created_at.desc())
                .limit(limit)
                .all()
            )

            result = []
            for reel in reels:
                result.append(
                    {
                        "id": reel.id,
                        "code": reel.code,
                        "account": reel.account,
                        "caption": (
                            reel.caption[:100] + "..."
                            if len(reel.caption or "") > 100
                            else reel.caption
                        ),
                        "is_posted": reel.is_posted,
                        "created_at": (
                            reel.created_at.isoformat() if reel.created_at else None
                        ),
                        "posted_at": (
                            reel.posted_at.isoformat() if reel.posted_at else None
                        ),
                        "instagram_url": (
                            f"https://instagram.com/p/{reel.code}/"
                            if reel.code
                            else None
                        ),
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Error getting recent reels: {str(e)}")
            return []

    def get_activity_timeline(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get activity timeline for charts.

        Args:
            days: Number of days to include in timeline

        Returns:
            List of daily activity data
        """
        try:
            timeline = []
            end_date = datetime.now()

            for i in range(days):
                day_start = end_date - timedelta(days=i)
                day_end = day_start + timedelta(days=1)

                # Count posts for this day
                posts_count = (
                    self.session.query(Reel)
                    .filter(
                        Reel.posted_at >= day_start,
                        Reel.posted_at < day_end,
                        Reel.is_posted == True,
                    )
                    .count()
                )

                # Count scrapes for this day
                scrapes_count = (
                    self.session.query(Reel)
                    .filter(Reel.created_at >= day_start, Reel.created_at < day_end)
                    .count()
                )

                timeline.append(
                    {
                        "date": day_start.strftime("%Y-%m-%d"),
                        "day": day_start.strftime("%a"),
                        "posts": posts_count,
                        "scrapes": scrapes_count,
                    }
                )

            return list(reversed(timeline))  # Chronological order

        except Exception as e:
            logger.error(f"Error getting activity timeline: {str(e)}")
            return []

    def get_account_performance(self) -> List[Dict[str, Any]]:
        """
        Get performance metrics by account.

        Returns:
            List of account performance data
        """
        try:
            accounts_data = []

            # Get unique accounts from database
            accounts = self.session.query(Reel.account).distinct().all()

            for (account,) in accounts:
                if not account:
                    continue

                total = self.session.query(Reel).filter_by(account=account).count()
                posted = (
                    self.session.query(Reel)
                    .filter_by(account=account, is_posted=True)
                    .count()
                )

                success_rate = (posted / max(total, 1)) * 100

                accounts_data.append(
                    {
                        "account": account,
                        "total_reels": total,
                        "posted_reels": posted,
                        "pending_reels": total - posted,
                        "success_rate": round(success_rate, 1),
                    }
                )

            # Sort by total reels descending
            accounts_data.sort(key=lambda x: x["total_reels"], reverse=True)

            return accounts_data

        except Exception as e:
            logger.error(f"Error getting account performance: {str(e)}")
            return []


# Initialize API instance
api_instance = DashboardAPI()


# API Routes
@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "ReelsAutoPilot Dashboard API",
        }
    )


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get system statistics."""
    stats = api_instance.get_system_stats()
    return jsonify(stats)


@app.route("/api/config", methods=["GET"])
def get_config():
    """Get application configuration."""
    config_data = api_instance.get_configuration()
    return jsonify(config_data)


@app.route("/api/reels", methods=["GET"])
def get_reels():
    """Get recent reels."""
    limit = request.args.get("limit", 10, type=int)
    reels_data = api_instance.get_recent_reels(limit)
    return jsonify(reels_data)


@app.route("/api/timeline", methods=["GET"])
def get_timeline():
    """Get activity timeline."""
    days = request.args.get("days", 7, type=int)
    timeline_data = api_instance.get_activity_timeline(days)
    return jsonify(timeline_data)


@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    """Get account performance data."""
    accounts_data = api_instance.get_account_performance()
    return jsonify(accounts_data)


@app.route("/api/dashboard", methods=["GET"])
def get_dashboard_data():
    """Get complete dashboard data in one request."""
    dashboard_data = {
        "stats": api_instance.get_system_stats(),
        "config": api_instance.get_configuration(),
        "recent_reels": api_instance.get_recent_reels(5),
        "timeline": api_instance.get_activity_timeline(7),
        "accounts": api_instance.get_account_performance(),
    }
    return jsonify(dashboard_data)


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info("🚀 Starting ReelsAutoPilot Dashboard API")
    logger.info("📊 API will be available at http://localhost:5000")

    # Run in debug mode for development
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
