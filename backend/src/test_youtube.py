from backend.src.shorts import extract_channel_id, get_shorts_videos
from backend.src.config import config
import backend.src.helpers as Helper

# Charger la config
Helper.load_all_config()

# Test d'extraction d'ID de chaîne
test_url = "https://www.youtube.com/@MrBeast"
try:
    channel_id = extract_channel_id(test_url)
    print(f"✅ Channel ID extracted: {channel_id}")

    # Test de récupération des shorts
    shorts = get_shorts_videos(channel_id, config.YOUTUBE_API_KEY, 2)
    print(f"✅ Found {len(shorts)} shorts")

except Exception as e:
    print(f"❌ Error: {e}")
