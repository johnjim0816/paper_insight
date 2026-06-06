import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.config import _read_config
from app.db.models import Paper
from app.db.session import get_db
from app.schemas import PaperResponse, PaperSearchResponse, TopicConfig
from app.services.artifact_store import save_paper_search_artifacts
from app.services.matching import match_paper
from app.services.paper_repository import paper_to_response, upsert_paper
from app.services.paper_sources.arxiv import ArxivSource
from app.services.paper_sources.base import PaperQuery, PaperSource
from app.services.paper_sources.semantic_scholar import SemanticScholarSource

router = APIRouter(prefix="/api/papers", tags=["papers"])


def default_sources() -> list[PaperSource]:
    return [ArxivSource(), SemanticScholarSource()]


def _source_warning(source: PaperSource, exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        if source.__class__.__name__ == "SemanticScholarSource" and exc.response.status_code == 429:
            return "SemanticScholarSource: HTTP 429 rate limited; set SEMANTIC_SCHOLAR_API_KEY or retry later"
        return f"{source.__class__.__name__}: HTTP {exc.response.status_code}"

    message = str(exc).strip().splitlines()[0] if str(exc).strip() else exc.__class__.__name__
    return f"{source.__class__.__name__}: {message}"


def _topics_for_search(topics: list[TopicConfig], topic_name: str | None) -> tuple[list[TopicConfig], str | None]:
    if topic_name is None or not topic_name.strip():
        return topics, None

    requested = topic_name.strip().lower()
    for topic in topics:
        if topic.name.strip().lower() == requested:
            return [topic], topic.name
    raise HTTPException(status_code=404, detail=f"Topic not found: {topic_name}")


@router.post("/search", response_model=PaperSearchResponse)
async def search_papers(
    topic: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> PaperSearchResponse:
    config = _read_config(db)
    selected_topics, selected_topic_name = _topics_for_search(config.topics, topic)
    keywords = [keyword for topic_config in selected_topics for keyword in topic_config.keywords]
    venues = [venue for topic_config in selected_topics for venue in topic_config.venues]
    exclusions = [item for topic_config in selected_topics for item in topic_config.exclude_keywords]
    query = PaperQuery(
        keywords=keywords,
        venues=venues,
        exclude_keywords=exclusions,
        lookback_days=config.search.lookback_days,
        max_results=config.search.max_results_per_source,
    )

    warnings: list[str] = []
    saved_by_id: dict[int, Paper] = {}
    for source in default_sources():
        try:
            candidates = await source.search(query)
        except Exception as exc:
            warnings.append(_source_warning(source, exc))
            continue
        for candidate in candidates:
            match = match_paper(candidate, selected_topics)
            if match.matched:
                paper = upsert_paper(db, candidate, match)
                saved_by_id[paper.id] = paper
    db.commit()

    responses = [paper_to_response(db, paper) for paper in saved_by_id.values()]
    save_paper_search_artifacts(responses, warnings, query, topic_name=selected_topic_name)
    return PaperSearchResponse(count=len(responses), papers=responses, warnings=warnings)


@router.get("", response_model=list[PaperResponse])
def list_papers(db: Session = Depends(get_db)) -> list[PaperResponse]:
    papers = db.scalars(select(Paper).order_by(Paper.created_at.desc())).all()
    return [paper_to_response(db, paper) for paper in papers]
