# ================================================================================
# FILE: check_db.py (NEW - Database inspection tool)
# Description: Tool to inspect and fix database issues
# ================================================================================

"""
Database inspection and repair tool.
Use this to check the current state of your database.
"""

from backend.src.db import Session, Config, Reel
from backend.src.logger_config import logger
from datetime import datetime
import json


def check_database():
    """
    Check database status and content.
    """
    session = Session()
    try:
        logger.info("=" * 60)
        logger.info("DATABASE INSPECTION REPORT")
        logger.info("=" * 60)

        # Check configurations
        logger.info("\n📋 CONFIGURATION TABLE:")
        logger.info("-" * 40)

        configs = session.query(Config).all()
        if configs:
            for config in configs:
                value = (
                    config.value[:50] + "..."
                    if len(config.value or "") > 50
                    else config.value
                )
                if config.key == "PASSWORD":
                    value = "***hidden***" if config.value else "NOT SET"
                logger.info(f"  {config.key}: {value}")
        else:
            logger.warning("  No configurations found!")

        # Check reels
        logger.info("\n📹 REELS TABLE:")
        logger.info("-" * 40)

        total_reels = session.query(Reel).count()
        posted_reels = session.query(Reel).filter_by(is_posted=True).count()
        pending_reels = session.query(Reel).filter_by(is_posted=False).count()

        logger.info(f"  Total reels: {total_reels}")
        logger.info(f"  Posted: {posted_reels}")
        logger.info(f"  Pending: {pending_reels}")

        # Show latest reels
        latest_reels = session.query(Reel).order_by(Reel.id.desc()).limit(5).all()
        if latest_reels:
            logger.info("\n  Latest 5 reels:")
            for reel in latest_reels:
                status = "✅ Posted" if reel.is_posted else "⏳ Pending"
                logger.info(f"    - {reel.code} from @{reel.account} [{status}]")

        # Check for issues
        logger.info("\n🔍 CHECKING FOR ISSUES:")
        logger.info("-" * 40)

        # Check for reels with missing files
        issues_found = False

        import os

        missing_files = []
        for reel in session.query(Reel).filter_by(is_posted=False).all():
            if not os.path.exists(reel.file_path):
                missing_files.append(reel.code)
                issues_found = True

        if missing_files:
            logger.warning(f"  ⚠️  {len(missing_files)} reels with missing files:")
            for code in missing_files[:5]:
                logger.warning(f"     - {code}")

        # Check for corrupted JSON data
        corrupted_json = []
        for reel in session.query(Reel).limit(10).all():
            try:
                if reel.data:
                    json.loads(reel.data)
            except:
                corrupted_json.append(reel.code)
                issues_found = True

        if corrupted_json:
            logger.warning(f"  ⚠️  {len(corrupted_json)} reels with corrupted JSON data")

        if not issues_found:
            logger.info("  ✅ No issues found!")

        logger.info("\n" + "=" * 60)

    except Exception as e:
        logger.error(f"Error checking database: {str(e)}")
    finally:
        session.close()


def fix_missing_configs():
    """
    Add any missing configuration entries.
    """
    from init_config import initialize_configuration

    initialize_configuration()


def clean_failed_reels():
    """
    Clean up reels that failed to download properly.
    """
    session = Session()
    try:
        import os

        # Find reels with missing files
        deleted_count = 0
        for reel in session.query(Reel).filter_by(is_posted=False).all():
            if not os.path.exists(reel.file_path):
                session.delete(reel)
                deleted_count += 1
                logger.info(f"Removed reel {reel.code} (missing file)")

        if deleted_count > 0:
            session.commit()
            logger.info(f"✅ Cleaned {deleted_count} failed reels")
        else:
            logger.info("No failed reels to clean")

    except Exception as e:
        logger.error(f"Error cleaning reels: {str(e)}")
        session.rollback()
    finally:
        session.close()


def main():
    """
    Main execution.
    """
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--fix":
            logger.info("Fixing missing configurations...")
            fix_missing_configs()
        elif sys.argv[1] == "--clean":
            logger.info("Cleaning failed reels...")
            clean_failed_reels()
        else:
            logger.info("Usage: python check_db.py [--fix|--clean]")
    else:
        check_database()


if __name__ == "__main__":
    main()
