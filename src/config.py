import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --------------------------------------------------------------------------------------------------#
# Global Configurations                                                                            #
# --------------------------------------------------------------------------------------------------#

# Config Variables
CURRENT_DIR = os.getcwd() + os.sep

# SQLite DB path
DB_PATH = CURRENT_DIR + ".." + os.sep + "database" + os.sep + "sqlite.db"

# Download Path
DOWNLOAD_DIR = (
    CURRENT_DIR + ".." + os.sep + "downloads" + os.sep
)  # Path of folder where files will be stored

# IS REMOVE FILES
IS_REMOVE_FILES = 1

# Remove Posted Files Interval
REMOVE_FILE_AFTER_MINS = 120  # every two hours

# --------------------------------------------------------------------------------------------------#
# Instagram Configurations                                                                         #
# --------------------------------------------------------------------------------------------------#

# IS RUN REELS SCRAPER
IS_ENABLED_REELS_SCRAPER = 1

# IS RUN AUTO POSTER
IS_ENABLED_AUTO_POSTER = 1

# IS POST STORY
IS_POST_TO_STORY = 1

# Fetch LIMIT for scraper script
FETCH_LIMIT = 5

# Posting interval in Minutes
POSTING_INTERVAL_IN_MIN = 30  # Every 15 Minutes

# Scraper interval in Minutes
SCRAPER_INTERVAL_IN_MIN = 720  # Every 12 hours

# Account List for scraping
ACCOUNTS = [
    "creustel",
    "elouen_la_baleine",
    "victorhabchy",
    # "totalgaming_official",
    # "carryminati",
    # "techno_gamerz",
    # "payalgamingg",
    # "dynamo__gaming",
]

# like_and_view_counts_disabled
LIKE_AND_VIEW_COUNTS_DISABLED = 0

# disable_comments
DISABLE_COMMENTS = 0

# HASHTAGS to add while Posting
HASHTAGS = "#reels #shorts #likes #follow #Reels-AutoPilot"

# --------------------------------------------------------------------------------------------------#
# Youtube Configurations                                                                           #
# --------------------------------------------------------------------------------------------------#

# IS RUN YOUTUBE SCRAPER
IS_ENABLED_YOUTUBE_SCRAPING = 1


# IS RUN YOUTUBE SCRAPER
YOUTUBE_SCRAPING_INTERVAL_IN_MINS = 360


# YouTube Channel List short for scraping
CHANNEL_LINKS = [
    "https://www.youtube.com/@SuprOrdinary",
    "https://www.youtube.com/@DrexLee",
    # "https://www.youtube.com/@",
]
