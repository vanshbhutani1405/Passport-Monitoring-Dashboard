import logging
from collections.abc import Iterable
from typing import Any

import requests

from app.core.config import Settings, get_settings


logger = logging.getLogger(__name__)

YOUTUBE_SEARCH_KEYWORDS = [
    "passport",
    "passport renewal",
    "passport seva",
    "passport application",
    "passport delay",
]


class YouTubeScraper:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def search(
        self,
        keywords: Iterable[str] = YOUTUBE_SEARCH_KEYWORDS,
        max_results_per_keyword: int = 25,
        region_code: str | None = None,
    ) -> list[dict[str, Any]]:
        if not self.settings.youtube_api_key:
            raise ValueError("YouTube API key is missing. Set YOUTUBE_API_KEY.")

        videos: list[dict[str, Any]] = []

        for keyword in keywords:
            try:
                logger.info("Searching YouTube for keyword=%s", keyword)
                video_ids = self._search_video_ids(
                    keyword=keyword,
                    max_results=max_results_per_keyword,
                    region_code=region_code,
                )
                videos.extend(self._fetch_video_details(video_ids=video_ids))
            except Exception:
                logger.exception("YouTube search failed for keyword=%s", keyword)
                raise

        return videos

    def _search_video_ids(
        self,
        keyword: str,
        max_results: int,
        region_code: str | None,
    ) -> list[str]:
        url = "https://www.googleapis.com/youtube/v3/search"
        params: dict[str, Any] = {
            "part": "id",
            "q": keyword,
            "type": "video",
            "order": "date",
            "maxResults": max_results,
            "key": self.settings.youtube_api_key,
        }
        if region_code:
            params["regionCode"] = region_code

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        video_ids: list[str] = []
        for item in data.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            if video_id:
                video_ids.append(video_id)
            else:
                logger.warning("Skipping malformed YouTube search result: %s", item)

        return video_ids

    def _fetch_video_details(self, video_ids: list[str]) -> list[dict[str, Any]]:
        if not video_ids:
            return []

        videos: list[dict[str, Any]] = []
        # Process in chunks of 50 (YouTube API limit)
        for i in range(0, len(video_ids), 50):
            chunk = video_ids[i:i+50]
            url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                "part": "snippet,statistics",
                "id": ",".join(chunk),
                "maxResults": len(chunk),
                "key": self.settings.youtube_api_key,
            }
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            videos.extend(data.get("items", []))

        return videos
