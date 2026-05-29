"""Tests for FetchOrchestrator with mocked dependencies."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.article import Article
from src.orchestrator import FetchOrchestrator


def _make_article(title: str = "Test", source: str = "test") -> Article:
    return Article(
        title=title,
        url=f"https://example.com/{title.lower()}",
        published_at=datetime(2026, 1, 1),
        source=source,
    )


def _mock_fetcher(articles: list[Article], source_name: str = "mock") -> MagicMock:
    fetcher = MagicMock()
    fetcher.get_source_name.return_value = source_name
    fetcher.fetch_articles = AsyncMock(return_value=articles)
    fetcher.fetch_and_save = AsyncMock(return_value=articles)
    return fetcher


@pytest.mark.asyncio
async def test_fetch_all_returns_combined_articles():
    """fetch_all aggregates articles from all fetchers."""
    f1 = _mock_fetcher([_make_article("A", "src1")], "src1")
    f2 = _mock_fetcher([_make_article("B", "src2")], "src2")

    orchestrator = FetchOrchestrator(
        fetchers=[f1, f2],
        storage=MagicMock(),
        transformer=MagicMock(),
    )

    articles = await orchestrator.fetch_all()

    assert len(articles) == 2
    titles = {a.title for a in articles}
    assert titles == {"A", "B"}


@pytest.mark.asyncio
async def test_fetch_all_with_single_fetcher():
    """fetch_all works with a single fetcher."""
    article = _make_article("Solo")
    fetcher = _mock_fetcher([article], "solo")

    orchestrator = FetchOrchestrator(
        fetchers=[fetcher],
        storage=MagicMock(),
        transformer=MagicMock(),
    )

    result = await orchestrator.fetch_all()

    assert len(result) == 1
    assert result[0].title == "Solo"


@pytest.mark.asyncio
async def test_fetch_all_calls_each_fetcher():
    """fetch_all calls fetch_articles on every registered fetcher."""
    f1 = _mock_fetcher([], "s1")
    f2 = _mock_fetcher([], "s2")
    f3 = _mock_fetcher([], "s3")

    orchestrator = FetchOrchestrator(
        fetchers=[f1, f2, f3],
        storage=MagicMock(),
        transformer=MagicMock(),
    )

    await orchestrator.fetch_all()

    f1.fetch_articles.assert_called_once()
    f2.fetch_articles.assert_called_once()
    f3.fetch_articles.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_all_handles_fetcher_exception_gracefully():
    """A failing fetcher does not crash the whole orchestration run."""
    good = _mock_fetcher([_make_article("Good")], "good")

    bad = MagicMock()
    bad.get_source_name.return_value = "bad"
    bad.fetch_articles = AsyncMock(side_effect=RuntimeError("network down"))

    orchestrator = FetchOrchestrator(
        fetchers=[good, bad],
        storage=MagicMock(),
        transformer=MagicMock(),
    )

    articles = await orchestrator.fetch_all()

    assert len(articles) == 1
    assert articles[0].title == "Good"


@pytest.mark.asyncio
async def test_fetch_all_returns_empty_list_when_no_fetchers():
    """fetch_all returns empty list when fetchers list is empty."""
    orchestrator = FetchOrchestrator(
        fetchers=[],
        storage=MagicMock(),
        transformer=MagicMock(),
    )

    result = await orchestrator.fetch_all()

    assert result == []


@pytest.mark.asyncio
async def test_fetch_all_saves_combined_articles():
    """fetch_all saves the aggregated article list to storage."""
    articles = [_make_article("X"), _make_article("Y")]
    fetcher = _mock_fetcher(articles, "src")
    storage = MagicMock()

    orchestrator = FetchOrchestrator(
        fetchers=[fetcher],
        storage=storage,
        transformer=MagicMock(),
    )

    await orchestrator.fetch_all()

    storage.save.assert_called_once()
    saved_articles = storage.save.call_args[0][0]
    assert len(saved_articles) == 2
