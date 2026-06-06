import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.config import _read_config
from app.db.models import Paper
from app.db.session import get_db
from app.schemas import PaperResponse, PaperSearchResponse
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
        return f"{source.__class__.__name__}: HTTP {exc.response.status_code}"

    message = str(exc).strip().splitlines()[0] if str(exc).strip() else exc.__class__.__name__
    return f"{source.__class__.__name__}: {message}"


@router.post("/search", response_model=PaperSearchResponse)
async def search_papers(db: Session = Depends(get_db)) -> PaperSearchResponse:
    config = _read_config(db)
    keywords = [keyword for topic in config.topics for keyword in topic.keywords]
    venues = [venue for topic in config.topics for venue in topic.venues]
    exclusions = [item for topic in config.topics for item in topic.exclude_keywords]
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
            match = match_paper(candidate, config.topics)
            if match.matched:
                paper = upsert_paper(db, candidate, match)
                saved_by_id[paper.id] = paper
    db.commit()

    responses = [paper_to_response(db, paper) for paper in saved_by_id.values()]
    return PaperSearchResponse(count=len(responses), papers=responses, warnings=warnings)


@router.get("", response_model=list[PaperResponse])
def list_papers(db: Session = Depends(get_db)) -> list[PaperResponse]:
    papers = db.scalars(select(Paper).order_by(Paper.created_at.desc())).all()
    return [paper_to_response(db, paper) for paper in papers]
