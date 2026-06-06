from app.services.dedup import dedup_key, normalize_title
from app.services.paper_sources.base import PaperCandidate


def make_paper(**overrides):
    data = {
        "source": "arxiv",
        "source_id": "src-1",
        "title": "  Tool Use   For Agents! ",
        "abstract": None,
        "authors": [],
        "venue": None,
        "published_at": None,
        "url": "https://example.com",
        "doi": None,
        "arxiv_id": None,
        "semantic_scholar_id": None,
        "citation_count": None,
    }
    data.update(overrides)
    return PaperCandidate(**data)


def test_normalize_title():
    assert normalize_title("  Tool Use   For Agents! ") == "tool use for agents"


def test_prefers_doi():
    assert dedup_key(make_paper(doi="10.1000/ABC")) == "doi:10.1000/abc"


def test_prefers_arxiv_after_doi():
    assert dedup_key(make_paper(arxiv_id="2401.12345")) == "arxiv:2401.12345"


def test_falls_back_to_title_hash():
    assert dedup_key(make_paper()).startswith("title:")
