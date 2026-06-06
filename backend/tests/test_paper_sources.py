import pytest

from app.services.paper_sources.arxiv import ArxivSource
from app.services.paper_sources.base import PaperQuery
from app.services.paper_sources.semantic_scholar import SemanticScholarSource


class FakeResponse:
    def __init__(self, text=None, payload=None):
        self.text = text
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def get(self, url, params=None, headers=None):
        self.calls.append((url, params, headers))
        return self.response


@pytest.mark.asyncio
async def test_arxiv_source_parses_feed(monkeypatch):
    feed = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/2401.12345v1</id>
        <title>Tool Use for Agents</title>
        <summary>Agent paper abstract.</summary>
        <published>2026-06-05T00:00:00Z</published>
        <author><name>Alice</name></author>
        <link href="http://arxiv.org/abs/2401.12345v1" />
        <arxiv:doi xmlns:arxiv="http://arxiv.org/schemas/atom">10.1000/test</arxiv:doi>
      </entry>
    </feed>"""
    fake = FakeClient(FakeResponse(text=feed))
    monkeypatch.setattr("app.services.paper_sources.arxiv.httpx.AsyncClient", lambda timeout: fake)

    result = await ArxivSource().search(PaperQuery(["agent"], [], [], 30, 5))

    assert len(result) == 1
    assert result[0].title == "Tool Use for Agents"
    assert result[0].arxiv_id == "2401.12345"
    assert result[0].doi == "10.1000/test"


@pytest.mark.asyncio
async def test_semantic_scholar_source_parses_json(monkeypatch):
    payload = {
        "data": [
            {
                "paperId": "s2-1",
                "title": "Agent Planning",
                "abstract": "Planning with tools.",
                "authors": [{"name": "Bob"}],
                "venue": "ICLR",
                "year": 2026,
                "url": "https://semanticscholar.org/paper/s2-1",
                "citationCount": 10,
                "externalIds": {"DOI": "10.1000/s2", "ArXiv": "2401.00001"},
            }
        ]
    }
    fake = FakeClient(FakeResponse(payload=payload))
    monkeypatch.setattr("app.services.paper_sources.semantic_scholar.httpx.AsyncClient", lambda timeout: fake)

    result = await SemanticScholarSource().search(PaperQuery(["agent"], ["ICLR"], [], 7, 5))

    assert len(result) == 1
    assert result[0].semantic_scholar_id == "s2-1"
    assert result[0].venue == "ICLR"
    assert result[0].citation_count == 10
