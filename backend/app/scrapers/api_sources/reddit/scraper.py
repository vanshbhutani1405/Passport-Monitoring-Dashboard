import logging
from collections.abc import Iterable

from app.core.config import Settings, get_settings


logger = logging.getLogger(__name__)

REDDIT_SEARCH_KEYWORDS = [
    "passport",
    "passport renewal",
    "passport seva",
    "passport application",
    "passport delay",
]


class RedditScraper:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._reddit = None

    def _get_client(self):
        if self._reddit is not None:
            return self._reddit

        if not self.settings.reddit_client_id or not self.settings.reddit_client_secret:
            raise ValueError(
                "Reddit credentials are missing. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET."
            )

        try:
            import praw
        except ImportError as exc:
            raise RuntimeError("PRAW is required for Reddit ingestion. Install the praw package.") from exc

        self._reddit = praw.Reddit(
            client_id=self.settings.reddit_client_id,
            client_secret=self.settings.reddit_client_secret,
            user_agent=self.settings.reddit_user_agent,
        )
        return self._reddit

    def search(
        self,
        keywords: Iterable[str] = REDDIT_SEARCH_KEYWORDS,
        limit_per_keyword: int = 25,
        subreddit: str = "all",
    ) -> list:
        reddit = self._get_client()
        submissions = []

        for keyword in keywords:
            try:
                logger.info("Searching Reddit for keyword=%s subreddit=%s", keyword, subreddit)
                results = reddit.subreddit(subreddit).search(
                    keyword,
                    sort="new",
                    time_filter="year",
                    limit=limit_per_keyword,
                )
                submissions.extend(results)
            except Exception:
                logger.exception("Reddit search failed for keyword=%s", keyword)
                raise

        return submissions
