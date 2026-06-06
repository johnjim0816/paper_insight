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

    keywords: Mapped[list["TopicKeyword"]] = relationship(
        back_populates="topic",
        cascade="all, delete-orphan",
        order_by="TopicKeyword.id",
    )
    venues: Mapped[list["TopicVenue"]] = relationship(
        back_populates="topic",
        cascade="all, delete-orphan",
        order_by="TopicVenue.id",
    )
    exclusions: Mapped[list["TopicExclusion"]] = relationship(
        back_populates="topic",
        cascade="all, delete-orphan",
        order_by="TopicExclusion.id",
    )


class TopicKeyword(Base):
    __tablename__ = "topic_keywords"
    __table_args__ = (UniqueConstraint("topic_id", "value"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    value: Mapped[str] = mapped_column(String(240))

    topic: Mapped[Topic] = relationship(back_populates="keywords")


class TopicVenue(Base):
    __tablename__ = "topic_venues"
    __table_args__ = (UniqueConstraint("topic_id", "value"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    value: Mapped[str] = mapped_column(String(240))

    topic: Mapped[Topic] = relationship(back_populates="venues")


class TopicExclusion(Base):
    __tablename__ = "topic_exclusions"
    __table_args__ = (UniqueConstraint("topic_id", "value"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    value: Mapped[str] = mapped_column(String(240))

    topic: Mapped[Topic] = relationship(back_populates="exclusions")


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


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_date: Mapped[str] = mapped_column(String(20), unique=True, index=True)
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


class DeliveryLog(Base):
    __tablename__ = "delivery_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(40))
    report_id: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(40))
    response: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
