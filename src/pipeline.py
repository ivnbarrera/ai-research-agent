"""Complete pipeline: Fetch → Filter."""
import asyncio
from pathlib import Path

from src.agents.news_filter_agent import NewsFilterAgent
from src.orchestrator import FetchOrchestrator


async def run_pipeline():
    """
    Run complete pipeline.

    1. Fetch articles (Milestone 1)
    2. Filter with AI agent (Milestone 3)
    """
    print("=" * 60)
    print("  Complete Pipeline: Fetch + Filter")
    print("=" * 60)

    print("\n📰 Step 1: Fetching articles...")
    orchestrator = FetchOrchestrator()
    articles = await orchestrator.fetch_all()

    fetch_output = Path("data/articles/all_articles.md")
    print(f"✅ Fetched {len(articles)} articles")
    print(f"   Saved to: {fetch_output}")

    print("\n🤖 Step 2: Filtering with AI...")
    agent = NewsFilterAgent()
    filter_output = Path("data/context/filtered_articles.md")

    await agent.execute(
        input_path=str(fetch_output),
        output_path=str(filter_output),
    )

    print(f"✅ Filtering complete")
    print(f"   Filtered articles: {filter_output}")

    print("\n" + "=" * 60)
    print("🎉 Pipeline complete!")
    print(f"   1. Fetched: {fetch_output}")
    print(f"   2. Filtered: {filter_output}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
