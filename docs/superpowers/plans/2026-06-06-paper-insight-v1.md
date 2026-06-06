# Paper Insight V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local React + FastAPI application that searches papers by configured keywords and venues, generates a GPT-assisted Chinese daily report, and sends it to the user's own Feishu account.

**Architecture:** The backend owns persistence, paper source adapters, report generation, summarization, and Feishu delivery. The frontend is a Vite React single-page app that edits configuration, runs searches, views papers and reports, and triggers Feishu test or report sends. Scheduling stays outside the app; Codex automation or another scheduler calls `POST /api/reports/generate-and-send`.

**Tech Stack:** React, Vite, TypeScript, FastAPI, SQLAlchemy, SQLite, httpx, pytest, Vitest, OpenAI-compatible chat completions, Feishu custom app bot APIs.

---

## File Structure

Create and maintain these project areas:

- `backend/pyproject.toml`: Python package metadata and dev dependencies.
- `backend/app/main.py`: FastAPI application factory, CORS, router mounting, and startup database initialization.
- `backend/app/core/config.py`: environment settings and non-secret defaults.
- `backend/app/db/models.py`: SQLAlchemy tables for topics, papers, reports, and delivery logs.
- `backend/app/db/session.py`: engine, session maker, and database initialization.
- `backend/app/schemas.py`: Pydantic request and response shapes shared by API routers.
- `backend/app/api/config.py`: configuration read and update endpoints.
- `backend/app/api/papers.py`: paper search and listing endpoints.
- `backend/app/api/reports.py`: report generation, retrieval, and send endpoints.
- `backend/app/api/delivery.py`: Feishu test send endpoint.
- `backend/app/services/matching.py`: keyword, venue, exclusion, and match-reason logic.
- `backend/app/services/dedup.py`: stable paper deduplication keys.
- `backend/app/services/paper_sources/base.py`: source adapter protocol and shared data classes.
- `backend/app/services/paper_sources/arxiv.py`: arXiv API adapter.
- `backend/app/services/paper_sources/semantic_scholar.py`: Semantic Scholar API adapter.
- `backend/app/services/paper_repository.py`: persistence helpers for papers and matches.
- `backend/app/services/report_builder.py`: report selection and Markdown/rich-text content building.
- `backend/app/services/summarizer.py`: OpenAI-compatible summary client and fallback behavior.
- `backend/app/services/feishu.py`: Feishu token retrieval and message delivery.
- `backend/app/jobs/generate_report.py`: orchestration entrypoint for search, summary, report save, and delivery.
- `backend/tests/`: backend unit and API tests.
- `frontend/package.json`: frontend scripts and dependencies.
- `frontend/src/api/client.ts`: typed API client.
- `frontend/src/types.ts`: frontend data types.
- `frontend/src/App.tsx`: app shell and page routing state.
- `frontend/src/pages/*.tsx`: dashboard, configuration, papers, reports, delivery test pages.
- `frontend/src/styles.css`: application styles.
- `.env.example`: required backend secrets and local defaults.
- `.gitignore`: Python, Node, local database, and environment ignores.
- `README.md`: local setup, run commands, Feishu setup, and Codex automation command.

## Task 1: Backend Skeleton, Settings, And Health Check

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/db/__init__.py`
- Create: `backend/app/db/session.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`
- Create: `.gitignore`
- Create: `.env.example`

- [ ] **Step 1: Write the health check test**

Create `backend/tests/test_health.py`:

```python
def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Write the test client fixture**

Create `backend/tests/conftest.py`:

```python
import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_paper_insight.db")
os.environ.setdefault("OPENAI_MODEL", "gpt-4.1-mini")

from app.main import app
from app.db.session import Base, engine


@pytest.fixture(autouse=True)
def reset_database() -> Iterator[None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
```

- [ ] **Step 3: Run the failing test**

Run:

```bash
cd backend
python -m pytest tests/test_health.py -v
```

Expected: import or endpoint failure because the backend application does not exist yet.

- [ ] **Step 4: Add backend package and dependencies**

Create `backend/pyproject.toml`:

```toml
[project]
name = "paper-insight-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.30.0",
  "sqlalchemy>=2.0.0",
  "pydantic-settings>=2.4.0",
  "httpx>=0.27.0",
  "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0.0",
  "pytest-asyncio>=0.23.0",
]

[tool.pytest.ini_options]
pythonpath = ["."]
asyncio_mode = "auto"
```

Create empty package files:

```text
backend/app/__init__.py
backend/app/core/__init__.py
backend/app/db/__init__.py
```

- [ ] **Step 5: Add environment settings**

Create `backend/app/core/config.py`:

```python
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./paper_insight.db"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4.1-mini"
    feishu_app_id: str | None = None
    feishu_app_secret: str | None = None
    feishu_recipient_id: str | None = None
    feishu_recipient_id_type: str = Field(default="email", pattern="^(email|open_id|user_id)$")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 6: Add database session helpers**

Create `backend/app/db/session.py`:

```python
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    import app.db.models

    Base.metadata.create_all(bind=engine)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 7: Add FastAPI app**

Create `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import init_db

app = FastAPI(title="Paper Insight API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 8: Add local ignores and environment example**

Create `.gitignore`:

```gitignore
.DS_Store
.env
*.db
*.sqlite
__pycache__/
.pytest_cache/
.venv/
node_modules/
dist/
coverage/
```

Create `.env.example`:

```env
DATABASE_URL=sqlite:///./paper_insight.db
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
FEISHU_APP_ID=
FEISHU_APP_SECRET=
FEISHU_RECIPIENT_ID=
FEISHU_RECIPIENT_ID_TYPE=email
```

- [ ] **Step 9: Run the health check test**

Run:

```bash
cd backend
python -m pytest tests/test_health.py -v
```

Expected: `1 passed`.

- [ ] **Step 10: Commit**

```bash
git add .gitignore .env.example backend
git commit -m "feat: add FastAPI backend skeleton"
```

## Task 2: Database Models And Configuration API

**Files:**
- Create: `backend/app/db/models.py`
- Create: `backend/app/schemas.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/config.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_config_api.py`

- [ ] **Step 1: Write configuration API tests**

Create `backend/tests/test_config_api.py`:

```python
def test_get_default_config(client):
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert data["search"]["lookback_days"] == 7
    assert data["search"]["max_results_per_source"] == 30
    assert data["delivery"]["provider"] == "feishu"
    assert data["topics"] == []


def test_save_and_read_config(client):
    payload = {
        "topics": [
            {
                "name": "llm_agents",
                "keywords": ["LLM agent", "tool use"],
                "venues": ["ICLR", "NeurIPS"],
                "exclude_keywords": ["survey"],
            }
        ],
        "search": {"lookback_days": 3, "max_results_per_source": 12},
        "summary": {"language": "zh"},
        "delivery": {"provider": "feishu", "mode": "app_bot", "recipient_id_type": "email"},
    }

    put_response = client.put("/api/config", json=payload)
    assert put_response.status_code == 200
    assert put_response.json()["topics"][0]["name"] == "llm_agents"

    get_response = client.get("/api/config")
    assert get_response.status_code == 200
    assert get_response.json() == put_response.json()
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd backend
python -m pytest tests/test_config_api.py -v
```

Expected: FAIL because `/api/config` is not mounted.

- [ ] **Step 3: Add SQLAlchemy models**

Create `backend/app/db/models.py`:

```python
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    keywords: Mapped[list["TopicKeyword"]] = relationship(cascade="all, delete-orphan")
    venues: Mapped[list["TopicVenue"]] = relationship(cascade="all, delete-orphan")
    exclusions: Mapped[list["TopicExclusion"]] = relationship(cascade="all, delete-orphan")


