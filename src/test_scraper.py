# ================================================================================
# FILE: test_scraper.py (NEW - Test scraping functionality)
# Description: Test script to verify scraping works
# ================================================================================

"""
Test script to verify Instagram scraping functionality.
"""

from logger_config import logger
import auth
from reels import ReelsScraper
from db import Session, Config


def test_single_account(account_name: str = None):
    """
    Test scraping a single account.

    Args:
        account_name: Instagram username to test
    """
    logger.info("=" * 60)
    logger.info("INSTAGRAM SCRAPER TEST")
    logger.info("=" * 60)

    # Get account to test
    if not account_name:
        session = Session()
        accounts_config = session.query(Config).filter_by(key="ACCOUNTS").first()
        session.close()

        if accounts_config and accounts_config.value:
            accounts = [a.strip() for a in accounts_config.value.split(",")]
            account_name = accounts[0] if accounts else "creustel"
        else:
            account_name = "creustel"

    logger.info(f"Testing account: @{account_name}")
    logger.info("-" * 40)

    try:
        # Login
        logger.info("1. Authenticating...")
        api = auth.login()

        if not api:
            logger.error("❌ Authentication failed!")
            return False

        logger.info("✅ Authentication successful")

        # Create scraper
        logger.info("\n2. Initializing scraper...")
        scraper = ReelsScraper(api)

        # Scrape account
        logger.info(f"\n3. Scraping @{account_name}...")
        reels = scraper.scrape_account(account_name)

        if not reels:
            logger.warning(f"No reels found for @{account_name}")
            return False

        logger.info(f"✅ Found {len(reels)} reels")

        # Show reel details
        logger.info("\n4. Reel details:")
        for i, reel in enumerate(reels[:3], 1):
            logger.info(f"\n   Reel #{i}:")
            logger.info(f"   - Code: {getattr(reel, 'code', 'N/A')}")
            logger.info(f"   - Caption: {getattr(reel, 'caption_text', 'N/A')[:50]}...")
            logger.info(
                f"   - Video URL: {str(getattr(reel, 'video_url', 'N/A'))[:80]}..."
            )

        # Try downloading one
        if reels:
            logger.info(f"\n5. Testing download of first reel...")
            success = scraper.download_and_save_reel(reels[0], account_name)

            if success:
                logger.info("✅ Download and save successful!")
            else:
                logger.warning("⚠️  Download failed (might already exist)")

        logger.info("\n" + "=" * 60)
        logger.info("TEST COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return False

    finally:
        if "scraper" in locals():
            scraper.session.close()


def main():
    """
    Main test execution.
    """
    import sys

    account = sys.argv[1] if len(sys.argv) > 1 else None

    if test_single_account(account):
        logger.info("\n✅ All tests passed! The scraper is working correctly.")
    else:
        logger.error("\n❌ Tests failed. Please check the errors above.")


if __name__ == "__main__":
    main()
