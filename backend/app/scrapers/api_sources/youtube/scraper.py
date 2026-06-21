import logging
from collections.abc import Iterable
from typing import Any

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
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client

        if not self.settings.youtube_api_key:
            raise ValueError("YouTube API key is missing. Set YOUTUBE_API_KEY.")

        try:
            from googleapiclient.discovery import build
            from googleapiclient.errors import HttpError
        except ImportError as exc:
            raise RuntimeError(
                "google-api-python-client is required for YouTube ingestion."
            ) from exc

        self._http_error_cls = HttpError
        import httplib2
        http = httplib2.Http(timeout=30)
        self._client = build(
            "youtube",
            "v3",
            developerKey=self.settings.youtube_api_key,
            cache_discovery=False,
            http=http,
        )
        return self._client

    def search(
        self,
        keywords: Iterable[str] = YOUTUBE_SEARCH_KEYWORDS,
        max_results_per_keyword: int = 25,
        region_code: str | None = None,
    ) -> list[dict[str, Any]]:
        client = self._get_client()
        videos: list[dict[str, Any]] = []

        for keyword in keywords:
            try:
                logger.info("Searching YouTube for keyword=%s", keyword)
                video_ids = self._search_video_ids(
                    client=client,
                    keyword=keyword,
                    max_results=max_results_per_keyword,
                    region_code=region_code,
                )
                videos.extend(self._fetch_video_details(client=client, video_ids=video_ids))
            except self._http_error_cls as exc:
                logger.exception("YouTube API request failed for keyword=%s", keyword)
                raise RuntimeError(f"YouTube API request failed for keyword '{keyword}': {exc}") from exc
            except Exception:
                logger.exception("YouTube search failed for keyword=%s", keyword)
                raise

        return videos

    @staticmethod
    def _search_video_ids(
        client: Any,
        keyword: str,
        max_results: int,
        region_code: str | None,
    ) -> list[str]:
        request_params: dict[str, Any] = {
            "part": "id",
            "q": keyword,
            "type": "video",
            "order": "date",
            "maxResults": max_results,
        }
        if region_code:
            request_params["regionCode"] = region_code

        response = client.search().list(**request_params).execute()
        items = response.get("items", [])
        video_ids: list[str] = []

        for item in items:
            video_id = item.get("id", {}).get("videoId")
            if video_id:
                video_ids.append(video_id)
            else:
                logger.warning("Skipping malformed YouTube search result: %s", item)

        return video_ids

    @staticmethod
    def _fetch_video_details(client: Any, video_ids: list[str]) -> list[dict[str, Any]]:
        if not video_ids:
            return []

        videos: list[dict[str, Any]] = []
        for start in range(0, len(video_ids), 50):
            chunk = video_ids[start : start + 50]
            response = (
                client.videos()
                .list(
                    part="snippet,statistics",
                    id=",".join(chunk),
                    maxResults=len(chunk),
                )
                .execute()
            )
            videos.extend(response.get("items", []))

        return videos
