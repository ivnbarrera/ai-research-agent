"""Test Liskov Substitution Principle — all fetchers are interchangeable."""
from __future__ import annotations

import pytest

from src.fetchers.base_fetcher import BaseFetcher
from src.fetchers.github_trending_fetcher import GitHubTrendingFetcher
from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.fetchers.rss_fetcher import RSSFetcher
from src.storage.markdown_storage import MarkdownStorage
from src.transformers.article_transformer import ArticleTransformer


@pytest.fixture
def transformer():
    return ArticleTransformer()


@pytest.fixture
def storage(tmp_path):
    return MarkdownStorage(base_path=str(tmp_path / "articles"))


def test_all_fetchers_implement_base_contract(transformer, storage):
    """All fetchers must implement BaseFetcher's abstract methods."""
    fetchers = [
        HackerNewsFetcher(transformer, storage),
        RSSFetcher("https://hnrss.org/frontpage", transformer, storage),
        GitHubTrendingFetcher(transformer, storage),
    ]

    for fetcher in fetchers:
        assert isinstance(fetcher, BaseFetcher)
        assert hasattr(fetcher, "fetch_articles")
        assert hasattr(fetcher, "get_source_name")
        assert hasattr(fetcher, "fetch_and_save")


def test_all_fetchers_return_string_source_name(transformer, storage):
    """get_source_name() must return a non-empty string for all fetchers."""
    fetchers = [
        HackerNewsFetcher(transformer, storage),
        RSSFetcher("https://hnrss.org/frontpage", transformer, storage),
        GitHubTrendingFetcher(transformer, storage),
    ]

    for fetcher in fetchers:
        name = fetcher.get_source_name()
        assert isinstance(name, str)
        assert len(name) > 0


def test_polymorphic_source_name_lookup(transformer, storage):
    """Any fetcher can be used anywhere BaseFetcher is expected."""

    def get_source(fetcher: BaseFetcher) -> str:
        return fetcher.get_source_name()

    assert get_source(HackerNewsFetcher(transformer, storage)) == "hackernews"
    assert get_source(GitHubTrendingFetcher(transformer, storage)) == "github_trending"
    assert get_source(RSSFetcher("https://hnrss.org/frontpage", transformer, storage)) == "rss"


def test_factory_creates_correct_types(transformer, storage):
    """FetcherFactory returns the right subclass for each source type."""
    from src.factories.fetcher_factory import FetcherFactory

    hn = FetcherFactory.create("hackernews", transformer, storage)
    assert isinstance(hn, HackerNewsFetcher)

    gh = FetcherFactory.create("github", transformer, storage)
    assert isinstance(gh, GitHubTrendingFetcher)

    rss = FetcherFactory.create("rss", transformer, storage, feed_url="https://hnrss.org/frontpage")
    assert isinstance(rss, RSSFetcher)


def test_factory_raises_for_unknown_type(transformer, storage):
    from src.factories.fetcher_factory import FetcherFactory

    with pytest.raises(ValueError):
        FetcherFactory.create("unknown_source", transformer, storage)
