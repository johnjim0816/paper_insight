from dataclasses import dataclass

from app.schemas import TopicConfig
from app.services.paper_sources.base import PaperCandidate


@dataclass(frozen=True)
class MatchResult:
    matched: bool
    topic_names: list[str]
    reasons: list[str]


def _contains(text: str, needle: str) -> bool:
    return needle.lower() in text.lower()


def match_paper(paper: PaperCandidate, topics: list[TopicConfig]) -> MatchResult:
    text = " ".join([paper.title, paper.abstract or "", paper.venue or ""])
    reasons: list[str] = []
    topic_names: list[str] = []

    for topic in topics:
        for exclusion in topic.exclude_keywords:
            if _contains(text, exclusion):
                return MatchResult(matched=False, topic_names=[], reasons=[f"excluded: {exclusion}"])

        topic_matched = False
        for keyword in topic.keywords:
            if _contains(text, keyword):
                topic_matched = True
                reasons.append(f"keyword: {keyword}")

        for venue in topic.venues:
            if paper.venue and _contains(paper.venue, venue):
                topic_matched = True
                reasons.append(f"venue: {venue}")

        if topic_matched:
            topic_names.append(topic.name)

    return MatchResult(
        matched=bool(topic_names),
        topic_names=list(dict.fromkeys(topic_names)),
        reasons=list(dict.fromkeys(reasons)),
    )
