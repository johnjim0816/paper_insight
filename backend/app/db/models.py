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
