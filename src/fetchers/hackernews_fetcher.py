"""Fetch top stories from HackerNews."""
import asyncio
import aiohttp
from typing import List
from datetime import datetime
from src.models.article import Article
from src.storage.markdown_storage import MarkdownStorage


class HackerNewsFetcher:
    """
    Fetches top stories from HackerNews API.
    
    API Docs: https://github.com/HackerNews/API
    """
    
    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self):
        self.storage = MarkdownStorage()
    
    async def fetch_and_save(self, limit: int = 30) -> List[Article]:
        """Fetch articles and save to markdown."""
        articles = await self.fetch(limit)
        
        if articles:
            self.storage.save(articles, "hackernews_articles.md")
        
        return articles
    
    async def fetch(self, limit: int = 30) -> List[Article]:
        """
        Fetch top stories from HackerNews.
        
        Args:
            limit: Number of stories to fetch (default 30)
            
        Returns:
            List of Article objects
        """
        print(f"📰 Fetching {limit} stories from HackerNews...")
        
        # Step 1: Get top story IDs
        story_ids = await self._fetch_top_story_ids()
        
        # Step 2: Fetch first N stories concurrently
        articles = await self._fetch_stories(story_ids[:limit])
        
        print(f"✅ Fetched {len(articles)} HackerNews stories")
        return articles
    
    async def _fetch_top_story_ids(self) -> List[int]:
        """Fetch list of top story IDs."""
        url = f"{self.BASE_URL}/topstories.json"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                story_ids = await response.json()
                return story_ids
    
    async def _fetch_stories(self, story_ids: List[int]) -> List[Article]:
        """
        Fetch multiple stories concurrently.
        
        This is where async shines - fetch all at once!
        """
        # Create tasks for all stories
        tasks = [self._fetch_story(story_id) for story_id in story_ids]
        
        # Run all tasks concurrently
        stories = await asyncio.gather(*tasks)
        
        # Filter out None (failed fetches)
        return [s for s in stories if s is not None]
    
    async def _fetch_story(self, story_id: int) -> Article:
        """Fetch single story by ID."""
        url = f"{self.BASE_URL}/item/{story_id}.json"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()
                    
                    # Skip if no URL (Ask HN, etc.)
                    if not data.get('url'):
                        return None
                    
                    # Convert to Article
                    return Article(
                        title=data.get('title', 'No Title'),
                        url=data['url'],
                        published_at=datetime.fromtimestamp(
                            data.get('time', 0)
                        ),
                        source='hackernews',
                        summary=data.get('text', '')[:200],  # First 200 chars
                        score=data.get('score', 0)
                    )
        except Exception as e:
            print(f"⚠️  Failed to fetch story {story_id}: {e}")
            return None
