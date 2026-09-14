from datetime import datetime
from typing import Any, Literal
import uuid

from pydantic import BaseModel, Field


class MetricSnapshot(BaseModel):
    events_per_second: int
    p99_latency_ms: float
    consumer_lag: int
    buffer_usage_percent: float
    active_incidents: int


class TelemetryPoint(BaseModel):
    timestamp: datetime
    events_per_second: int
    latency_ms: float


class PipelineNode(BaseModel):
    id: str
    label: str
    kind: Literal["source", "queue", "processor", "sink"]
    status: Literal["healthy", "processing", "warning", "paused"]
    detail: str


class OverviewResponse(BaseModel):
    metrics: MetricSnapshot
    points: list[TelemetryPoint]
    nodes: list[PipelineNode]
    stream_status: Literal["running", "paused"]
    generated_at: datetime


class PipelineResource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    kind: Literal["source", "consumer"]
    protocol: Literal["Kafka", "Redis", "Postgres CDC", "Webhook"]
    status: Literal["healthy", "processing", "warning", "paused"]
    partitions: int
    messages_per_second: int
    lag: int
    retention_days: int
    updated_at: datetime


class PipelineCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    kind: Literal["source", "consumer"]
    protocol: Literal["Kafka", "Redis", "Postgres CDC", "Webhook"]
    partitions: int = Field(default=3, ge=1, le=128)
    retention_days: int = Field(default=7, ge=1, le=365)


class EventRecord(BaseModel):
    id: str
    timestamp: datetime
    level: Literal["INFO", "WARN", "ERROR", "CRITICAL"]
    source: str
    topic: str
    partition: int
    offset: int
    event_type: str
    message: str
    payload: dict[str, Any]


class Alert(BaseModel):
    id: str
    title: str
    severity: Literal["P1", "P2", "P3"]
    status: Literal["active", "acknowledged", "resolved"]
    summary: str
    affected_stage: str
    created_at: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    resolution_note: str | None = None
    operator: str | None = None


class ResolutionNote(BaseModel):
    resolution_note: str = Field(min_length=3, max_length=500)


class StreamState(BaseModel):
    status: Literal["running", "paused"]
    updated_at: datetime


class IntegrationSummary(BaseModel):
    id: str
    kind: Literal["kafka", "redis", "timescaledb"]
    name: str
    endpoint: str
    topic_or_database: str
    security_mode: str
    credential_state: Literal["placeholder", "configured"]
    enabled: bool
    test_status: Literal["not_tested", "passed", "failed"]
    last_tested_at: datetime | None = None


class IntegrationWrite(BaseModel):
    kind: Literal["kafka", "redis", "timescaledb"]
    name: str = Field(min_length=2, max_length=80)
    endpoint: str = Field(min_length=3, max_length=300)
    topic_or_database: str = Field(default="", max_length=120)
    security_mode: str = Field(default="TLS", max_length=40)
    credential_state: Literal["placeholder", "configured"] = "placeholder"
    enabled: bool = True


class IntegrationTestResult(BaseModel):
    id: str
    kind: Literal["kafka", "redis", "timescaledb"]
    ok: bool
    mocked: bool
    detail: str
