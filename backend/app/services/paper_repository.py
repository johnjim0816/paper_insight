import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Paper, PaperMatch
from app.schemas import PaperResponse
from app.services.dedup import dedup_key
from app.services.matching import MatchResult
from app.services.paper_sources.base import PaperCandidate


def upsert_paper(db: Session, candidate: PaperCandidate, match: MatchResult) -> Paper:
    key = dedup_key(candidate)
    paper = db.scalar(select(Paper).where(Paper.dedup_key == key))
    if paper is None:
        paper = Paper(dedup_key=key)

    paper.source = candidate.source
    paper.source_id = candidate.source_id
    paper.title = candidate.title
    paper.abstract = candidate.abstract
    paper.authors = json.dumps(candidate.authors, ensure_ascii=False)
    paper.venue = candidate.venue
    paper.published_at = candidate.published_at
    paper.url = candidate.url
    paper.doi = candidate.doi
    paper.arxiv_id = candidate.arxiv_id
    paper.semantic_scholar_id = candidate.semantic_scholar_id
    paper.citation_count = candidate.citation_count
    db.add(paper)
    db.flush()

    for topic_name in match.topic_names:
        existing = db.scalar(
            select(PaperMatch).where(PaperMatch.paper_id == paper.id, PaperMatch.topic_name == topic_name)
        )
        if existing is None:
            existing = PaperMatch(paper_id=paper.id, topic_name=topic_name)
        existing.reasons = json.dumps(match.reasons, ensure_ascii=False)
        db.add(existing)

    return paper


def paper_to_response(db: Session, paper: Paper) -> PaperResponse:
    matches = db.scalars(select(PaperMatch).where(PaperMatch.paper_id == paper.id)).all()
    reasons: list[str] = []
    topic_names: list[str] = []
    for match in matches:
        topic_names.append(match.topic_name)
        reasons.extend(json.loads(match.reasons))

    return PaperResponse(
        id=paper.id,
        dedup_key=paper.dedup_key,
        source=paper.source,
        title=paper.title,
        abstract=paper.abstract,
        authors=json.loads(paper.authors),
        venue=paper.venue,
        published_at=paper.published_at,
        url=paper.url,
        doi=paper.doi,
        arxiv_id=paper.arxiv_id,
        semantic_scholar_id=paper.semantic_scholar_id,
        citation_count=paper.citation_count,
        topic_names=list(dict.fromkeys(topic_names)),
        match_reasons=list(dict.fromkeys(reasons)),
    )
