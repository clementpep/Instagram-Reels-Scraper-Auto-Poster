# ================================================================================
# FILE: auth.py (Enhanced version)
# Description: Enhanced authentication module with better error handling
# ================================================================================

from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired, TwoFactorRequired
from typing import Optional
import os
import json
from config import config
from logger_config import logger
import helpers as Helper

SESSION_FILE = "session.json"
MAX_LOGIN_ATTEMPTS = 3


class InstagramAuthenticator:
    """
    Handles Instagram authentication with session management and error recovery.
    """

    def __init__(self, username: str, password: str):
        """
        Initialize authenticator with credentials.

        Args:
            username: Instagram username
            password: Instagram password
        """
        self.username = username
        self.password = password
        self.api = None
        self.session_file = SESSION_FILE

    def login(self) -> Optional[Client]:
        """
        Perform login with session management and error handling.

        Returns:
            Authenticated Client instance or None if login fails
        """
        logger.info(f"Starting Instagram authentication for user: {self.username}")

        for attempt in range(MAX_LOGIN_ATTEMPTS):
            try:
                self.api = Client()
                self.api.delay_range = [1, 3]

                # Try to load existing session
                if os.path.exists(self.session_file) and attempt == 0:
                    if self._login_with_session():
                        return self.api
                    else:
                        logger.warning("Session login failed, trying username/password")
                        os.remove(self.session_file)

                # Login with username and password
                if self._login_with_credentials():
                    return self.api

            except ChallengeRequired as e:
                logger.error(f"Challenge required: {e}")
                logger.info("Please complete the challenge in your Instagram app")
                # Implement challenge handling if needed

            except TwoFactorRequired as e:
                logger.error(f"Two-factor authentication required: {e}")
                # Implement 2FA handling if needed
                code = input("Enter 2FA code: ")
                if self._handle_two_factor(code):
                    return self.api

            except Exception as e:
                logger.error(f"Login attempt {attempt + 1} failed: {str(e)}")

        logger.critical("All login attempts failed")
        return None

    def _login_with_session(self) -> bool:
        """
        Attempt to login using saved session.

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Attempting login with saved session")
            self.api.load_settings(self.session_file)
            self.api.login(self.username, self.password)

            # Verify session is valid
            self.api.get_timeline_feed()
            self._save_session()
            logger.info("Successfully logged in with saved session")
            return True

        except Exception as e:
            logger.warning(f"Session login failed: {str(e)}")
            return False

    def _login_with_credentials(self) -> bool:
        """
        Login using username and password.

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Attempting login with username and password")
            self.api.login(self.username, self.password)

            # Verify login
            self.api.get_timeline_feed()
            self._save_session()
            logger.info("Successfully logged in with credentials")
            return True

        except Exception as e:
            logger.error(f"Credential login failed: {str(e)}")
            return False

    def _handle_two_factor(self, code: str) -> bool:
        """
        Handle two-factor authentication.

        Args:
            code: 2FA code

        Returns:
            True if successful, False otherwise
        """
        try:
            self.api.two_factor_login(code)
            self._save_session()
            logger.info("Successfully completed 2FA")
            return True
        except Exception as e:
            logger.error(f"2FA failed: {str(e)}")
            return False

    def _save_session(self):
        """Save session to file."""
        try:
            self.api.dump_settings(self.session_file)
            logger.debug("Session saved successfully")
        except Exception as e:
            logger.warning(f"Failed to save session: {str(e)}")


def login() -> Optional[Client]:
    """
    Legacy login function for backward compatibility.

    Returns:
        Authenticated Client instance or None
    """
    Helper.load_all_config()

    if not config.USERNAME or not config.PASSWORD:
        logger.error("Username or password not configured")
        return None

    authenticator = InstagramAuthenticator(config.USERNAME, config.PASSWORD)
    return authenticator.login()
