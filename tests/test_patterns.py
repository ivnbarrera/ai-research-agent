"""Tests for Factory and Strategy design patterns."""
from __future__ import annotations

import asyncio
import time

import pytest

from src.factories.fetcher_factory import FetcherFactory
from src.fetchers.github_trending_fetcher import GitHubTrendingFetcher
from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.fetchers.rss_fetcher import RSSFetcher
from src.storage.markdown_storage import MarkdownStorage
from src.strategies.rate_limit_strategy import SemaphoreStrategy, TokenBucketStrategy
from src.transformers.article_transformer import ArticleTransformer


# ---------------------------------------------------------------------------
# Factory pattern
# ---------------------------------------------------------------------------


@pytest.fixture
def transformer():
    return ArticleTransformer()


@pytest.fixture
def storage(tmp_path):
    return MarkdownStorage(base_path=str(tmp_path / "articles"))


def test_factory_creates_hackernews_fetcher(transformer, storage):
    fetcher = FetcherFactory.create("hackernews", transformer, storage)
    assert isinstance(fetcher, HackerNewsFetcher)


def test_factory_creates_github_fetcher(transformer, storage):
    fetcher = FetcherFactory.create("github", transformer, storage)
    assert isinstance(fetcher, GitHubTrendingFetcher)


def test_factory_creates_rss_fetcher(transformer, storage):
    fetcher = FetcherFactory.create(
        "rss", transformer, storage, feed_url="https://hnrss.org/frontpage"
    )
    assert isinstance(fetcher, RSSFetcher)


def test_factory_raises_for_unknown_type(transformer, storage):
    with pytest.raises(ValueError, match="Unknown fetcher type"):
        FetcherFactory.create("nonexistent", transformer, storage)


def test_factory_rss_raises_without_feed_url(transformer, storage):
    with pytest.raises(ValueError, match="feed_url"):
        FetcherFactory.create("rss", transformer, storage)


def test_factory_get_available_types_includes_known_sources():
    types = FetcherFactory.get_available_types()
    assert "hackernews" in types
    assert "github" in types
    assert "rss" in types


def test_factory_register_adds_new_type(transformer, storage):
    """register() lets callers extend the factory without modifying it (OCP)."""

    class DummyFetcher(HackerNewsFetcher):
        def get_source_name(self):
            return "dummy"

    FetcherFactory.register("dummy", DummyFetcher)
    fetcher = FetcherFactory.create("dummy", transformer, storage)
    assert isinstance(fetcher, DummyFetcher)
    assert fetcher.get_source_name() == "dummy"

    # Clean up so other tests are not affected
    del FetcherFactory._fetchers["dummy"]


def test_factory_created_fetcher_has_correct_source_name(transformer, storage):
    fetcher = FetcherFactory.create("hackernews", transformer, storage)
    assert fetcher.get_source_name() == "hackernews"


# ---------------------------------------------------------------------------
# Strategy pattern — SemaphoreStrategy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_semaphore_strategy_acquire_and_release():
    strategy = SemaphoreStrategy(max_concurrent=2)
    await strategy.acquire()
    strategy.release()
    # If we can acquire again the semaphore was properly released
    await strategy.acquire()
    strategy.release()


@pytest.mark.asyncio
async def test_semaphore_strategy_limits_concurrency():
    """With max_concurrent=1, tasks run sequentially."""
    strategy = SemaphoreStrategy(max_concurrent=1)
    results: list[int] = []

    async def task(n: int):
        await strategy.acquire()
        results.append(n)
        await asyncio.sleep(0.01)
        results.append(-n)
        strategy.release()

    await asyncio.gather(task(1), task(2))

    # Each task must complete before the next starts: [1, -1, 2, -2] or [2, -2, 1, -1]
    pairs = list(zip(results[::2], results[1::2]))
    for pos, neg in pairs:
        assert pos == -neg


@pytest.mark.asyncio
async def test_semaphore_strategy_allows_multiple_concurrent():
    """With max_concurrent=2, two tasks can overlap."""
    strategy = SemaphoreStrategy(max_concurrent=2)
    active: list[int] = []

    async def task():
        await strategy.acquire()
        active.append(1)
        await asyncio.sleep(0.02)
        strategy.release()
        active.pop()

    start = time.monotonic()
    await asyncio.gather(task(), task())
    elapsed = time.monotonic() - start

    # Both tasks ran concurrently so total time should be ~0.02 s, not ~0.04 s
    assert elapsed < 0.035


# ---------------------------------------------------------------------------
# Strategy pattern — TokenBucketStrategy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_token_bucket_allows_burst():
    """When the bucket is full, multiple acquires succeed immediately."""
    strategy = TokenBucketStrategy(rate=5, per=1.0)

    start = time.monotonic()
    for _ in range(5):
        await strategy.acquire()
    elapsed = time.monotonic() - start

    assert elapsed < 0.05  # Should be near-instant


@pytest.mark.asyncio
async def test_token_bucket_throttles_when_empty():
    """Once the bucket is empty, the next acquire sleeps."""
    strategy = TokenBucketStrategy(rate=1, per=0.1)

    await strategy.acquire()  # consumes the only token

    start = time.monotonic()
    await strategy.acquire()  # must wait for refill
    elapsed = time.monotonic() - start

    assert elapsed >= 0.05  # at least a noticeable wait


def test_token_bucket_release_is_noop():
    """release() on TokenBucketStrategy does not raise."""
    strategy = TokenBucketStrategy(rate=10, per=1.0)
    strategy.release()  # should be silent
