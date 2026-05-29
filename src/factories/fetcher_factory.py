"""Factory for creating fetchers."""
from typing import Dict, List, Type

from src.fetchers.base_fetcher import BaseFetcher
from src.fetchers.github_trending_fetcher import GitHubTrendingFetcher
from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.fetchers.rss_fetcher import RSSFetcher


class FetcherFactory:
    """
    Factory for creating fetcher instances.

    Implements Factory pattern.
    """

    _fetchers: Dict[str, Type[BaseFetcher]] = {
        "hackernews": HackerNewsFetcher,
        "github": GitHubTrendingFetcher,
        "rss": RSSFetcher,
    }

    @classmethod
    def create(
        cls,
        source_type: str,
        transformer=None,
        storage=None,
        **kwargs,
    ) -> BaseFetcher:
        """
        Create fetcher by type.

        Args:
            source_type: Type of fetcher ('hackernews', 'github', 'rss')
            transformer: Transformer instance
            storage: Storage instance
            **kwargs: Additional args (e.g. feed_url for rss)

        Returns:
            Fetcher instance

        Raises:
            ValueError: If source_type unknown
        """
        if source_type not in cls._fetchers:
            raise ValueError(f"Unknown fetcher type: {source_type}")

        if source_type == "rss":
            feed_url = kwargs.get("feed_url")
            if not feed_url:
                raise ValueError("RSS fetcher requires feed_url")
            return RSSFetcher(feed_url, transformer, storage)

        fetcher_class = cls._fetchers[source_type]
        return fetcher_class(transformer, storage)

    @classmethod
    def register(cls, name: str, fetcher_class: Type[BaseFetcher]):
        """Register new fetcher type (allows extending factory without modifying it)."""
        cls._fetchers[name] = fetcher_class

    @classmethod
    def get_available_types(cls) -> List[str]:
        """Get list of available fetcher types."""
        return list(cls._fetchers.keys())
