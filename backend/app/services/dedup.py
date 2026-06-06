import hashlib
import re

from app.services.paper_sources.base import PaperCandidate


def normalize_title(title: str) -> str:
    lowered = title.lower().strip()
    without_punctuation = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return re.sub(r"\s+", " ", without_punctuation).strip()


def dedup_key(paper: PaperCandidate) -> str:
    if paper.doi:
        return f"doi:{paper.doi.lower().strip()}"
    if paper.arxiv_id:
        return f"arxiv:{paper.arxiv_id.lower().strip()}"
    if paper.semantic_scholar_id:
        return f"s2:{paper.semantic_scholar_id.lower().strip()}"
    digest = hashlib.sha256(normalize_title(paper.title).encode("utf-8")).hexdigest()[:16]
    return f"title:{digest}"
