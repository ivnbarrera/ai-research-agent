"""Tests for NewsFilterAgent."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.agents.news_filter_agent import NewsFilterAgent
from src.tools.calculator import calculator
from src.tools.web_search import web_search


# --- tool unit tests ---


def test_calculator_addition():
    result = calculator("2 + 2")
    assert result["success"]
    assert result["result"] == 4


def test_calculator_multiplication():
    result = calculator("10 * 5 + 3")
    assert result["success"]
    assert result["result"] == 53


def test_calculator_invalid_expression():
    result = calculator("not a number")
    assert not result["success"]
    assert "error" in result


def test_web_search_returns_results():
    result = web_search("AI news")
    assert result["success"]
    assert result["query"] == "AI news"
    assert len(result["results"]) > 0


def test_web_search_respects_num_results():
    result = web_search("test", num_results=2)
    assert len(result["results"]) == 2


# --- agent parse tests (no LLM) ---


def test_parse_markdown_extracts_articles():
    agent = NewsFilterAgent.__new__(NewsFilterAgent)
    content = """
## GPT-4 Released by OpenAI

**URL:** https://example.com/gpt4

OpenAI announces GPT-4 with enhanced capabilities.

---

## New JavaScript Framework

**URL:** https://example.com/js

React alternative for web development.
"""
    articles = agent._parse_markdown(content)
    assert len(articles) == 2
    titles = [a["title"] for a in articles]
    assert "GPT-4 Released by OpenAI" in titles
    assert "New JavaScript Framework" in titles


# --- agent integration test (mocked LLM) ---


@pytest.mark.asyncio
async def test_agent_filters_articles_with_mock_llm(tmp_path):
    """Agent correctly filters and saves articles when LLM is mocked."""
    input_file = tmp_path / "input.md"
    output_file = tmp_path / "output.md"

    input_file.write_text(
        """## GPT-4 Released by OpenAI

**URL:** https://example.com/gpt4

OpenAI announces GPT-4 with enhanced capabilities.

---

## New JavaScript Framework

**URL:** https://example.com/js

React alternative for web development.
"""
    )

    relevant_response = json.dumps(
        {
            "relevant": True,
            "relevance_score": 10,
            "reasoning": "Major LLM release",
            "key_topics": ["LLM", "GPT"],
        }
    )
    not_relevant_response = json.dumps(
        {
            "relevant": False,
            "relevance_score": 1,
            "reasoning": "Web dev, not AI",
            "key_topics": [],
        }
    )

    responses = iter([relevant_response, not_relevant_response])

    with patch("src.agents.base_agent.completion") as mock_completion:

        def side_effect(*args, **kwargs):
            msg = MagicMock()
            msg.content = next(responses)
            msg.tool_calls = None
            choice = MagicMock()
            choice.message = msg
            resp = MagicMock()
            resp.choices = [choice]
            return resp

        mock_completion.side_effect = side_effect

        agent = NewsFilterAgent(model="gpt-4o-mini")
        await agent.execute(str(input_file), str(output_file))

    assert output_file.exists()
    content = output_file.read_text()
    assert "GPT-4" in content
    assert "JavaScript" not in content


@pytest.mark.asyncio
async def test_judge_relevance_handles_llm_error():
    """_judge_relevance returns not-relevant default when LLM raises."""
    with patch("src.agents.base_agent.completion", side_effect=RuntimeError("API error")):
        agent = NewsFilterAgent(model="gpt-4o-mini")
        result = agent._judge_relevance(
            {"title": "Test", "summary": "Test summary"}
        )

    assert result["relevant"] is False
    assert result["relevance_score"] == 0