class TopicKeyword(Base):
    __tablename__ = "topic_keywords"
    __table_args__ = (UniqueConstraint("topic_id", "value"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    value: Mapped[str] = mapped_column(String(240))


class TopicVenue(Base):
    __tablename__ = "topic_venues"
    __table_args__ = (UniqueConstraint("topic_id", "value"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    value: Mapped[str] = mapped_column(String(240))


class TopicExclusion(Base):
    __tablename__ = "topic_exclusions"
    __table_args__ = (UniqueConstraint("topic_id", "value"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    value: Mapped[str] = mapped_column(String(240))


class AppConfig(Base):
    __tablename__ = "app_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    lookback_days: Mapped[int] = mapped_column(Integer, default=7)
    max_results_per_source: Mapped[int] = mapped_column(Integer, default=30)
    summary_language: Mapped[str] = mapped_column(String(16), default="zh")
    delivery_provider: Mapped[str] = mapped_column(String(40), default="feishu")
    delivery_mode: Mapped[str] = mapped_column(String(40), default="app_bot")
    recipient_id_type: Mapped[str] = mapped_column(String(40), default="email")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
```

- [ ] **Step 4: Add Pydantic schemas**

Create `backend/app/schemas.py`:

```python
from pydantic import BaseModel, Field


class TopicConfig(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    keywords: list[str] = Field(default_factory=list)
    venues: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)


class SearchConfig(BaseModel):
    lookback_days: int = Field(default=7, ge=1, le=60)
    max_results_per_source: int = Field(default=30, ge=1, le=100)


class SummaryConfig(BaseModel):
    language: str = "zh"


class DeliveryConfig(BaseModel):
    provider: str = "feishu"
    mode: str = "app_bot"
    recipient_id_type: str = Field(default="email", pattern="^(email|open_id|user_id)$")


class AppConfigPayload(BaseModel):
    topics: list[TopicConfig] = Field(default_factory=list)
    search: SearchConfig = Field(default_factory=SearchConfig)
    summary: SummaryConfig = Field(default_factory=SummaryConfig)
    delivery: DeliveryConfig = Field(default_factory=DeliveryConfig)
```

- [ ] **Step 5: Add configuration API**

Create `backend/app/api/__init__.py`:

```python
```

Create `backend/app/api/config.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import AppConfig, Topic, TopicExclusion, TopicKeyword, TopicVenue, utc_now
from app.db.session import get_db
from app.schemas import AppConfigPayload, DeliveryConfig, SearchConfig, SummaryConfig, TopicConfig

router = APIRouter(prefix="/api/config", tags=["config"])


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


def _read_config(db: Session) -> AppConfigPayload:
    config = db.get(AppConfig, 1)
    if config is None:
        config = AppConfig(id=1)
        db.add(config)
        db.commit()
        db.refresh(config)

    topics = []
    for topic in db.scalars(select(Topic).order_by(Topic.name)).all():
        topics.append(
            TopicConfig(
                name=topic.name,
                keywords=[item.value for item in topic.keywords],
                venues=[item.value for item in topic.venues],
                exclude_keywords=[item.value for item in topic.exclusions],
            )
        )

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
    db.execute(delete(Topic))
    config = db.get(AppConfig, 1) or AppConfig(id=1)
    config.lookback_days = payload.search.lookback_days
    config.max_results_per_source = payload.search.max_results_per_source
    config.summary_language = payload.summary.language
    config.delivery_provider = payload.delivery.provider
    config.delivery_mode = payload.delivery.mode
    config.recipient_id_type = payload.delivery.recipient_id_type
    config.updated_at = utc_now()
    db.add(config)

    for topic_payload in payload.topics:
        topic = Topic(name=topic_payload.name.strip())
        topic.keywords = [TopicKeyword(value=value) for value in _clean(topic_payload.keywords)]
        topic.venues = [TopicVenue(value=value) for value in _clean(topic_payload.venues)]
        topic.exclusions = [TopicExclusion(value=value) for value in _clean(topic_payload.exclude_keywords)]
        db.add(topic)

    db.commit()
    return _read_config(db)
```

- [ ] **Step 6: Mount the router**

Modify `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.config import router as config_router
from app.db.session import init_db

app = FastAPI(title="Paper Insight API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(config_router)
```

- [ ] **Step 7: Run tests**

Run:

```bash
cd backend
python -m pytest tests/test_health.py tests/test_config_api.py -v
```

Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add backend
git commit -m "feat: add configuration API"
```

## Task 3: Paper Matching And Deduplication

**Files:**
- Modify: `backend/app/schemas.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/paper_sources/__init__.py`
- Create: `backend/app/services/paper_sources/base.py`
- Create: `backend/app/services/matching.py`
- Create: `backend/app/services/dedup.py`
- Create: `backend/tests/test_matching.py`
- Create: `backend/tests/test_dedup.py`

- [ ] **Step 1: Write matching tests**

Create `backend/tests/test_matching.py`:

```python
from app.schemas import TopicConfig
from app.services.matching import match_paper
from app.services.paper_sources.base import PaperCandidate


def test_matches_keyword_and_venue():
    topic = TopicConfig(
        name="agents",
        keywords=["tool use"],
        venues=["ICLR"],
        exclude_keywords=[],
    )
    paper = PaperCandidate(
        source="arxiv",
        source_id="1234.5678",
        title="Tool Use Improves Agent Planning",
        abstract="A method for language model planning.",
        authors=["A. User"],
        venue="ICLR",
        published_at="2026-06-05",
        url="https://arxiv.org/abs/1234.5678",
        doi=None,
        arxiv_id="1234.5678",
        semantic_scholar_id=None,
        citation_count=None,
    )

    result = match_paper(paper, [topic])

    assert result.matched is True
    assert result.topic_names == ["agents"]
    assert "keyword: tool use" in result.reasons
    assert "venue: ICLR" in result.reasons


def test_exclusion_removes_paper():
    topic = TopicConfig(
        name="agents",
        keywords=["agent"],
        venues=[],
        exclude_keywords=["survey"],
    )
    paper = PaperCandidate(
        source="arxiv",
        source_id="9999.0000",
        title="A Survey of Agent Planning",
        abstract="Survey paper.",
        authors=[],
        venue=None,
        published_at=None,
        url="https://arxiv.org/abs/9999.0000",
        doi=None,
        arxiv_id="9999.0000",
        semantic_scholar_id=None,
        citation_count=None,
    )

    result = match_paper(paper, [topic])

    assert result.matched is False
    assert result.reasons == ["excluded: survey"]
```

- [ ] **Step 2: Write deduplication tests**

Create `backend/tests/test_dedup.py`:

```python
from app.services.dedup import dedup_key, normalize_title
from app.services.paper_sources.base import PaperCandidate


def make_paper(**overrides):
    data = {
        "source": "arxiv",
        "source_id": "src-1",
        "title": "  Tool Use   For Agents! ",
        "abstract": None,
        "authors": [],
        "venue": None,
        "published_at": None,
        "url": "https://example.com",
        "doi": None,
        "arxiv_id": None,
        "semantic_scholar_id": None,
        "citation_count": None,
    }
    data.update(overrides)
    return PaperCandidate(**data)


def test_normalize_title():
    assert normalize_title("  Tool Use   For Agents! ") == "tool use for agents"


def test_prefers_doi():
    assert dedup_key(make_paper(doi="10.1000/ABC")) == "doi:10.1000/abc"


def test_prefers_arxiv_after_doi():
    assert dedup_key(make_paper(arxiv_id="2401.12345")) == "arxiv:2401.12345"


def test_falls_back_to_title_hash():
    assert dedup_key(make_paper()).startswith("title:")
```

- [ ] **Step 3: Run tests to verify failure**

Run:

```bash
cd backend
python -m pytest tests/test_matching.py tests/test_dedup.py -v
```

Expected: FAIL because matching and deduplication services do not exist.

- [ ] **Step 4: Add paper source data classes**

Create `backend/app/services/__init__.py`:

```python
```

Create `backend/app/services/paper_sources/__init__.py`:

```python
```

Create `backend/app/services/paper_sources/base.py`:

```python
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
```

- [ ] **Step 5: Add matching service**

Create `backend/app/services/matching.py`:

```python
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

    unique_reasons = list(dict.fromkeys(reasons))
    unique_topics = list(dict.fromkeys(topic_names))
    return MatchResult(matched=bool(unique_topics), topic_names=unique_topics, reasons=unique_reasons)
```

- [ ] **Step 6: Add deduplication service**

Create `backend/app/services/dedup.py`:

```python
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
```

- [ ] **Step 7: Run tests**

Run:

```bash
cd backend
python -m pytest tests/test_matching.py tests/test_dedup.py -v
```

Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add backend
git commit -m "feat: add paper matching and deduplication"
```

## Task 4: Paper Source Adapters

**Files:**
- Create: `backend/app/services/paper_sources/arxiv.py`
- Create: `backend/app/services/paper_sources/semantic_scholar.py`
- Create: `backend/tests/test_paper_sources.py`

- [ ] **Step 1: Write paper source adapter tests**

Create `backend/tests/test_paper_sources.py`:

```python
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

    result = await ArxivSource().search(PaperQuery(["agent"], [], [], 7, 5))

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
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd backend
python -m pytest tests/test_paper_sources.py -v
```

Expected: FAIL because source adapters do not exist.

- [ ] **Step 3: Implement arXiv adapter**

Create `backend/app/services/paper_sources/arxiv.py`:

```python
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus
from xml.etree import ElementTree

import httpx

from app.services.paper_sources.base import PaperCandidate, PaperQuery

ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"


class ArxivSource:
    base_url = "https://export.arxiv.org/api/query"

    async def search(self, query: PaperQuery) -> list[PaperCandidate]:
        search_terms = [f'all:"{term}"' for term in query.keywords]
        if query.venues:
            search_terms.extend(f'all:"{venue}"' for venue in query.venues)
        search_query = " OR ".join(search_terms) or "all:machine learning"

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                self.base_url,
                params={
                    "search_query": search_query,
                    "start": 0,
                    "max_results": query.max_results,
                    "sortBy": "submittedDate",
                    "sortOrder": "descending",
                },
            )
            response.raise_for_status()

        cutoff = datetime.now(timezone.utc) - timedelta(days=query.lookback_days)
        root = ElementTree.fromstring(response.text)
        papers: list[PaperCandidate] = []

        for entry in root.findall(f"{ATOM}entry"):
            published_text = entry.findtext(f"{ATOM}published")
            published_at = published_text[:10] if published_text else None
            if published_text:
                published_dt = datetime.fromisoformat(published_text.replace("Z", "+00:00"))
                if published_dt < cutoff:
                    continue

            entry_id = entry.findtext(f"{ATOM}id") or ""
            arxiv_id = entry_id.rsplit("/", 1)[-1].replace("v1", "")
            authors = [node.findtext(f"{ATOM}name") or "" for node in entry.findall(f"{ATOM}author")]
            link_node = entry.find(f"{ATOM}link")
            url = link_node.attrib.get("href") if link_node is not None else entry_id

            papers.append(
                PaperCandidate(
                    source="arxiv",
                    source_id=arxiv_id,
                    title=" ".join((entry.findtext(f"{ATOM}title") or "").split()),
                    abstract=" ".join((entry.findtext(f"{ATOM}summary") or "").split()),
                    authors=[author for author in authors if author],
                    venue=None,
                    published_at=published_at,
                    url=url,
                    doi=entry.findtext(f"{ARXIV}doi"),
                    arxiv_id=arxiv_id,
                    semantic_scholar_id=None,
                    citation_count=None,
                )
            )

        return papers
```

- [ ] **Step 4: Implement Semantic Scholar adapter**

Create `backend/app/services/paper_sources/semantic_scholar.py`:

```python
import httpx

from app.services.paper_sources.base import PaperCandidate, PaperQuery


class SemanticScholarSource:
    base_url = "https://api.semanticscholar.org/graph/v1/paper/search"

    async def search(self, query: PaperQuery) -> list[PaperCandidate]:
        text_query = " ".join(query.keywords + query.venues).strip() or "machine learning"
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                self.base_url,
                params={
                    "query": text_query,
                    "limit": query.max_results,
                    "fields": "paperId,title,abstract,authors,venue,year,url,citationCount,externalIds",
                },
            )
            response.raise_for_status()

        papers: list[PaperCandidate] = []
        for item in response.json().get("data", []):
            external_ids = item.get("externalIds") or {}
            papers.append(
                PaperCandidate(
                    source="semantic_scholar",
                    source_id=item["paperId"],
                    title=item.get("title") or "Untitled",
                    abstract=item.get("abstract"),
                    authors=[author.get("name", "") for author in item.get("authors", []) if author.get("name")],
                    venue=item.get("venue"),
                    published_at=str(item["year"]) if item.get("year") else None,
                    url=item.get("url") or f"https://www.semanticscholar.org/paper/{item['paperId']}",
                    doi=external_ids.get("DOI"),
                    arxiv_id=external_ids.get("ArXiv"),
                    semantic_scholar_id=item["paperId"],
                    citation_count=item.get("citationCount"),
                )
            )
        return papers
```

- [ ] **Step 5: Run tests**

Run:

```bash
cd backend
python -m pytest tests/test_paper_sources.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend
git commit -m "feat: add paper source adapters"
```

## Task 5: Paper Persistence And Search API

**Files:**
- Modify: `backend/app/db/models.py`
- Modify: `backend/app/schemas.py`
- Create: `backend/app/services/paper_repository.py`
- Create: `backend/app/api/papers.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_papers_api.py`

- [ ] **Step 1: Write paper search API test**

Create `backend/tests/test_papers_api.py`:

```python
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
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cd backend
python -m pytest tests/test_papers_api.py -v
```

Expected: FAIL because paper API and models do not exist.

- [ ] **Step 3: Extend models**

Append to `backend/app/db/models.py`:

```python
class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dedup_key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(80))
    source_id: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(Text)
    abstract: Mapped[str | None] = mapped_column(Text)
    authors: Mapped[str] = mapped_column(Text, default="[]")
    venue: Mapped[str | None] = mapped_column(String(240))
    published_at: Mapped[str | None] = mapped_column(String(40))
    url: Mapped[str] = mapped_column(Text)
    doi: Mapped[str | None] = mapped_column(String(240))
    arxiv_id: Mapped[str | None] = mapped_column(String(120))
    semantic_scholar_id: Mapped[str | None] = mapped_column(String(120))
    citation_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class PaperMatch(Base):
    __tablename__ = "paper_matches"
    __table_args__ = (UniqueConstraint("paper_id", "topic_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"))
    topic_name: Mapped[str] = mapped_column(String(120))
    reasons: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
```

- [ ] **Step 4: Extend schemas**

Append to `backend/app/schemas.py`:

```python
class PaperResponse(BaseModel):
    id: int
    dedup_key: str
    source: str
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
    topic_names: list[str]
    match_reasons: list[str]


class PaperSearchResponse(BaseModel):
    count: int
    papers: list[PaperResponse]
    warnings: list[str] = Field(default_factory=list)
```

- [ ] **Step 5: Add paper repository**

Create `backend/app/services/paper_repository.py`:

```python
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
```

- [ ] **Step 6: Add paper API**

Create `backend/app/api/papers.py`:

```python
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
    saved = []
    for source in default_sources():
        try:
            candidates = await source.search(query)
        except Exception as exc:
            warnings.append(f"{source.__class__.__name__}: {exc}")
            continue
        for candidate in candidates:
            match = match_paper(candidate, config.topics)
            if match.matched:
                saved.append(upsert_paper(db, candidate, match))
    db.commit()

    responses = [paper_to_response(db, paper) for paper in saved]
    return PaperSearchResponse(count=len(responses), papers=responses, warnings=warnings)


@router.get("", response_model=list[PaperResponse])
def list_papers(db: Session = Depends(get_db)) -> list[PaperResponse]:
    papers = db.scalars(select(Paper).order_by(Paper.created_at.desc())).all()
    return [paper_to_response(db, paper) for paper in papers]
```

- [ ] **Step 7: Mount paper router**

Modify `backend/app/main.py` to import and include `papers_router`:

```python
from app.api.papers import router as papers_router

app.include_router(papers_router)
```

Keep the existing config router mounted.

- [ ] **Step 8: Run tests**

Run:

```bash
cd backend
python -m pytest tests/test_papers_api.py tests/test_config_api.py tests/test_matching.py tests/test_dedup.py -v
```

Expected: all tests pass.

- [ ] **Step 9: Commit**

```bash
git add backend
git commit -m "feat: add paper search API"
```

## Task 6: Summarizer And Report Builder

**Files:**
- Modify: `backend/app/db/models.py`
- Modify: `backend/app/schemas.py`
- Create: `backend/app/services/summarizer.py`
- Create: `backend/app/services/report_builder.py`
- Create: `backend/tests/test_report_builder.py`
- Create: `backend/tests/test_summarizer.py`

- [ ] **Step 1: Write report builder test**

Create `backend/tests/test_report_builder.py`:

```python
from app.schemas import PaperResponse
from app.services.report_builder import build_report_markdown


def test_build_report_markdown_groups_papers():
    papers = [
        PaperResponse(
            id=1,
            dedup_key="doi:1",
            source="fake",
            title="Tool Use for Agents",
            abstract="Abstract",
            authors=["Alice"],
            venue="ICLR",
            published_at="2026-06-05",
            url="https://example.com",
            doi="10.1000/1",
            arxiv_id=None,
            semantic_scholar_id=None,
            citation_count=2,
            topic_names=["agents"],
            match_reasons=["keyword: agents"],
        )
    ]
    summaries = {1: "一句话结论：这篇论文值得优先阅读。"}

    markdown = build_report_markdown("2026-06-06", papers, summaries)

    assert "# Paper Insight Daily Report - 2026-06-06" in markdown
    assert "## Worth Reading First" in markdown
    assert "Tool Use for Agents" in markdown
    assert "一句话结论" in markdown
```

- [ ] **Step 2: Write summarizer fallback test**

Create `backend/tests/test_summarizer.py`:

```python
import pytest

from app.schemas import PaperResponse
from app.services.summarizer import summarize_paper


class BrokenClient:
    async def post(self, url, headers=None, json=None):
        raise RuntimeError("network down")


@pytest.mark.asyncio
async def test_summarizer_fallback_on_failure():
    paper = PaperResponse(
        id=1,
        dedup_key="doi:1",
        source="fake",
        title="Tool Use for Agents",
        abstract=None,
        authors=[],
        venue=None,
        published_at=None,
        url="https://example.com",
        doi=None,
        arxiv_id=None,
        semantic_scholar_id=None,
        citation_count=None,
        topic_names=["agents"],
        match_reasons=["keyword: agents"],
    )

    result = await summarize_paper(paper, api_key="key", base_url="https://api.example.com/v1", model="model", client=BrokenClient())

    assert "摘要生成失败" in result
    assert "Tool Use for Agents" in result
```

- [ ] **Step 3: Run tests to verify failure**

Run:

```bash
cd backend
python -m pytest tests/test_report_builder.py tests/test_summarizer.py -v
```

Expected: FAIL because report builder and summarizer do not exist.

- [ ] **Step 4: Add report models**

Append to `backend/app/db/models.py`:

```python
class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_date: Mapped[str] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(String(240))
    markdown: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ReportItem(Base):
    __tablename__ = "report_items"
    __table_args__ = (UniqueConstraint("report_id", "paper_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"))
    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"))
    summary: Mapped[str] = mapped_column(Text)
```

- [ ] **Step 5: Add report schemas**

Append to `backend/app/schemas.py`:

```python
class ReportResponse(BaseModel):
    id: int
    report_date: str
    title: str
    markdown: str
```

- [ ] **Step 6: Implement report builder**

Create `backend/app/services/report_builder.py`:

```python
from collections import defaultdict

from app.schemas import PaperResponse


def build_report_markdown(report_date: str, papers: list[PaperResponse], summaries: dict[int, str]) -> str:
    lines = [
        f"# Paper Insight Daily Report - {report_date}",
        "",
        "## Worth Reading First",
        "",
    ]

    for paper in papers[:3]:
        lines.extend(
            [
                f"- [{paper.title}]({paper.url})",
                f"  - {summaries.get(paper.id, '暂无摘要')}",
            ]
        )

    grouped: dict[str, list[PaperResponse]] = defaultdict(list)
    for paper in papers:
        for topic in paper.topic_names or ["unclassified"]:
            grouped[topic].append(paper)

    lines.extend(["", "## Papers By Topic", ""])
    for topic, topic_papers in grouped.items():
        lines.extend([f"### {topic}", ""])
        for paper in topic_papers:
            meta = " | ".join(item for item in [paper.venue, paper.published_at, paper.source] if item)
            lines.extend(
                [
                    f"- **[{paper.title}]({paper.url})**",
                    f"  - Metadata: {meta or 'unknown'}",
                    f"  - Match: {', '.join(paper.match_reasons) or 'matched'}",
                    f"  - Summary: {summaries.get(paper.id, '暂无摘要')}",
                ]
            )

    return "\n".join(lines).strip() + "\n"
```

- [ ] **Step 7: Implement summarizer**

Create `backend/app/services/summarizer.py`:

```python
import httpx

from app.schemas import PaperResponse


def _fallback_summary(paper: PaperResponse, reason: str) -> str:
    return f"摘要生成失败，已保留元数据：{paper.title}。原因：{reason}"


async def summarize_paper(
    paper: PaperResponse,
    api_key: str | None,
    base_url: str,
    model: str,
    client: httpx.AsyncClient | None = None,
) -> str:
    if not api_key:
        return _fallback_summary(paper, "OPENAI_API_KEY is missing")

    prompt = (
        "请用中文总结这篇论文，包含一句话结论、研究问题、方法亮点、"
        "以及它为什么匹配用户关注方向。控制在 180 字以内。\n\n"
        f"Title: {paper.title}\n"
        f"Abstract: {paper.abstract or 'No abstract'}\n"
        f"Venue: {paper.venue or 'Unknown'}\n"
        f"Match reasons: {', '.join(paper.match_reasons)}"
    )
    close_client = client is None
    active_client = client or httpx.AsyncClient(timeout=40.0)
    try:
        response = await active_client.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You summarize academic papers for a Chinese research daily report."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        return _fallback_summary(paper, str(exc))
    finally:
        if close_client:
            await active_client.aclose()
```

- [ ] **Step 8: Run tests**

Run:

```bash
cd backend
python -m pytest tests/test_report_builder.py tests/test_summarizer.py -v
```

Expected: all tests pass.

- [ ] **Step 9: Commit**

```bash
git add backend
git commit -m "feat: add report builder and summarizer"
```

## Task 7: Report Generation Job And Reports API

**Files:**
- Create: `backend/app/jobs/__init__.py`
- Create: `backend/app/jobs/generate_report.py`
- Create: `backend/app/api/reports.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_reports_api.py`

- [ ] **Step 1: Write reports API test**

Create `backend/tests/test_reports_api.py`:

```python
from app.db.models import Paper, PaperMatch


def seed_paper(db):
    paper = Paper(
        dedup_key="doi:10.1000/report",
        source="fake",
        source_id="fake-1",
        title="Tool Use for Agents",
        abstract="Agent abstract",
        authors='["Alice"]',
        venue="ICLR",
        published_at="2026-06-05",
        url="https://example.com",
        doi="10.1000/report",
        arxiv_id=None,
        semantic_scholar_id=None,
        citation_count=1,
    )
    db.add(paper)
    db.flush()
    db.add(PaperMatch(paper_id=paper.id, topic_name="agents", reasons='["keyword: agents"]'))
    db.commit()


def test_generate_and_read_report(client, monkeypatch):
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        seed_paper(db)

    async def fake_summary(paper, api_key, base_url, model):
        return "一句话结论：值得阅读。"

    monkeypatch.setattr("app.jobs.generate_report.summarize_paper", fake_summary)

    response = client.post("/api/reports/generate")

    assert response.status_code == 200
    report = response.json()
    assert "Paper Insight Daily Report" in report["markdown"]

    list_response = client.get("/api/reports")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cd backend
python -m pytest tests/test_reports_api.py -v
```

Expected: FAIL because report API does not exist.

- [ ] **Step 3: Add report generation job**

Create `backend/app/jobs/__init__.py`:

```python
```

Create `backend/app/jobs/generate_report.py`:

```python
from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Paper, Report, ReportItem
from app.schemas import ReportResponse
from app.services.paper_repository import paper_to_response
from app.services.report_builder import build_report_markdown
from app.services.summarizer import summarize_paper


async def generate_report(db: Session, report_date: str | None = None) -> ReportResponse:
    settings = get_settings()
    target_date = report_date or date.today().isoformat()
    papers = db.scalars(select(Paper).order_by(Paper.created_at.desc()).limit(20)).all()
    paper_responses = [paper_to_response(db, paper) for paper in papers]

    summaries: dict[int, str] = {}
    for paper in paper_responses:
        summaries[paper.id] = await summarize_paper(
            paper,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
        )

    markdown = build_report_markdown(target_date, paper_responses, summaries)
    existing = db.scalar(select(Report).where(Report.report_date == target_date))
    if existing is not None:
        db.execute(delete(ReportItem).where(ReportItem.report_id == existing.id))
        report = existing
    else:
        report = Report(report_date=target_date, title=f"Paper Insight Daily Report - {target_date}", markdown="")

    report.markdown = markdown
    db.add(report)
    db.flush()

    for paper in paper_responses:
        db.add(ReportItem(report_id=report.id, paper_id=paper.id, summary=summaries[paper.id]))

    db.commit()
    db.refresh(report)
    return ReportResponse(id=report.id, report_date=report.report_date, title=report.title, markdown=report.markdown)
```

- [ ] **Step 4: Add reports API**

Create `backend/app/api/reports.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Report
from app.db.session import get_db
from app.jobs.generate_report import generate_report
from app.schemas import ReportResponse

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _to_response(report: Report) -> ReportResponse:
    return ReportResponse(id=report.id, report_date=report.report_date, title=report.title, markdown=report.markdown)


@router.post("/generate", response_model=ReportResponse)
async def generate(db: Session = Depends(get_db)) -> ReportResponse:
    return await generate_report(db)


@router.get("", response_model=list[ReportResponse])
def list_reports(db: Session = Depends(get_db)) -> list[ReportResponse]:
    reports = db.scalars(select(Report).order_by(Report.created_at.desc())).all()
    return [_to_response(report) for report in reports]


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db)) -> ReportResponse:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return _to_response(report)
```

- [ ] **Step 5: Mount reports router**

Modify `backend/app/main.py` to import and include `reports_router`:

```python
from app.api.reports import router as reports_router

app.include_router(reports_router)
```

Keep existing routers mounted.

- [ ] **Step 6: Run tests**

Run:

```bash
cd backend
python -m pytest tests/test_reports_api.py tests/test_report_builder.py tests/test_summarizer.py -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend
git commit -m "feat: add report generation API"
```

## Task 8: Feishu Delivery

**Files:**
- Modify: `backend/app/db/models.py`
- Modify: `backend/app/schemas.py`
- Create: `backend/app/services/feishu.py`
- Create: `backend/app/api/delivery.py`
- Modify: `backend/app/api/reports.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_feishu.py`

- [ ] **Step 1: Write Feishu tests**

Create `backend/tests/test_feishu.py`:

```python
import pytest

from app.services.feishu import FeishuClient, FeishuSettings


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeHttpClient:
    def __init__(self):
        self.posts = []

    async def post(self, url, json=None, headers=None):
        self.posts.append((url, json, headers))
        if "tenant_access_token" in url:
            return FakeResponse({"code": 0, "tenant_access_token": "token-1"})
        return FakeResponse({"code": 0, "data": {"message_id": "msg-1"}})


@pytest.mark.asyncio
async def test_feishu_sends_message():
    http_client = FakeHttpClient()
    client = FeishuClient(
        FeishuSettings(
            app_id="cli_x",
            app_secret="secret",
            recipient_id="me@example.com",
            recipient_id_type="email",
        ),
        http_client=http_client,
    )

    result = await client.send_report("hello")

    assert result == "msg-1"
    assert len(http_client.posts) == 2
    assert http_client.posts[1][1]["receive_id"] == "me@example.com"
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cd backend
python -m pytest tests/test_feishu.py -v
```

Expected: FAIL because Feishu service does not exist.

- [ ] **Step 3: Add delivery log model**

Append to `backend/app/db/models.py`:

```python
class DeliveryLog(Base):
    __tablename__ = "delivery_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(40))
    report_id: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(40))
    response: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
```

- [ ] **Step 4: Add delivery schemas**

Append to `backend/app/schemas.py`:

```python
class DeliveryResponse(BaseModel):
    status: str
    message_id: str | None = None
    detail: str | None = None
```

- [ ] **Step 5: Implement Feishu client**

Create `backend/app/services/feishu.py`:

```python
from dataclasses import dataclass
import json

import httpx


@dataclass(frozen=True)
class FeishuSettings:
    app_id: str
    app_secret: str
    recipient_id: str
    recipient_id_type: str


class FeishuClient:
    token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    message_url = "https://open.feishu.cn/open-apis/im/v1/messages"

    def __init__(self, settings: FeishuSettings, http_client: httpx.AsyncClient | None = None):
        self.settings = settings
        self.http_client = http_client

    async def _post(self, url: str, json: dict, headers: dict | None = None):
        if self.http_client is not None:
            return await self.http_client.post(url, json=json, headers=headers)
        async with httpx.AsyncClient(timeout=20.0) as client:
            return await client.post(url, json=json, headers=headers)

    async def tenant_access_token(self) -> str:
        response = await self._post(
            self.token_url,
            json={"app_id": self.settings.app_id, "app_secret": self.settings.app_secret},
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != 0:
            raise RuntimeError(str(payload))
        return payload["tenant_access_token"]

    async def send_report(self, markdown: str) -> str:
        token = await self.tenant_access_token()
        response = await self._post(
            f"{self.message_url}?receive_id_type={self.settings.recipient_id_type}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "receive_id": self.settings.recipient_id,
                "msg_type": "post",
                "content": _markdown_to_post(markdown),
            },
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != 0:
            raise RuntimeError(str(payload))
        return payload["data"]["message_id"]


def _markdown_to_post(markdown: str) -> str:
    lines = []
    for line in markdown.splitlines():
        if not line.strip():
            continue
        lines.append([{"tag": "text", "text": line}])
    return json.dumps({
        "zh_cn": {
            "title": "Paper Insight Daily Report",
            "content": lines[:80],
        }
    }, ensure_ascii=False)
```

- [ ] **Step 6: Add delivery API and report send endpoints**

Create `backend/app/api/delivery.py`:

```python
from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas import DeliveryResponse
from app.services.feishu import FeishuClient, FeishuSettings

router = APIRouter(prefix="/api/delivery", tags=["delivery"])


def _feishu_client() -> FeishuClient:
    settings = get_settings()
    missing = [
        name
        for name, value in {
            "FEISHU_APP_ID": settings.feishu_app_id,
            "FEISHU_APP_SECRET": settings.feishu_app_secret,
            "FEISHU_RECIPIENT_ID": settings.feishu_recipient_id,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing Feishu settings: {', '.join(missing)}")
    return FeishuClient(
        FeishuSettings(
            app_id=settings.feishu_app_id or "",
            app_secret=settings.feishu_app_secret or "",
            recipient_id=settings.feishu_recipient_id or "",
            recipient_id_type=settings.feishu_recipient_id_type,
        )
    )


@router.post("/feishu/test", response_model=DeliveryResponse)
async def test_feishu() -> DeliveryResponse:
    message_id = await _feishu_client().send_report("# Paper Insight\nFeishu test message")
    return DeliveryResponse(status="sent", message_id=message_id)
```

Modify `backend/app/api/reports.py` to add:

```python
from app.api.delivery import _feishu_client
from app.db.models import DeliveryLog
from app.schemas import DeliveryResponse


def _record_delivery(db: Session, report_id: int | None, status: str, response: str) -> None:
    db.add(DeliveryLog(provider="feishu", report_id=report_id, status=status, response=response))
    db.commit()


@router.post("/{report_id}/send", response_model=DeliveryResponse)
async def send_report(report_id: int, db: Session = Depends(get_db)) -> DeliveryResponse:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    try:
        message_id = await _feishu_client().send_report(report.markdown)
    except Exception as exc:
        _record_delivery(db, report_id, "failed", str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    _record_delivery(db, report_id, "sent", message_id)
    return DeliveryResponse(status="sent", message_id=message_id)


@router.post("/generate-and-send", response_model=DeliveryResponse)
async def generate_and_send(db: Session = Depends(get_db)) -> DeliveryResponse:
    report = await generate_report(db)
    try:
        message_id = await _feishu_client().send_report(report.markdown)
    except Exception as exc:
        _record_delivery(db, report.id, "failed", str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    _record_delivery(db, report.id, "sent", message_id)
    return DeliveryResponse(status="sent", message_id=message_id)
```

- [ ] **Step 7: Mount delivery router**

Modify `backend/app/main.py` to import and include `delivery_router`:

```python
from app.api.delivery import router as delivery_router

app.include_router(delivery_router)
```

Keep existing routers mounted.

- [ ] **Step 8: Run tests**

Run:

```bash
cd backend
python -m pytest tests/test_feishu.py tests/test_reports_api.py -v
```

Expected: all tests pass.

- [ ] **Step 9: Commit**

```bash
git add backend
git commit -m "feat: add Feishu delivery"
```

## Task 9: Frontend Skeleton And API Client

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/types.ts`
- Create: `frontend/src/styles.css`
- Create: `frontend/src/App.test.tsx`

- [ ] **Step 1: Add frontend package**

Create `frontend/package.json`:

```json
{
  "scripts": {
    "dev": "vite --host 127.0.0.1",
    "build": "tsc && vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^5.4.0",
    "typescript": "^5.5.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "lucide-react": "^0.468.0"
  },
  "devDependencies": {
    "@testing-library/react": "^16.0.0",
    "@testing-library/jest-dom": "^6.4.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "jsdom": "^25.0.0",
    "vitest": "^2.0.0"
  }
}
```

- [ ] **Step 2: Add Vite config files**

Create `frontend/index.html`:

```html
<div id="root"></div>
<script type="module" src="/src/main.tsx"></script>
```

Create `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"]
}
```

Create `frontend/vite.config.ts`:

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: []
  }
});
```

- [ ] **Step 3: Add frontend types and API client**

Create `frontend/src/types.ts`:

```ts
export type TopicConfig = {
  name: string;
  keywords: string[];
  venues: string[];
  exclude_keywords: string[];
};

export type AppConfig = {
  topics: TopicConfig[];
  search: { lookback_days: number; max_results_per_source: number };
  summary: { language: string };
  delivery: { provider: string; mode: string; recipient_id_type: string };
};

export type Paper = {
  id: number;
  dedup_key: string;
  source: string;
  title: string;
  abstract: string | null;
  authors: string[];
  venue: string | null;
  published_at: string | null;
  url: string;
  match_reasons: string[];
  topic_names: string[];
};

export type Report = {
  id: number;
  report_date: string;
  title: string;
  markdown: string;
};
```

Create `frontend/src/api/client.ts`:

```ts
import type { AppConfig, Paper, Report } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const requestOptions = Object.assign({}, options, {
    headers: Object.assign({ "Content-Type": "application/json" }, options?.headers ?? {})
  });
  const response = await fetch(`${API_BASE}${path}`, requestOptions);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export const api = {
  getConfig: () => request<AppConfig>("/api/config"),
  saveConfig: (config: AppConfig) => request<AppConfig>("/api/config", { method: "PUT", body: JSON.stringify(config) }),
  searchPapers: () => request<{ count: number; papers: Paper[]; warnings: string[] }>("/api/papers/search", { method: "POST" }),
  listPapers: () => request<Paper[]>("/api/papers"),
  generateReport: () => request<Report>("/api/reports/generate", { method: "POST" }),
  generateAndSend: () => request<{ status: string; message_id?: string }>("/api/reports/generate-and-send", { method: "POST" }),
  listReports: () => request<Report[]>("/api/reports"),
  sendFeishuTest: () => request<{ status: string; message_id?: string }>("/api/delivery/feishu/test", { method: "POST" })
};
```

- [ ] **Step 4: Add app shell**

Create `frontend/src/App.tsx`:

```tsx
import { BookOpen, FileText, Home, Send, Settings } from "lucide-react";
import { useState } from "react";
import "./styles.css";

type Page = "dashboard" | "config" | "papers" | "reports" | "delivery";

const nav: { key: Page; label: string; icon: React.ComponentType<{ size?: number }> }[] = [
  { key: "dashboard", label: "Dashboard", icon: Home },
  { key: "config", label: "Config", icon: Settings },
  { key: "papers", label: "Papers", icon: BookOpen },
  { key: "reports", label: "Reports", icon: FileText },
  { key: "delivery", label: "Feishu", icon: Send }
];

export default function App() {
  const [page, setPage] = useState<Page>("dashboard");

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>Paper Insight</h1>
        <nav>
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <button key={item.key} className={page === item.key ? "active" : ""} onClick={() => setPage(item.key)}>
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>
      <main className="content">
        <section className="page-header">
          <h2>{nav.find((item) => item.key === page)?.label}</h2>
        </section>
        <section className="panel">Page ready: {page}</section>
      </main>
    </div>
  );
}
```

Create `frontend/src/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 5: Add styles**

Create `frontend/src/styles.css`:

```css
:root {
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #1f2933;
  background: #f6f7f9;
}

body {
  margin: 0;
}

button {
  font: inherit;
}

.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 240px 1fr;
}

.sidebar {
  background: #17202a;
  color: white;
  padding: 24px 16px;
}

.sidebar h1 {
  font-size: 20px;
  margin: 0 8px 24px;
}

.sidebar nav {
  display: grid;
  gap: 6px;
}

.sidebar button {
  align-items: center;
  background: transparent;
  border: 0;
  border-radius: 8px;
  color: #d9e2ec;
  cursor: pointer;
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  text-align: left;
}

.sidebar button.active,
.sidebar button:hover {
  background: #2f3d4a;
  color: white;
}

.content {
  padding: 28px;
}

.page-header h2 {
  font-size: 24px;
  margin: 0 0 18px;
}

.panel {
  background: white;
  border: 1px solid #d9e2ec;
  border-radius: 8px;
  padding: 18px;
}
```

- [ ] **Step 6: Add smoke test**

Create `frontend/src/App.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import App from "./App";

test("renders app shell", () => {
  render(<App />);
  expect(screen.getByText("Paper Insight")).toBeInTheDocument();
  expect(screen.getByText("Dashboard")).toBeInTheDocument();
});
```

- [ ] **Step 7: Run frontend tests**

Run:

```bash
cd frontend
npm install
npm test
npm run build
```

Expected: tests pass and build succeeds.

- [ ] **Step 8: Commit**

```bash
git add frontend
git commit -m "feat: add React frontend shell"
```

## Task 10: Frontend Pages And Workflow Actions

**Files:**
- Create: `frontend/src/pages/DashboardPage.tsx`
- Create: `frontend/src/pages/ConfigPage.tsx`
- Create: `frontend/src/pages/PapersPage.tsx`
- Create: `frontend/src/pages/ReportsPage.tsx`
- Create: `frontend/src/pages/DeliveryPage.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/styles.css`
- Create: `frontend/src/pages/ConfigPage.test.tsx`

- [ ] **Step 1: Write configuration page test**

Create `frontend/src/pages/ConfigPage.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { ConfigPage } from "./ConfigPage";

test("renders config controls", () => {
  render(<ConfigPage />);
  expect(screen.getByLabelText("Topic name")).toBeInTheDocument();
  expect(screen.getByLabelText("Keywords")).toBeInTheDocument();
  expect(screen.getByLabelText("Venues")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cd frontend
npm test -- ConfigPage.test.tsx
```

Expected: FAIL because `ConfigPage` does not exist.

- [ ] **Step 3: Add page components**

Create `frontend/src/pages/DashboardPage.tsx`:

```tsx
import { api } from "../api/client";

export function DashboardPage() {
  return (
    <div className="stack">
      <div className="panel">
        <h3>Daily workflow</h3>
        <button onClick={() => api.searchPapers()}>Search papers</button>
        <button onClick={() => api.generateReport()}>Generate report</button>
        <button onClick={() => api.generateAndSend()}>Generate and send</button>
      </div>
    </div>
  );
}
```

Create `frontend/src/pages/ConfigPage.tsx`:

```tsx
import { useState } from "react";
import { api } from "../api/client";
import type { AppConfig } from "../types";

const initialConfig: AppConfig = {
  topics: [{ name: "", keywords: [], venues: [], exclude_keywords: [] }],
  search: { lookback_days: 7, max_results_per_source: 30 },
  summary: { language: "zh" },
  delivery: { provider: "feishu", mode: "app_bot", recipient_id_type: "email" }
};

function splitLines(value: string): string[] {
  return value.split("\n").map((item) => item.trim()).filter(Boolean);
}

export function ConfigPage() {
  const [config, setConfig] = useState<AppConfig>(initialConfig);
  const topic = config.topics[0];
  const updateTopic = (patch: Partial<typeof topic>) => {
    setConfig(Object.assign({}, config, { topics: [Object.assign({}, topic, patch)] }));
  };

  return (
    <form className="panel stack" onSubmit={(event) => { event.preventDefault(); api.saveConfig(config); }}>
      <label>
        Topic name
        <input
          aria-label="Topic name"
          value={topic.name}
          onChange={(event) => updateTopic({ name: event.target.value })}
        />
      </label>
      <label>
        Keywords
        <textarea
          aria-label="Keywords"
          value={topic.keywords.join("\n")}
          onChange={(event) => updateTopic({ keywords: splitLines(event.target.value) })}
        />
      </label>
      <label>
        Venues
        <textarea
          aria-label="Venues"
          value={topic.venues.join("\n")}
          onChange={(event) => updateTopic({ venues: splitLines(event.target.value) })}
        />
      </label>
      <label>
        Exclude keywords
        <textarea
          aria-label="Exclude keywords"
          value={topic.exclude_keywords.join("\n")}
          onChange={(event) => updateTopic({ exclude_keywords: splitLines(event.target.value) })}
        />
      </label>
      <button type="submit">Save config</button>
    </form>
  );
}
```

Create `frontend/src/pages/PapersPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Paper } from "../types";

export function PapersPage() {
  const [papers, setPapers] = useState<Paper[]>([]);

  useEffect(() => {
    api.listPapers().then(setPapers).catch(() => setPapers([]));
  }, []);

  return (
    <div className="stack">
      {papers.map((paper) => (
        <article className="panel" key={paper.id}>
          <h3><a href={paper.url}>{paper.title}</a></h3>
          <p>{paper.venue ?? paper.source}</p>
          <p>{paper.match_reasons.join(", ")}</p>
        </article>
      ))}
    </div>
  );
}
```

Create `frontend/src/pages/ReportsPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Report } from "../types";

export function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);

  useEffect(() => {
    api.listReports().then(setReports).catch(() => setReports([]));
  }, []);

  return (
    <div className="stack">
      {reports.map((report) => (
        <article className="panel" key={report.id}>
          <h3>{report.title}</h3>
          <pre>{report.markdown}</pre>
        </article>
      ))}
    </div>
  );
}
```

Create `frontend/src/pages/DeliveryPage.tsx`:

```tsx
import { useState } from "react";
import { api } from "../api/client";

export function DeliveryPage() {
  const [status, setStatus] = useState("Not tested");

  return (
    <div className="panel stack">
      <h3>Feishu delivery</h3>
      <p>{status}</p>
      <button
        onClick={() => api.sendFeishuTest().then((result) => setStatus(`Sent: ${result.message_id ?? "ok"}`)).catch((error) => setStatus(error.message))}
      >
        Send test message
      </button>
    </div>
  );
}
```

- [ ] **Step 4: Wire pages into app shell**

Modify `frontend/src/App.tsx`:

```tsx
import { BookOpen, FileText, Home, Send, Settings } from "lucide-react";
import { useState } from "react";
import { ConfigPage } from "./pages/ConfigPage";
import { DashboardPage } from "./pages/DashboardPage";
import { DeliveryPage } from "./pages/DeliveryPage";
import { PapersPage } from "./pages/PapersPage";
import { ReportsPage } from "./pages/ReportsPage";
import "./styles.css";

type Page = "dashboard" | "config" | "papers" | "reports" | "delivery";

const nav: { key: Page; label: string; icon: React.ComponentType<{ size?: number }> }[] = [
  { key: "dashboard", label: "Dashboard", icon: Home },
  { key: "config", label: "Config", icon: Settings },
  { key: "papers", label: "Papers", icon: BookOpen },
  { key: "reports", label: "Reports", icon: FileText },
  { key: "delivery", label: "Feishu", icon: Send }
];

function renderPage(page: Page) {
  if (page === "config") return <ConfigPage />;
  if (page === "papers") return <PapersPage />;
  if (page === "reports") return <ReportsPage />;
  if (page === "delivery") return <DeliveryPage />;
  return <DashboardPage />;
}

export default function App() {
  const [page, setPage] = useState<Page>("dashboard");

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>Paper Insight</h1>
        <nav>
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <button key={item.key} className={page === item.key ? "active" : ""} onClick={() => setPage(item.key)}>
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>
      <main className="content">
        <section className="page-header">
          <h2>{nav.find((item) => item.key === page)?.label}</h2>
        </section>
        {renderPage(page)}
      </main>
    </div>
  );
}
```

- [ ] **Step 5: Extend styles**

Append to `frontend/src/styles.css`:

```css
.stack {
  display: grid;
  gap: 14px;
}

label {
  display: grid;
  gap: 6px;
  font-weight: 600;
}

input,
textarea {
  border: 1px solid #bcccdc;
  border-radius: 6px;
  font: inherit;
  padding: 9px 10px;
}

textarea {
  min-height: 96px;
  resize: vertical;
}

.panel button,
form button {
  background: #0f6f72;
  border: 0;
  border-radius: 6px;
  color: white;
  cursor: pointer;
  padding: 9px 12px;
}

pre {
  background: #f0f4f8;
  border-radius: 6px;
  overflow: auto;
  padding: 12px;
  white-space: pre-wrap;
}
```

- [ ] **Step 6: Run frontend tests and build**

Run:

```bash
cd frontend
npm test
npm run build
```

Expected: tests pass and build succeeds.

- [ ] **Step 7: Commit**

```bash
git add frontend
git commit -m "feat: add frontend workflow pages"
```

## Task 11: Local Documentation And Full Verification

**Files:**
- Create: `README.md`
- Modify: `.env.example`

- [ ] **Step 1: Write README**

Create `README.md`:

```markdown
# Paper Insight

Paper Insight is a local-first paper monitoring app. It lets you configure research keywords and venues, search recent papers, generate a Chinese daily report with GPT, and send the report to yourself through a Feishu custom app bot.

## Local Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp ../.env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Feishu Setup

Create a Feishu custom app, enable bot capability, and make sure your account is in the app availability scope. Configure:

```env
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
FEISHU_RECIPIENT_ID=your_email@example.com
FEISHU_RECIPIENT_ID_TYPE=email
```

If email delivery fails in your tenant, switch `FEISHU_RECIPIENT_ID_TYPE` to `open_id` or `user_id` and set `FEISHU_RECIPIENT_ID` accordingly.

## Codex Automation Command

Run the full daily workflow:

```bash
curl -X POST http://127.0.0.1:8000/api/reports/generate-and-send
```

## Tests

```bash
cd backend
python -m pytest -v

cd ../frontend
npm test
npm run build
```
```

- [ ] **Step 2: Run backend test suite**

Run:

```bash
cd backend
python -m pytest -v
```

Expected: all backend tests pass.

- [ ] **Step 3: Run frontend test and build**

Run:

```bash
cd frontend
npm test
npm run build
```

Expected: frontend tests pass and build succeeds.

- [ ] **Step 4: Start backend locally**

Run:

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Expected: FastAPI starts and `GET http://127.0.0.1:8000/api/health` returns `{"status":"ok"}`.

- [ ] **Step 5: Start frontend locally**

Run:

```bash
cd frontend
npm run dev
```

Expected: Vite starts at `http://127.0.0.1:5173`.

- [ ] **Step 6: Verify core API smoke path**

Run:

```bash
curl -s http://127.0.0.1:8000/api/health
curl -s -X PUT http://127.0.0.1:8000/api/config \
  -H 'Content-Type: application/json' \
  -d '{"topics":[{"name":"agents","keywords":["LLM agent"],"venues":["ICLR"],"exclude_keywords":["survey"]}],"search":{"lookback_days":7,"max_results_per_source":5},"summary":{"language":"zh"},"delivery":{"provider":"feishu","mode":"app_bot","recipient_id_type":"email"}}'
curl -s -X POST http://127.0.0.1:8000/api/papers/search
curl -s -X POST http://127.0.0.1:8000/api/reports/generate
```

Expected: health returns OK, config save returns the topic, search returns a `count`, and report generation returns Markdown.

- [ ] **Step 7: Verify Feishu delivery when secrets are configured**

Run:

```bash
curl -s -X POST http://127.0.0.1:8000/api/delivery/feishu/test
```

Expected with valid Feishu credentials: JSON response has `"status":"sent"` and a `message_id`. Expected without credentials: backend returns a clear missing settings error.

- [ ] **Step 8: Commit**

```bash
git add README.md .env.example
git commit -m "docs: add local setup instructions"
```

## Self-Review Checklist

- Spec coverage: Tasks cover local React + FastAPI setup, SQLite persistence, keyword and venue configuration, arXiv and Semantic Scholar adapters, GPT summaries, report generation, Feishu app bot private delivery, external scheduling endpoint, and local verification.
- Scope: V1 excludes multi-user auth, cloud deployment, worker queues, OpenReview, DBLP, Crossref, Feishu event subscriptions, and Feishu interactive command handling.
- Type consistency: API paths use `/api/config`, `/api/papers/search`, `/api/papers`, `/api/reports/generate`, `/api/reports/generate-and-send`, `/api/reports/{report_id}/send`, and `/api/delivery/feishu/test` throughout.
- Execution order: Each task produces testable software and ends with a commit.
