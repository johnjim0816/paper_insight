import httpx

from app.services.paper_sources.base import PaperCandidate


class FakeSource:
    async def search(self, query):
        return [
            PaperCandidate(
                source="fake",
                source_id="fake-1",
                title="Tool Use for LLM Agents",
                abstract="An agent paper.",
                authors=["Alice"],
                venue="ICLR",
                published_at="2026-06-05",
                url="https://example.com/paper",
                doi="10.1000/fake",
                arxiv_id=None,
                semantic_scholar_id=None,
                citation_count=5,
            )
        ]


class RateLimitedSource:
    async def search(self, query):
        request = httpx.Request("GET", "https://example.test/search?query=very-long")
        response = httpx.Response(429, request=request)
        raise httpx.HTTPStatusError("Client error '429 ' for url 'https://example.test/search?query=very-long'", request=request, response=response)


def test_search_papers_saves_matches(client, monkeypatch):
    config = {
        "topics": [
            {
                "name": "agents",
                "keywords": ["LLM Agents"],
                "venues": ["ICLR"],
                "exclude_keywords": [],
            }
        ],
        "search": {"lookback_days": 7, "max_results_per_source": 5},
        "summary": {"language": "zh"},
        "delivery": {"provider": "feishu", "mode": "app_bot", "recipient_id_type": "email"},
    }
    client.put("/api/config", json=config)
    monkeypatch.setattr("app.api.papers.default_sources", lambda: [FakeSource()])

    response = client.post("/api/papers/search")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["papers"][0]["title"] == "Tool Use for LLM Agents"
    assert data["papers"][0]["match_reasons"] == ["keyword: LLM Agents", "venue: ICLR"]

    list_response = client.get("/api/papers")
    assert list_response.status_code == 200
    assert list_response.json()[0]["dedup_key"] == "doi:10.1000/fake"


def test_search_papers_returns_compact_source_warnings(client, monkeypatch):
    monkeypatch.setattr("app.api.papers.default_sources", lambda: [RateLimitedSource()])

    response = client.post("/api/papers/search")

    assert response.status_code == 200
    assert response.json()["warnings"] == ["RateLimitedSource: HTTP 429"]


def test_search_papers_uses_default_topic_without_manual_save(client, monkeypatch):
    monkeypatch.setattr("app.api.papers.default_sources", lambda: [FakeSource()])

    response = client.post("/api/papers/search")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["papers"][0]["title"] == "Tool Use for LLM Agents"
