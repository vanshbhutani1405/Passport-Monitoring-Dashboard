from datetime import UTC, datetime
from typing import Any


def normalize_youtube_video(video: dict[str, Any]) -> dict[str, Any]:
    video_id = video.get("id")
    snippet = video.get("snippet") or {}
    statistics = video.get("statistics") or {}
    published_at = _parse_youtube_datetime(snippet.get("publishedAt"))

    return {
        "platform": "youtube",
        "platform_post_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else None,
        "title": snippet.get("title"),
        "content": snippet.get("description") or snippet.get("title") or "",
        "author_name": snippet.get("channelTitle"),
        "author_url": _channel_url(snippet.get("channelId")),
        "content_type": "video",
        "posted_at": published_at,
        "collected_at": datetime.now(UTC),
        "like_count": _to_int(statistics.get("likeCount")),
        "comment_count": _to_int(statistics.get("commentCount")),
        "share_count": 0,
        "view_count": _to_int(statistics.get("viewCount")),
        "raw_data": video,
    }


def _parse_youtube_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _to_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _channel_url(channel_id: str | None) -> str | None:
    if not channel_id:
        return None
    return f"https://www.youtube.com/channel/{channel_id}"
