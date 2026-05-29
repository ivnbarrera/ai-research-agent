"""Orchestrate multiple news fetchers."""
import asyncio
from typing import List

from src.fetchers.base_fetcher import BaseFetcher
from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.fetchers.rss_fetcher import RSSFetcher
from src.models.article import Article
from src.storage.base_storage import ArticleStorage
from src.storage.markdown_storage import MarkdownStorage
from src.transformers.article_transformer import ArticleTransformer


class FetchOrchestrator:
    """
    Orchestrates fetching from multiple sources.

    Follows Dependency Inversion Principle:
    - Depends on abstractions (BaseFetcher, ArticleStorage)
    - Dependencies injected via constructor
    """

    def __init__(
        self,
        fetchers: List[BaseFetcher] = None,
        storage: ArticleStorage = None,
        transformer: ArticleTransformer = None,
    ):
        """
        Initialize orchestrator.

        Args:
            fetchers: List of fetcher instances. If None, default set is created.
            storage: Storage implementation. If None, MarkdownStorage is used.
            transformer: Transformer instance. If None, ArticleTransformer is used.
        """
        self.transformer = transformer or ArticleTransformer()
        self.storage = storage or MarkdownStorage()

        if fetchers is None:
            self.fetchers = self._default_fetchers()
        else:
            self.fetchers = fetchers

    def _default_fetchers(self) -> List[BaseFetcher]:
        """Create default set of fetchers."""
        return [
            HackerNewsFetcher(self.transformer, self.storage),
            RSSFetcher("https://hnrss.org/frontpage", self.transformer, self.storage),
        ]

    async def fetch_all(self) -> List[Article]:
        """
        Fetch from all sources concurrently.

        Returns:
            Combined list of all articles
        """
        print(f"\n🚀 Starting fetch from {len(self.fetchers)} sources...")

        tasks = [fetcher.fetch_articles() for fetcher in self.fetchers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_articles = []
        for fetcher, result in zip(self.fetchers, results):
            name = fetcher.get_source_name()
            if isinstance(result, Exception):
                print(f"⚠️  {name} failed: {result}")
            else:
                print(f"✅ {name}: {len(result)} articles")
                all_articles.extend(result)

        if all_articles:
            self.storage.save(all_articles, "all_articles.md")

        print(f"\n🎉 Total: {len(all_articles)} articles from {len(self.fetchers)} sources")
        return all_articles


async def _main():
    orchestrator = FetchOrchestrator()
    articles = await orchestrator.fetch_all()

    print(f"\n📊 Sample articles:")
    for article in articles[:5]:
        print(f"  [{article.source}] {article.title[:60]}...")


if __name__ == "__main__":
    asyncio.run(_main())
