"""Tests for MarkdownStorage."""
import pytest
from datetime import datetime
from pathlib import Path

from src.models.article import Article
from src.storage.markdown_storage import MarkdownStorage


@pytest.fixture
def tmp_storage(tmp_path):
    return MarkdownStorage(base_path=str(tmp_path / "articles"))


@pytest.fixture
def sample_article():
    return Article(
        title="Test Article",
        url="https://example.com/test",
        published_at=datetime(2026, 1, 1, 12, 0, 0),
        source="test",
        summary="A test summary.",
        score=42,
    )


def test_creates_directory_on_init(tmp_path):
    target = tmp_path / "new_dir" / "articles"
    assert not target.exists()
    MarkdownStorage(base_path=str(target))
    assert target.exists()


def test_save_returns_path(tmp_storage, sample_article):
    path = tmp_storage.save([sample_article], filename="out.md")
    assert isinstance(path, Path)
    assert path.exists()


def test_save_with_explicit_filename(tmp_storage, sample_article):
    path = tmp_storage.save([sample_article], filename="custom.md")
    assert path.name == "custom.md"


def test_save_auto_generates_filename(tmp_storage, sample_article):
    path = tmp_storage.save([sample_article])
    assert path.name.startswith("articles_")
    assert path.name.endswith(".md")


def test_saved_file_contains_article_title(tmp_storage, sample_article):
    path = tmp_storage.save([sample_article], filename="out.md")
    content = path.read_text(encoding="utf-8")
    assert "Test Article" in content


def test_saved_file_contains_article_url(tmp_storage, sample_article):
    path = tmp_storage.save([sample_article], filename="out.md")
    content = path.read_text(encoding="utf-8")
    assert "https://example.com/test" in content


def test_saved_file_contains_header(tmp_storage, sample_article):
    path = tmp_storage.save([sample_article], filename="out.md")
    content = path.read_text(encoding="utf-8")
    assert "# News Articles" in content


def test_save_multiple_articles(tmp_storage):
    articles = [
        Article(title=f"Article {i}", url=f"https://example.com/{i}",
                published_at=datetime(2026, 1, 1), source="test")
        for i in range(3)
    ]
    path = tmp_storage.save(articles, filename="multi.md")
    content = path.read_text(encoding="utf-8")
    assert "**Total Articles:** 3" in content
    for i in range(3):
        assert f"Article {i}" in content


def test_save_empty_list(tmp_storage):
    path = tmp_storage.save([], filename="empty.md")
    content = path.read_text(encoding="utf-8")
    assert "**Total Articles:** 0" in content
