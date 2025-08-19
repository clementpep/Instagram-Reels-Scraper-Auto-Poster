# ================================================================================
# FILE: poster.py (Enhanced version)
# Description: Enhanced poster with bug fixes and better error handling
# ================================================================================

import os
from instagrapi import Client
from instagrapi.types import StoryMention, StoryMedia, StoryLink, StoryHashtag
from instagrapi.exceptions import MediaNotFound, ChallengeRequired
from backend.src.db import Session, Reel
from backend.src.config import config
from backend.src.logger_config import logger
from datetime import datetime
from moviepy.editor import VideoFileClip
from typing import Optional
import backend.src.helpers as Helper


class ReelsPoster:
    """
    Handles posting of reels to Instagram with story support.
    """

    def __init__(self, api: Client):
        """
        Initialize poster with authenticated client.

        Args:
            api: Authenticated Instagram client
        """
        self.api = api
        self.session = Session()
        self.api.delay_range = [1, 3]

    def get_next_reel(self) -> Optional[Reel]:
        """
        Get the next unposted reel from database.

        Returns:
            Reel object or None if no reels available
        """
        try:
            reel = self.session.query(Reel).filter_by(is_posted=False).first()

            if reel:
                logger.info(f"Found reel to post: {reel.code} from {reel.account}")
            else:
                logger.info("No unposted reels available")

            return reel

        except Exception as e:
            logger.error(f"Error fetching next reel: {str(e)}")
            return None

    def post_reel(self, reel: Reel) -> bool:
        """
        Post a reel to Instagram.

        Args:
            reel: Reel object to post

        Returns:
            True if successful, False otherwise
        """
        try:
            # Verify file exists and is valid
            if not self._verify_file(reel.file_path):
                logger.error(f"Invalid file for reel {reel.code}")
                self._mark_as_failed(reel)
                return False

            # Prepare caption with hashtags
            caption = self._prepare_caption(reel)

            # Upload reel
            logger.info(f"Uploading reel {reel.code}")
            media = self.api.clip_upload(
                reel.file_path,
                caption,
                extra_data={
                    "like_and_view_counts_disabled": config.LIKE_AND_VIEW_COUNTS_DISABLED,
                    "disable_comments": config.DISABLE_COMMENTS,
                },
            )

            if media:
                self._mark_as_posted(reel)
                logger.info(f"Successfully posted reel {reel.code}")

                # Post to story if enabled
                if config.IS_POST_TO_STORY == 1:
                    self._post_to_story(media, reel)

                return True
            else:
                logger.error(f"Failed to upload reel {reel.code}")
                return False

        except ChallengeRequired as e:
            logger.error(f"Challenge required while posting: {e}")
            return False

        except Exception as e:
            logger.error(
                f"Error posting reel {reel.code}: {type(e).__name__}: {str(e)}"
            )
            return False

    def _verify_file(self, filepath: str, min_size: int = 10000) -> bool:
        """
        Verify that a file exists and is valid.

        Args:
            filepath: Path to file
            min_size: Minimum acceptable file size

        Returns:
            True if valid, False otherwise
        """
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return False

        if os.path.getsize(filepath) < min_size:
            logger.error(f"File too small: {filepath}")
            return False

        return True

    def _prepare_caption(self, reel: Reel) -> str:
        """
        Prepare caption with hashtags.

        Args:
            reel: Reel object

        Returns:
            Caption string
        """
        # Get hashtags from config (FIX: typo correction)
        hashtags = Helper.get_config("HASHTAGS") or config.HASHTAGS

        # Combine original caption with hashtags if needed
        if reel.caption:
            caption = f"{reel.caption}\n\n{hashtags}"
        else:
            caption = hashtags

        # Limit caption length (Instagram limit is 2200 characters)
        if len(caption) > 2200:
            caption = caption[:2197] + "..."

        return caption

    def _mark_as_posted(self, reel: Reel):
        """
        Mark a reel as posted in the database.

        Args:
            reel: Reel object
        """
        try:
            self.session.query(Reel).filter_by(code=reel.code).update(
                {"is_posted": True, "posted_at": datetime.now()}
            )
            self.session.commit()
            logger.debug(f"Marked reel {reel.code} as posted")

        except Exception as e:
            logger.error(f"Error updating reel status: {str(e)}")
            self.session.rollback()

    def _mark_as_failed(self, reel: Reel):
        """
        Mark a reel as failed (for future retry logic).

        Args:
            reel: Reel object
        """
        # For now, just log it. Could add a 'failed_attempts' column
        logger.warning(f"Marking reel {reel.code} as failed")

    def _post_to_story(self, media, reel: Reel):
        """
        Post reel to Instagram story.

        Args:
            media: Posted media object
            reel: Original reel object
        """
        try:
            logger.info(f"Posting reel {reel.code} to story")

            # Trim video if needed
            video_path = self._prepare_story_video(reel.file_path, reel.code)

            # Get required information
            username = self.api.user_info_by_username(config.USERNAME)
            hashtag = self.api.hashtag_info("reels")
            media_pk = self.api.media_pk_from_url(
                f"https://www.instagram.com/p/{reel.code}/"
            )

            # Upload to story
            self.api.video_upload_to_story(
                video_path,
                "",
                mentions=[
                    StoryMention(
                        user=username,
                        x=0.5,
                        y=0.7,
                        width=0.8,
                        height=0.125,
                    )
                ],
                links=[StoryLink(webUri=f"https://www.instagram.com/p/{reel.code}/")],
                hashtags=[
                    StoryHashtag(hashtag=hashtag, x=0.5, y=0.3, width=0.5, height=0.2)
                ],
                medias=[
                    StoryMedia(media_pk=media_pk, x=0.5, y=0.5, width=0.6, height=0.8)
                ],
            )

            logger.info(f"Successfully posted reel {reel.code} to story")

        except Exception as e:
            logger.error(f"Error posting to story: {str(e)}")

    def _prepare_story_video(
        self, filepath: str, code: str, max_duration: int = 15
    ) -> str:
        """
        Prepare video for story (trim if needed).

        Args:
            filepath: Original video path
            code: Reel code
            max_duration: Maximum duration for story

        Returns:
            Path to prepared video
        """
        try:
            clip = VideoFileClip(filepath)
            duration = clip.duration

            if duration <= max_duration:
                return filepath

            # Trim video
            output_path = os.path.join(config.DOWNLOAD_DIR, f"{code}_story.mp4")
            trimmed_clip = clip.subclip(0, max_duration)
            trimmed_clip.write_videofile(output_path, logger=None)

            logger.debug(f"Trimmed video for story: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error preparing story video: {str(e)}")
            return filepath

    def run(self):
        """
        Main execution method for posting a reel.
        """
        Helper.load_all_config()

        reel = self.get_next_reel()
        if not reel:
            return

        success = self.post_reel(reel)

        if success:
            logger.info("Posting completed successfully")
        else:
            logger.warning("Posting failed")

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

    poster = ReelsPoster(api)
    poster.run()
