from unittest.mock import patch, MagicMock
import pytest
from fetch_arxiv import fetch_papers


def test_fetch_papers_returns_list():
    mock_entry = MagicMock()
    mock_entry.id = "http://arxiv.org/abs/2301.00001v1"
    mock_entry.title = "Test Paper"
    mock_entry.summary = "This is a test abstract."
    mock_entry.authors = [MagicMock(name="Author One")]
    mock_entry.tags = [MagicMock(term="cs.AI")]
    mock_entry.published = "2023-01-01T00:00:00Z"

    mock_feed = MagicMock()
    mock_feed.entries = [mock_entry]

    with patch("fetch_arxiv.feedparser.parse", return_value=mock_feed):
        results = fetch_papers(category="cs.AI", max_results=1)

    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["paper_id"] == "2301.00001"
    assert results[0]["title"] == "Test Paper"
    assert results[0]["abstract"] == "This is a test abstract."
    assert results[0]["category"] == "cs.AI"


def test_fetch_papers_retries_on_failure():
    from tenacity import RetryError
    with patch("fetch_arxiv.feedparser.parse", side_effect=[Exception("timeout"), Exception("timeout"), Exception("timeout")]):
        with pytest.raises(RetryError):
            fetch_papers(category="cs.AI", max_results=1)
