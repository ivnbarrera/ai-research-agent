"""Fetch articles from RSS feeds."""
import asyncio
import re
from datetime import datetime
from typing import List

import feedparser

from src.fetchers.base_fetcher import BaseFetcher
from src.models.article import Article
from src.storage.markdown_storage import MarkdownStorage
from src.transformers.article_transformer import ArticleTransformer


class RSSFetcher(BaseFetcher):
    """
    Fetches articles from RSS feeds.

    Uses feedparser library for RSS parsing.
    """

    def __init__(self, feed_url: str, transformer=None, storage=None):
        """
        Initialize RSS fetcher.

        Args:
            feed_url: URL of RSS feed
            transformer: ArticleTransformer instance (created if not provided)
            storage: ArticleStorage instance (created if not provided)
        """
        transformer = transformer or ArticleTransformer()
        storage = storage or MarkdownStorage()
        super().__init__(transformer, storage)
        self.feed_url = feed_url

    async def fetch_articles(self) -> List[Article]:
        """
        Fetch articles from RSS feed.

        Returns:
            List of Article objects
        """
        print(f"📰 Fetching from RSS: {self.feed_url}")

        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, self.feed_url)

        articles = self.transformer.transform_rss(feed.entries)

        print(f"✅ Fetched {len(articles)} RSS articles")
        return articles

    def get_source_name(self) -> str:
        return "rss"

    async def fetch(self) -> List[Article]:
        """Alias for fetch_articles() to match M1 API."""
        return await self.fetch_articles()


async def _test_rss():
    """Test RSS fetcher."""
    fetcher = RSSFetcher("https://hnrss.org/frontpage")
    articles = await fetcher.fetch_and_save()

    print(f"\n📊 Fetched {len(articles)} articles")
    for article in articles[:3]:
        print(f"  - {article.title[:50]}...")


if __name__ == "__main__":
    asyncio.run(_test_rss())
