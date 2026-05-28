"""Tests for HackerNewsFetcher."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.models.article import Article


STORY_DATA = {
    "id": 42,
    "title": "Test Story",
    "url": "https://example.com/story",
    "time": 1700000000,
    "score": 100,
    "text": "Some description",
}

ASK_HN_DATA = {
    "id": 43,
    "title": "Ask HN: Something?",
    "time": 1700000000,
    "score": 50,
    # no 'url' key
}


def _mock_session(json_data):
    """Build an aiohttp.ClientSession mock that returns json_data."""
    response = AsyncMock()
    response.json = AsyncMock(return_value=json_data)
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=False)

    session = MagicMock()
    session.get = MagicMock(return_value=response)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return session


@pytest.fixture
def fetcher():
    return HackerNewsFetcher()


# --- _fetch_top_story_ids ---

@pytest.mark.asyncio
async def test_fetch_top_story_ids_returns_list(fetcher):
    ids = [1, 2, 3, 4, 5]
    with patch("aiohttp.ClientSession", return_value=_mock_session(ids)):
        result = await fetcher._fetch_top_story_ids()
    assert result == ids


@pytest.mark.asyncio
async def test_fetch_top_story_ids_hits_correct_url(fetcher):
    session = _mock_session([])
    with patch("aiohttp.ClientSession", return_value=session):
        await fetcher._fetch_top_story_ids()
    session.get.assert_called_once_with(
        "https://hacker-news.firebaseio.com/v0/topstories.json"
    )


# --- _fetch_story ---

@pytest.mark.asyncio
async def test_fetch_story_returns_article(fetcher):
    with patch("aiohttp.ClientSession", return_value=_mock_session(STORY_DATA)):
        article = await fetcher._fetch_story(42)

    assert isinstance(article, Article)
    assert article.title == "Test Story"
    assert article.url == "https://example.com/story"
    assert article.source == "hackernews"
    assert article.score == 100
    assert article.published_at == datetime.fromtimestamp(1700000000)


@pytest.mark.asyncio
async def test_fetch_story_truncates_summary_to_200_chars(fetcher):
    long_text = "x" * 300
    data = {**STORY_DATA, "text": long_text}
    with patch("aiohttp.ClientSession", return_value=_mock_session(data)):
        article = await fetcher._fetch_story(42)
    assert len(article.summary) == 200


@pytest.mark.asyncio
async def test_fetch_story_returns_none_when_no_url(fetcher):
    with patch("aiohttp.ClientSession", return_value=_mock_session(ASK_HN_DATA)):
        article = await fetcher._fetch_story(43)
    assert article is None


@pytest.mark.asyncio
async def test_fetch_story_returns_none_on_exception(fetcher):
    session = MagicMock()
    session.__aenter__ = AsyncMock(side_effect=Exception("network error"))
    session.__aexit__ = AsyncMock(return_value=False)
    with patch("aiohttp.ClientSession", return_value=session):
        article = await fetcher._fetch_story(99)
    assert article is None


@pytest.mark.asyncio
async def test_fetch_story_uses_correct_url(fetcher):
    session = _mock_session(STORY_DATA)
    with patch("aiohttp.ClientSession", return_value=session):
        await fetcher._fetch_story(42)
    session.get.assert_called_once_with(
        "https://hacker-news.firebaseio.com/v0/item/42.json"
    )


# --- _fetch_stories ---

@pytest.mark.asyncio
async def test_fetch_stories_filters_none(fetcher):
    async def fake_fetch_story(story_id):
        return None if story_id == 2 else Article(
            title=f"Story {story_id}",
            url=f"https://example.com/{story_id}",
            published_at=datetime(2026, 1, 1),
            source="hackernews",
        )

    fetcher._fetch_story = fake_fetch_story
    result = await fetcher._fetch_stories([1, 2, 3])
    assert len(result) == 2
    assert all(a is not None for a in result)


# --- fetch (integration-style) ---

@pytest.mark.asyncio
async def test_fetch_respects_limit(fetcher):
    all_ids = list(range(1, 101))

    async def fake_fetch_top_story_ids():
        return all_ids

    async def fake_fetch_stories(ids):
        return [
            Article(
                title=f"Story {i}",
                url=f"https://example.com/{i}",
                published_at=datetime(2026, 1, 1),
                source="hackernews",
            )
            for i in ids
        ]

    fetcher._fetch_top_story_ids = fake_fetch_top_story_ids
    fetcher._fetch_stories = fake_fetch_stories

    result = await fetcher.fetch(limit=5)
    assert len(result) == 5


@pytest.mark.asyncio
async def test_fetch_returns_articles(fetcher):
    async def fake_fetch_top_story_ids():
        return [1, 2]

    async def fake_fetch_stories(ids):
        return [
            Article(
                title=f"Story {i}",
                url=f"https://example.com/{i}",
                published_at=datetime(2026, 1, 1),
                source="hackernews",
            )
            for i in ids
        ]

    fetcher._fetch_top_story_ids = fake_fetch_top_story_ids
    fetcher._fetch_stories = fake_fetch_stories

    result = await fetcher.fetch()
    assert all(isinstance(a, Article) for a in result)


# --- fetch_and_save ---

@pytest.mark.asyncio
async def test_fetch_and_save_returns_articles(fetcher):
    articles = [
        Article(title="A", url="https://a.com", published_at=datetime(2026, 1, 1), source="hackernews")
    ]
    fetcher.fetch = AsyncMock(return_value=articles)
    fetcher.storage.save = MagicMock()

    result = await fetcher.fetch_and_save(limit=10)

    assert result == articles


@pytest.mark.asyncio
async def test_fetch_and_save_calls_fetch_with_limit(fetcher):
    fetcher.fetch = AsyncMock(return_value=[])
    fetcher.storage.save = MagicMock()

    await fetcher.fetch_and_save(limit=7)

    fetcher.fetch.assert_called_once_with(7)


@pytest.mark.asyncio
async def test_fetch_and_save_saves_when_articles_returned(fetcher):
    articles = [
        Article(title="A", url="https://a.com", published_at=datetime(2026, 1, 1), source="hackernews")
    ]
    fetcher.fetch = AsyncMock(return_value=articles)
    fetcher.storage.save = MagicMock()

    await fetcher.fetch_and_save()

    fetcher.storage.save.assert_called_once_with(articles, "hackernews_articles.md")


@pytest.mark.asyncio
async def test_fetch_and_save_skips_save_when_no_articles(fetcher):
    fetcher.fetch = AsyncMock(return_value=[])
    fetcher.storage.save = MagicMock()

    await fetcher.fetch_and_save()

    fetcher.storage.save.assert_not_called()
