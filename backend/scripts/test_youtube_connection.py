import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
from app.core.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    settings = get_settings()
    api_key = settings.youtube_api_key

    if not api_key:
        print("❌ ERROR: YOUTUBE_API_KEY not set in environment variables")
        return

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": "passport",
        "maxResults": 1,
        "key": api_key,
    }

    try:
        print(f"📡 Making request to YouTube API...")
        print(f"   URL: {url}")
        print(f"   Params: part=snippet, q=passport, maxResults=1")
        response = requests.get(url, params=params, timeout=30)
        print(f"\n✅ Request completed!")
        print(f"   HTTP Status Code: {response.status_code}")
        print(f"\n📄 Response Body:")
        print(response.text)
    except requests.exceptions.Timeout as e:
        print(f"\n❌ ERROR: Request timed out")
        print(f"   Details: {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ ERROR: Connection failed")
        print(f"   Details: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: Unexpected error occurred")
        print(f"   Details: {e}")


if __name__ == "__main__":
    main()
