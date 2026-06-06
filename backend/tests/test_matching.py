from app.schemas import TopicConfig
from app.services.matching import match_paper
from app.services.paper_sources.base import PaperCandidate


def test_matches_keyword_and_venue():
    topic = TopicConfig(
        name="agents",
        keywords=["tool use"],
        venues=["ICLR"],
        exclude_keywords=[],
    )
    paper = PaperCandidate(
        source="arxiv",
        source_id="1234.5678",
        title="Tool Use Improves Agent Planning",
        abstract="A method for language model planning.",
        authors=["A. User"],
        venue="ICLR",
        published_at="2026-06-05",
        url="https://arxiv.org/abs/1234.5678",
        doi=None,
        arxiv_id="1234.5678",
        semantic_scholar_id=None,
        citation_count=None,
    )

    result = match_paper(paper, [topic])

    assert result.matched is True
    assert result.topic_names == ["agents"]
    assert "keyword: tool use" in result.reasons
    assert "venue: ICLR" in result.reasons


def test_exclusion_removes_paper():
    topic = TopicConfig(
        name="agents",
        keywords=["agent"],
        venues=[],
        exclude_keywords=["survey"],
    )
    paper = PaperCandidate(
        source="arxiv",
        source_id="9999.0000",
        title="A Survey of Agent Planning",
        abstract="Survey paper.",
        authors=[],
        venue=None,
        published_at=None,
        url="https://arxiv.org/abs/9999.0000",
        doi=None,
        arxiv_id="9999.0000",
        semantic_scholar_id=None,
        citation_count=None,
    )

    result = match_paper(paper, [topic])

    assert result.matched is False
    assert result.reasons == ["excluded: survey"]
