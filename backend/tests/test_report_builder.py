from app.schemas import PaperResponse
from app.services.report_builder import build_report_markdown


def test_build_report_markdown_groups_papers():
    papers = [
        PaperResponse(
            id=1,
            dedup_key="doi:1",
            source="fake",
            title="Tool Use for Agents",
            abstract="Abstract",
            authors=["Alice"],
            venue="ICLR",
            published_at="2026-06-05",
            url="https://example.com",
            doi="10.1000/1",
            arxiv_id=None,
            semantic_scholar_id=None,
            citation_count=2,
            topic_names=["agents"],
            match_reasons=["keyword: agents"],
        )
    ]
    summaries = {1: "一句话结论：这篇论文值得优先阅读。"}

    markdown = build_report_markdown("2026-06-06", papers, summaries)

    assert "# Paper Insight Daily Report - 2026-06-06" in markdown
    assert "## Worth Reading First" in markdown
    assert "Tool Use for Agents" in markdown
    assert "一句话结论" in markdown
