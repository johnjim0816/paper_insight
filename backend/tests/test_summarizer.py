import pytest

from app.schemas import PaperResponse
from app.services.summarizer import summarize_paper


class BrokenClient:
    async def post(self, url, headers=None, json=None):
        raise RuntimeError("network down")


@pytest.mark.asyncio
async def test_summarizer_fallback_on_failure():
    paper = PaperResponse(
        id=1,
        dedup_key="doi:1",
        source="fake",
        title="Tool Use for Agents",
        abstract=None,
        authors=[],
        venue=None,
        published_at=None,
        url="https://example.com",
        doi=None,
        arxiv_id=None,
        semantic_scholar_id=None,
        citation_count=None,
        topic_names=["agents"],
        match_reasons=["keyword: agents"],
    )

    result = await summarize_paper(
        paper,
        api_key="key",
        base_url="https://api.example.com/v1",
        model="model",
        client=BrokenClient(),
    )

    assert "摘要生成失败" in result
    assert "Tool Use for Agents" in result
