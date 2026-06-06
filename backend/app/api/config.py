from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import AppConfig, Topic, TopicExclusion, TopicKeyword, TopicVenue, utc_now
from app.db.session import get_db
from app.schemas import AppConfigPayload, DeliveryConfig, SearchConfig, SummaryConfig, TopicConfig

router = APIRouter(prefix="/api/config", tags=["config"])

DEFAULT_TOPICS = [
    TopicConfig(
        name="llm_agents",
        keywords=["LLM agent", "tool use", "autonomous agents"],
        venues=["ICLR", "NeurIPS", "ACL"],
        exclude_keywords=["survey"],
    )
]


def _clean(values: list[str]) -> list[str]:
    seen: set[str] = set()
    cleaned: list[str] = []
    for raw in values:
        value = raw.strip()
        key = value.lower()
        if value and key not in seen:
            seen.add(key)
            cleaned.append(value)
    return cleaned


def _topic_statement():
    return (
        select(Topic)
        .options(selectinload(Topic.keywords), selectinload(Topic.venues), selectinload(Topic.exclusions))
        .order_by(Topic.name)
    )


def _topic_to_config(topic: Topic) -> TopicConfig:
    return TopicConfig(
        name=topic.name,
        keywords=[item.value for item in topic.keywords],
        venues=[item.value for item in topic.venues],
        exclude_keywords=[item.value for item in topic.exclusions],
    )


def _read_topics(db: Session) -> list[TopicConfig]:
    return [_topic_to_config(topic) for topic in db.scalars(_topic_statement()).all()]


def _seed_default_topics(db: Session) -> None:
    for topic_payload in DEFAULT_TOPICS:
        topic = Topic(name=topic_payload.name)
        topic.keywords = [TopicKeyword(value=value) for value in topic_payload.keywords]
        topic.venues = [TopicVenue(value=value) for value in topic_payload.venues]
        topic.exclusions = [TopicExclusion(value=value) for value in topic_payload.exclude_keywords]
        db.add(topic)


def _read_config(db: Session) -> AppConfigPayload:
    config = db.get(AppConfig, 1)
    changed = False
    if config is None:
        config = AppConfig(id=1)
        db.add(config)
        db.flush()
        changed = True

    topics = _read_topics(db)
    if not topics:
        _seed_default_topics(db)
        changed = True

    if changed:
        db.commit()
        db.refresh(config)
        topics = _read_topics(db)

    return AppConfigPayload(
        topics=topics,
        search=SearchConfig(
            lookback_days=config.lookback_days,
            max_results_per_source=config.max_results_per_source,
        ),
        summary=SummaryConfig(language=config.summary_language),
        delivery=DeliveryConfig(
            provider=config.delivery_provider,
            mode=config.delivery_mode,
            recipient_id_type=config.recipient_id_type,
        ),
    )


@router.get("", response_model=AppConfigPayload)
def get_config(db: Session = Depends(get_db)) -> AppConfigPayload:
    return _read_config(db)


@router.put("", response_model=AppConfigPayload)
def update_config(payload: AppConfigPayload, db: Session = Depends(get_db)) -> AppConfigPayload:
    for topic in db.scalars(select(Topic)).all():
        db.delete(topic)

    config = db.get(AppConfig, 1) or AppConfig(id=1)
    config.lookback_days = payload.search.lookback_days
    config.max_results_per_source = payload.search.max_results_per_source
    config.summary_language = payload.summary.language
    config.delivery_provider = payload.delivery.provider
    config.delivery_mode = payload.delivery.mode
    config.recipient_id_type = payload.delivery.recipient_id_type
    config.updated_at = utc_now()
    db.add(config)

    seen_topics: set[str] = set()
    for topic_payload in payload.topics:
        topic_name = topic_payload.name.strip()
        topic_key = topic_name.lower()
        if not topic_name or topic_key in seen_topics:
            continue
        seen_topics.add(topic_key)
        topic = Topic(name=topic_name)
        topic.keywords = [TopicKeyword(value=value) for value in _clean(topic_payload.keywords)]
        topic.venues = [TopicVenue(value=value) for value in _clean(topic_payload.venues)]
        topic.exclusions = [TopicExclusion(value=value) for value in _clean(topic_payload.exclude_keywords)]
        db.add(topic)

    db.commit()
    return _read_config(db)
