from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PaperCandidate:
    source: str
    source_id: str
    title: str
    abstract: str | None
    authors: list[str]
    venue: str | None
    published_at: str | None
    url: str
    doi: str | None
    arxiv_id: str | None
    semantic_scholar_id: str | None
    citation_count: int | None


@dataclass(frozen=True)
class PaperQuery:
    keywords: list[str]
    venues: list[str]
    exclude_keywords: list[str]
    lookback_days: int
    max_results: int


class PaperSource(Protocol):
    async def search(self, query: PaperQuery) -> list[PaperCandidate]:
        raise NotImplementedError
