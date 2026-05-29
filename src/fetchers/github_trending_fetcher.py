"""Fetch from GitHub Trending."""
import asyncio
from datetime import datetime
from typing import List

import aiohttp
from bs4 import BeautifulSoup

from src.fetchers.base_fetcher import BaseFetcher
from src.models.article import Article
from src.storage.markdown_storage import MarkdownStorage
from src.transformers.article_transformer import ArticleTransformer


class GitHubTrendingFetcher(BaseFetcher):
    """
    Fetch trending repositories from GitHub.

    NEW fetcher added without modifying existing code — demonstrates Open/Closed Principle.
    """

    def __init__(self, transformer=None, storage=None):
        transformer = transformer or ArticleTransformer()
        storage = storage or MarkdownStorage()
        super().__init__(transformer, storage)

    async def fetch_articles(self) -> List[Article]:
        """Scrape GitHub trending page."""
        url = "https://github.com/trending"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    html = await response.text()
        except Exception as e:
            print(f"⚠️  GitHub Trending fetch failed: {e}")
            return []

        soup = BeautifulSoup(html, "html.parser")
        repos = soup.select("article.Box-row")

        articles = []
        for repo in repos[:20]:
            title_elem = repo.select_one("h2 a")
            if not title_elem:
                continue

            title = title_elem.text.strip().replace("\n", "").replace(" ", "")
            href = title_elem.get("href", "")
            repo_url = f"https://github.com{href}"

            description_elem = repo.select_one("p")
            description = description_elem.text.strip() if description_elem else ""

            stars_elem = repo.select_one("span.d-inline-block.float-sm-right")
            stars = stars_elem.text.strip() if stars_elem else "0"

            article = Article(
                title=title,
                url=repo_url,
                published_at=datetime.now(),
                source="github_trending",
                summary=f"{description} (⭐ {stars})",
                score=0,
            )
            articles.append(article)

        return articles

    def get_source_name(self) -> str:
        return "github_trending"
