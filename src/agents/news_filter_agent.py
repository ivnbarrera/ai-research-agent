"""Agent that filters AI-relevant articles."""
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from src.agents.base_agent import BaseAgent


class NewsFilterAgent(BaseAgent):
    """
    Filters articles for AI/ML relevance.

    Reads articles from markdown, uses LLM to judge relevance,
    saves filtered articles.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.relevance_threshold = 6

    async def _load_context(self, input_path: str) -> Dict[str, Any]:
        """Load articles from markdown file."""
        print(f"📖 Loading articles from {input_path}")

        content = Path(input_path).read_text()
        articles = self._parse_markdown(content)

        print(f"   Found {len(articles)} articles")
        return {"articles": articles}

    def _parse_markdown(self, content: str) -> List[Dict]:
        """Parse markdown content to extract articles."""
        articles = []

        sections = content.split("---")

        for section in sections:
            if "##" not in section:
                continue

            title_match = re.search(r"## (.+)", section)
            if not title_match:
                continue

            title = title_match.group(1).strip()

            url_match = re.search(r"\*\*URL:\*\* (.+)", section)
            url = url_match.group(1).strip() if url_match else ""

            lines = [
                line
                for line in section.split("\n")
                if line.strip() and not line.startswith("**")
            ]
            summary = lines[-1] if lines else ""

            articles.append({"title": title, "url": url, "summary": summary})

        return articles

    async def _process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Filter articles using LLM."""
        articles = context["articles"]
        print(f"🔍 Filtering {len(articles)} articles...")

        filtered = []

        for i, article in enumerate(articles):
            print(f"   [{i+1}/{len(articles)}] {article['title'][:50]}...")

            judgment = self._judge_relevance(article)

            if (
                judgment["relevant"]
                and judgment["relevance_score"] >= self.relevance_threshold
            ):
                filtered.append(
                    {
                        **article,
                        "relevance_score": judgment["relevance_score"],
                        "reasoning": judgment["reasoning"],
                        "key_topics": judgment.get("key_topics", []),
                    }
                )
                print(f"      ✅ Relevant (score: {judgment['relevance_score']})")
            else:
                print(f"      ❌ Not relevant (score: {judgment['relevance_score']})")

        print(f"\n📊 Filtered: {len(filtered)}/{len(articles)} articles")

        return {
            "filtered_articles": filtered,
            "total_input": len(articles),
            "total_output": len(filtered),
        }

    def _judge_relevance(self, article: Dict) -> Dict:
        """Use LLM to judge article relevance."""
        prompt = f"""You are an expert AI/ML news analyst. Judge if this article is relevant to AI/ML.

Article:
Title: {article['title']}
Summary: {article['summary']}

Relevant topics include: Machine Learning, LLMs, Neural Networks, Computer Vision, NLP, AI Research, AI Applications, Deep Learning, Transformers, GPT, Stable Diffusion, AI Ethics, AI Safety

Output ONLY valid JSON with this exact format:
{{
  "relevant": true or false,
  "relevance_score": 1-10,
  "reasoning": "brief explanation",
  "key_topics": ["topic1", "topic2"]
}}

Examples:
- "GPT-4 Released" -> {{"relevant": true, "relevance_score": 10, "reasoning": "Major LLM release", "key_topics": ["LLM", "GPT"]}}
- "New JavaScript Framework" -> {{"relevant": false, "relevance_score": 1, "reasoning": "Web dev, not AI", "key_topics": []}}

Your JSON response:"""

        try:
            response = self._call_llm(prompt)

            json_text = response
            if "```json" in response:
                json_text = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_text = response.split("```")[1].split("```")[0]

            judgment = json.loads(json_text.strip())

            assert "relevant" in judgment
            assert "relevance_score" in judgment
            assert "reasoning" in judgment

            return judgment

        except Exception as e:
            print(f"      ⚠️  Failed to parse LLM response: {e}")
            return {
                "relevant": False,
                "relevance_score": 0,
                "reasoning": f"Failed to judge: {e}",
                "key_topics": [],
            }

    async def _save_result(self, result: Dict[str, Any], output_path: str):
        """Save filtered articles to markdown."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        articles = result["filtered_articles"]

        with open(output_path, "w") as f:
            f.write("# Filtered AI/ML Articles\n\n")
            f.write(f"**Total Input:** {result['total_input']}\n")
            f.write(f"**Total Output:** {result['total_output']}\n")
            if result["total_input"] > 0:
                pct = result["total_output"] / result["total_input"] * 100
                f.write(f"**Filter Rate:** {pct:.1f}%\n\n")
            else:
                f.write("**Filter Rate:** N/A\n\n")
            f.write("---\n\n")

            for article in articles:
                f.write(f"## {article['title']}\n\n")
                f.write(f"**URL:** {article['url']}\n")
                f.write(f"**Relevance Score:** {article['relevance_score']}/10\n")
                f.write(f"**Reasoning:** {article['reasoning']}\n")
                f.write(f"**Key Topics:** {', '.join(article['key_topics'])}\n\n")
                f.write(f"{article['summary']}\n\n")
                f.write("---\n\n")

        print(f"💾 Saved {len(articles)} filtered articles to {output_path}")
