import httpx
import json

from app.api.papers import _source_warning
from app.core.config import get_settings
from app.services.paper_sources.base import PaperCandidate
from app.services.paper_sources.semantic_scholar import SemanticScholarSource


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


class MultiTopicSource:
    def __init__(self):
        self.queries = []

    async def search(self, query):
        self.queries.append(query)
        return [
            PaperCandidate(
                source="fake",
                source_id="rl-1",
                title="Deep Reinforcement Learning for Agents",
                abstract="A reinforcement learning paper.",
                authors=["Alice"],
                venue="NeurIPS",
                published_at="2026-06-05",
                url="https://example.com/rl",
                doi="10.1000/rl",
                arxiv_id=None,
                semantic_scholar_id=None,
                citation_count=8,
            ),
            PaperCandidate(
                source="fake",
                source_id="wm-1",
                title="World Model Planning",
                abstract="A world model paper.",
                authors=["Bob"],
                venue="ICLR",
                published_at="2026-06-04",
                url="https://example.com/world-model",
                doi="10.1000/wm",
                arxiv_id=None,
                semantic_scholar_id=None,
                citation_count=6,
            ),
        ]


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


def test_search_papers_filters_to_requested_topic(client, monkeypatch):
    config = {
        "topics": [
            {"name": "RL", "keywords": ["reinforcement learning"], "venues": ["NeurIPS"], "exclude_keywords": []},
            {"name": "worldmodel", "keywords": ["world model"], "venues": ["ICLR"], "exclude_keywords": []},
        ],
        "search": {"lookback_days": 7, "max_results_per_source": 5},
        "summary": {"language": "zh"},
        "delivery": {"provider": "feishu", "mode": "app_bot", "recipient_id_type": "email"},
    }
    client.put("/api/config", json=config)
    source = MultiTopicSource()
    monkeypatch.setattr("app.api.papers.default_sources", lambda: [source])

    response = client.post("/api/papers/search?topic=RL")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["papers"][0]["title"] == "Deep Reinforcement Learning for Agents"
    assert data["papers"][0]["topic_names"] == ["RL"]
    assert source.queries[0].keywords == ["reinforcement learning"]
    assert source.queries[0].venues == ["NeurIPS"]


def test_search_papers_writes_results_to_configured_data_dir(client, monkeypatch, tmp_path):
    get_settings.cache_clear()
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setattr("app.api.papers.default_sources", lambda: [FakeSource()])

    response = client.post("/api/papers/search")

    assert response.status_code == 200
    papers_file = tmp_path / "papers" / "papers.json"
    sources_file = tmp_path / "papers" / "sources.json"
    assert papers_file.exists()
    assert sources_file.exists()

    papers_payload = json.loads(papers_file.read_text(encoding="utf-8"))
    assert papers_payload["count"] == 1
    assert papers_payload["papers"][0]["title"] == "Tool Use for LLM Agents"

    sources_payload = json.loads(sources_file.read_text(encoding="utf-8"))
    assert sources_payload["query"]["keywords"] == ["LLM agent", "tool use", "autonomous agents"]
    get_settings.cache_clear()


def test_topic_search_writes_results_to_topic_data_dir(client, monkeypatch, tmp_path):
    get_settings.cache_clear()
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    config = {
        "topics": [
            {"name": "RL", "keywords": ["reinforcement learning"], "venues": ["NeurIPS"], "exclude_keywords": []},
            {"name": "worldmodel", "keywords": ["world model"], "venues": ["ICLR"], "exclude_keywords": []},
        ],
        "search": {"lookback_days": 7, "max_results_per_source": 5},
        "summary": {"language": "zh"},
        "delivery": {"provider": "feishu", "mode": "app_bot", "recipient_id_type": "email"},
    }
    client.put("/api/config", json=config)
    monkeypatch.setattr("app.api.papers.default_sources", lambda: [MultiTopicSource()])

    response = client.post("/api/papers/search?topic=RL")

    assert response.status_code == 200
    papers_file = tmp_path / "topics" / "rl" / "papers" / "papers.json"
    sources_file = tmp_path / "topics" / "rl" / "papers" / "sources.json"
    assert papers_file.exists()
    assert sources_file.exists()
    assert json.loads(papers_file.read_text(encoding="utf-8"))["papers"][0]["topic_names"] == ["RL"]
    assert json.loads(sources_file.read_text(encoding="utf-8"))["topic"] == "RL"
    get_settings.cache_clear()


def test_search_papers_returns_compact_source_warnings(client, monkeypatch):
    monkeypatch.setattr("app.api.papers.default_sources", lambda: [RateLimitedSource()])

    response = client.post("/api/papers/search")

    assert response.status_code == 200
    assert response.json()["warnings"] == ["RateLimitedSource: HTTP 429"]


def test_semantic_scholar_rate_limit_warning_mentions_api_key():
    request = httpx.Request("GET", "https://api.semanticscholar.org/graph/v1/paper/search")
    response = httpx.Response(429, request=request)
    exc = httpx.HTTPStatusError("Rate limited", request=request, response=response)

    warning = _source_warning(SemanticScholarSource(), exc)

    assert warning == "SemanticScholarSource: HTTP 429 rate limited; set SEMANTIC_SCHOLAR_API_KEY or retry later"


def test_search_papers_uses_default_topic_without_manual_save(client, monkeypatch):
    monkeypatch.setattr("app.api.papers.default_sources", lambda: [FakeSource()])

    response = client.post("/api/papers/search")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["papers"][0]["title"] == "Tool Use for LLM Agents"
