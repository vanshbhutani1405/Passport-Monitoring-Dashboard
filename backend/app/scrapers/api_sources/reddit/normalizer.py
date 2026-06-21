from datetime import UTC, datetime
from typing import Any


def normalize_reddit_submission(submission: Any) -> dict[str, Any]:
    author = getattr(submission, "author", None)
    author_name = str(author) if author else None
    author_url = f"https://www.reddit.com/user/{author_name}" if author_name else None
    permalink = getattr(submission, "permalink", None)
    url = f"https://www.reddit.com{permalink}" if permalink else getattr(submission, "url", None)
    title = getattr(submission, "title", None)
    selftext = getattr(submission, "selftext", None) or ""
    created_utc = getattr(submission, "created_utc", None)

    return {
        "platform": "reddit",
        "platform_post_id": getattr(submission, "id"),
        "url": url,
        "title": title,
        "content": selftext or title or "",
        "author_name": author_name,
        "author_url": author_url,
        "content_type": "post",
        "posted_at": datetime.fromtimestamp(created_utc, tz=UTC) if created_utc else None,
        "collected_at": datetime.now(UTC),
        "like_count": int(getattr(submission, "score", 0) or 0),
        "comment_count": int(getattr(submission, "num_comments", 0) or 0),
        "share_count": 0,
        "view_count": 0,
        "raw_data": {
            "id": getattr(submission, "id", None),
            "subreddit": str(getattr(submission, "subreddit", "")),
            "title": title,
            "selftext": selftext,
            "author": author_name,
            "permalink": permalink,
            "url": getattr(submission, "url", None),
            "created_utc": created_utc,
            "score": getattr(submission, "score", None),
            "num_comments": getattr(submission, "num_comments", None),
            "upvote_ratio": getattr(submission, "upvote_ratio", None),
        },
    }
