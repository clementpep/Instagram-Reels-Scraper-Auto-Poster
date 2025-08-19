import sys
import os
import re
import requests
from googleapiclient.discovery import build
import yt_dlp
from yt_dlp.postprocessor.common import PostProcessor
from backend.src.config import config
from backend.src.db import Session, Reel
import json
import time
import backend.src.helpers as Helper
from backend.src.helpers import print
from backend.src.logger_config import logger


# Logger class to handle yt_dlp log messages
class Logger:
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        logger.error(msg)


# Function to download shorts video using yt-dlp
def download_shorts_video(video_url: str, output_directory: str = "downloads") -> str:
    ydl_opts = {
        "outtmpl": os.path.join(output_directory, "%(title)s-%(id)s.%(ext)s"),
        "format": "best[height<=1080]",
        "logger": Logger(),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.add_default_info_extractors()
        info_dict = ydl.extract_info(video_url, download=False)
        output_filename = ydl.prepare_filename(info_dict)
        ydl.process_info(info_dict)
        return output_filename


# Function to extract channel ID from the given channel link
def extract_channel_id(channel_link: str) -> str:
    """
    Extract channel ID from various YouTube URL formats.

    Args:
        channel_link: YouTube channel URL

    Returns:
        Channel ID string

    Raises:
        ValueError: If unable to extract channel ID
    """
    logger.info(f"Extracting channel ID from: {channel_link}")

    # Pattern 1: Direct channel ID format
    # https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw
    channel_id_pattern = r"(?:youtube\.com/channel/)([^/?&]+)"
    match = re.search(channel_id_pattern, channel_link)
    if match:
        channel_id = match.group(1)
        logger.info(f"Found channel ID via pattern: {channel_id}")
        return channel_id

    # Pattern 2: Username format with @
    # https://www.youtube.com/@MrBeast
    username_pattern = r"youtube\.com/@([^/?&]+)"
    match = re.search(username_pattern, channel_link)
    if match:
        username = match.group(1)
        logger.info(f"Found username: @{username}, resolving to channel ID...")

        # Use YouTube API to resolve username to channel ID
        try:
            youtube = build("youtube", "v3", developerKey=config.YOUTUBE_API_KEY)

            # Search for the channel by username
            search_response = (
                youtube.search()
                .list(q=username, type="channel", part="id,snippet", maxResults=1)
                .execute()
            )

            if search_response["items"]:
                channel_id = search_response["items"][0]["id"]["channelId"]
                logger.info(f"Resolved @{username} to channel ID: {channel_id}")
                return channel_id
            else:
                logger.warning(f"No channel found for username: @{username}")

        except Exception as e:
            logger.error(f"Error resolving username via API: {str(e)}")

    # Pattern 3: Old username format
    # https://www.youtube.com/user/username or https://www.youtube.com/c/username
    user_pattern = r"youtube\.com/(?:user|c)/([^/?&]+)"
    match = re.search(user_pattern, channel_link)
    if match:
        username = match.group(1)
        logger.info(f"Found old format username: {username}")

    # Fallback: Try to scrape the page
    try:
        logger.info("Attempting to scrape channel ID from page...")
        response = requests.get(channel_link, timeout=10)
        if response.status_code == 200:
            # Look for various patterns in the page content
            patterns = [
                r'"channelId":"([^"]+)"',
                r'<meta itemprop="channelId" content="([^"]+)">',
                r'"externalId":"([^"]+)"',
                r'channel_id=([^&"]+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, response.text)
                if match:
                    channel_id = match.group(1)
                    logger.info(f"Extracted channel ID from page: {channel_id}")
                    return channel_id

        else:
            logger.error(f"Failed to fetch channel page: HTTP {response.status_code}")

    except Exception as e:
        logger.error(f"Error scraping channel page: {str(e)}")

    # If all methods fail
    raise ValueError(f"Unable to extract channel ID from channel link: {channel_link}")


# Function to get shorts videos from a YouTube channel using YouTube API
def get_shorts_videos(channel_id: str, api_key: str, max_results: int = 50):
    """
    Get shorts videos from a YouTube channel.

    Args:
        channel_id: YouTube channel ID
        api_key: YouTube Data API key
        max_results: Maximum number of videos to fetch

    Returns:
        List of shorts video information
    """
    logger.info(f"Fetching shorts for channel ID: {channel_id}")

    youtube = build("youtube", "v3", developerKey=api_key)

    try:
        # Get channel details
        channel_response = (
            youtube.channels().list(part="contentDetails", id=channel_id).execute()
        )

        if not channel_response["items"]:
            logger.error(f"No channel found for ID: {channel_id}")
            return []

        uploads_playlist_id = channel_response["items"][0]["contentDetails"][
            "relatedPlaylists"
        ]["uploads"]

        logger.info(f"Found uploads playlist: {uploads_playlist_id}")

        shorts_videos = []
        next_page_token = None
        processed_videos = 0

        while processed_videos < max_results:
            try:
                playlist_items_request = youtube.playlistItems().list(
                    part="snippet",
                    maxResults=min(50, max_results - processed_videos),
                    playlistId=uploads_playlist_id,
                    pageToken=next_page_token,
                )

                playlist_items = playlist_items_request.execute()

                if not playlist_items["items"]:
                    logger.info("No more videos found")
                    break

                for item in playlist_items["items"]:
                    video_id = item["snippet"]["resourceId"]["videoId"]
                    video_title = item["snippet"]["title"]
                    video_description = item["snippet"]["description"]

                    processed_videos += 1

                    # Check if it's a short (multiple criteria)
                    is_short = (
                        "#shorts" in video_title.lower()
                        or "#shorts" in video_description.lower()
                        or "#short" in video_title.lower()
                        or "#short" in video_description.lower()
                        or any(
                            keyword in video_title.lower()
                            for keyword in ["shorts", "short"]
                        )
                    )

                    if is_short:
                        shorts_videos.append(
                            {
                                "id": video_id,
                                "title": video_title,
                                "description": video_description,
                                "url": f"https://www.youtube.com/watch?v={video_id}",
                            }
                        )
                        logger.debug(f"Found short: {video_title}")

                next_page_token = playlist_items.get("nextPageToken")
                if not next_page_token:
                    break

            except Exception as e:
                logger.error(f"Error fetching playlist items: {str(e)}")
                break

        logger.info(f"Found {len(shorts_videos)} shorts videos")
        return shorts_videos

    except Exception as e:
        logger.error(f"Error fetching channel details: {str(e)}")
        return []


# Main function to process each channel and download shorts videos
def main():
    """
    Main function to scrape YouTube shorts from configured channels.
    """
    Helper.load_all_config()

    if not config.YOUTUBE_API_KEY:
        logger.error("YouTube API key not configured")
        return

    if not config.CHANNEL_LINKS:
        logger.error("No YouTube channels configured")
        return

    api_key = config.YOUTUBE_API_KEY
    output_directory = config.DOWNLOAD_DIR
    session = Session()

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        logger.info(f"Created download directory: {output_directory}")

    total_downloaded = 0
    failed_channels = []

    for channel_link in config.CHANNEL_LINKS:
        try:
            logger.info(f"Processing channel: {channel_link}")

            # Extract channel ID
            channel_id = extract_channel_id(channel_link)
            logger.info(f"Channel ID: {channel_id}")

            # Get shorts videos
            shorts = get_shorts_videos(channel_id, api_key, config.FETCH_LIMIT)

            downloaded_count = 0

            for short_video in shorts:
                try:
                    # Check if already exists in database
                    exists = (
                        session.query(Reel).filter_by(code=short_video["id"]).first()
                    )
                    if exists:
                        logger.debug(f"Short already exists: {short_video['id']}")
                        continue

                    logger.info(
                        f"Downloading: {short_video['title']} ({short_video['url']})"
                    )

                    # Download the video
                    downloaded_file = download_shorts_video(
                        short_video["url"], output_directory
                    )

                    # Verify download
                    if (
                        not os.path.exists(downloaded_file)
                        or os.path.getsize(downloaded_file) < 1000
                    ):
                        logger.warning(
                            f"Download failed or file too small: {downloaded_file}"
                        )
                        continue

                    logger.info(f"Downloaded to: {downloaded_file}")

                    # Save to database
                    reel_db = Reel(
                        post_id=short_video["id"],
                        code=short_video["id"],
                        account=channel_id,
                        caption=short_video["title"][:500],  # Limit caption length
                        file_name=os.path.basename(downloaded_file),
                        file_path=downloaded_file,
                        data=json.dumps(short_video),
                        is_posted=False,
                    )
                    session.add(reel_db)
                    session.commit()

                    downloaded_count += 1
                    total_downloaded += 1
                    logger.info(f"Successfully processed short: {short_video['id']}")

                except Exception as e:
                    logger.error(
                        f"Error processing short {short_video.get('id', 'unknown')}: {str(e)}"
                    )
                    session.rollback()
                    continue

            logger.info(
                f"Downloaded {downloaded_count} new shorts from channel {channel_id}"
            )

        except Exception as e:
            logger.error(f"Failed to process channel {channel_link}: {str(e)}")
            failed_channels.append(channel_link)
            continue

    logger.info(f"YouTube scraping complete. Downloaded {total_downloaded} new shorts")

    if failed_channels:
        logger.warning(f"Failed channels: {', '.join(failed_channels)}")

    session.close()


if __name__ == "__main__":
    main()
