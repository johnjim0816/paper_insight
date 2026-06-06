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
