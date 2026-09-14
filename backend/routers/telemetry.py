import math
import time
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pymongo import ReturnDocument

from lib.db import db
from models.telemetry import (
    Alert,
    EventRecord,
    IntegrationSummary,
    IntegrationTestResult,
    IntegrationWrite,
    OverviewResponse,
    PipelineCreate,
    PipelineResource,
    ResolutionNote,
    StreamState,
    TelemetryPoint,
)

router = APIRouter()

DEMO_PIPELINES = [
    {"id": "src-orders", "name": "orders.ingress", "kind": "source", "protocol": "Kafka", "status": "healthy", "partitions": 12, "messages_per_second": 842, "lag": 0, "retention_days": 14},
    {"id": "src-webhooks", "name": "partner.webhooks", "kind": "source", "protocol": "Webhook", "status": "processing", "partitions": 4, "messages_per_second": 216, "lag": 38, "retention_days": 3},
    {"id": "consumer-enrich", "name": "enrichment-worker", "kind": "consumer", "protocol": "Kafka", "status": "healthy", "partitions": 8, "messages_per_second": 790, "lag": 12, "retention_days": 7},
    {"id": "consumer-cache", "name": "realtime-cache", "kind": "consumer", "protocol": "Redis", "status": "warning", "partitions": 2, "messages_per_second": 490, "lag": 184, "retention_days": 1},
    {"id": "consumer-archive", "name": "telemetry-archive", "kind": "consumer", "protocol": "Postgres CDC", "status": "healthy", "partitions": 6, "messages_per_second": 615, "lag": 4, "retention_days": 90},
]

DEMO_ALERTS = [
    {"id": "alert-lag", "title": "Consumer lag above threshold", "severity": "P1", "status": "active", "summary": "realtime-cache is 184 messages behind its committed offset.", "affected_stage": "Consumer / cache", "created_at": datetime.now(timezone.utc) - timedelta(minutes=8)},
    {"id": "alert-webhook", "title": "Webhook burst detected", "severity": "P2", "status": "acknowledged", "summary": "partner.webhooks exceeded its normal 5-minute event baseline.", "affected_stage": "Source / webhook ingress", "created_at": datetime.now(timezone.utc) - timedelta(minutes=23), "acknowledged_at": datetime.now(timezone.utc) - timedelta(minutes=19), "operator": "ops@streampulse"},
    {"id": "alert-latency", "title": "P99 processing latency drift", "severity": "P3", "status": "resolved", "summary": "Enrichment latency returned to baseline after worker rebalance.", "affected_stage": "Processor / enrichment", "created_at": datetime.now(timezone.utc) - timedelta(hours=2), "acknowledged_at": datetime.now(timezone.utc) - timedelta(hours=1, minutes=55), "resolved_at": datetime.now(timezone.utc) - timedelta(hours=1, minutes=42), "resolution_note": "Rebalanced enrichment workers and cleared the hot partition.", "operator": "ops@streampulse"},
]

DEMO_INTEGRATIONS = [
    {"id": "integration-kafka", "kind": "kafka", "name": "Kafka cluster", "endpoint": "kafka.example.internal:9092", "topic_or_database": "telemetry.events", "security_mode": "SASL_SSL", "credential_state": "placeholder", "enabled": True, "test_status": "not_tested"},
    {"id": "integration-redis", "kind": "redis", "name": "Redis cache", "endpoint": "rediss://redis.example.internal:6380", "topic_or_database": "telemetry-cache", "security_mode": "TLS", "credential_state": "placeholder", "enabled": True, "test_status": "not_tested"},
    {"id": "integration-timescale", "kind": "timescaledb", "name": "TimescaleDB archive", "endpoint": "postgresql://timescale.example.internal:5432/telemetry", "topic_or_database": "telemetry", "security_mode": "verify-full", "credential_state": "placeholder", "enabled": True, "test_status": "not_tested"},
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def ensure_collection_data() -> None:
    if await db.pipeline_resources.count_documents({}) == 0:
        now = utc_now()
        await db.pipeline_resources.insert_many([{**item, "updated_at": now} for item in DEMO_PIPELINES])
    if await db.alerts.count_documents({}) == 0:
        await db.alerts.insert_many(DEMO_ALERTS)
    if await db.integrations.count_documents({}) == 0:
        await db.integrations.insert_many(DEMO_INTEGRATIONS)


async def get_stream_status() -> str:
    state = await db.stream_state.find_one({"id": "global"})
    if not state:
        await db.stream_state.insert_one({"id": "global", "status": "running", "updated_at": utc_now()})
        return "running"
    return state["status"]


@router.get("/overview", response_model=OverviewResponse)
async def get_overview() -> OverviewResponse:
    await ensure_collection_data()
    now = utc_now()
    tick = time.time()
    stream_status = await get_stream_status()
    active_incidents = await db.alerts.count_documents({"status": {"$in": ["active", "acknowledged"]}})
    throughput = 1180 if stream_status == "paused" else int(1210 + math.sin(tick / 4) * 86)
    latency = 0 if stream_status == "paused" else round(82 + math.sin(tick / 6) * 9, 1)
    points = [TelemetryPoint(timestamp=now - timedelta(minutes=18 - index), events_per_second=int(1120 + math.sin((tick / 10) + index) * 90), latency_ms=round(74 + math.cos((tick / 11) + index) * 11, 1)) for index in range(18)]
    nodes = [
        {"id": "source", "label": "INGRESS", "kind": "source", "status": "healthy", "detail": "1.06k evt/s"},
        {"id": "queue", "label": "KAFKA QUEUE", "kind": "queue", "status": "processing" if stream_status == "running" else "paused", "detail": "12 partitions"},
        {"id": "processor", "label": "WORKERS", "kind": "processor", "status": "healthy", "detail": "8 active"},
        {"id": "sink", "label": "TIMESCALEDB", "kind": "sink", "status": "healthy", "detail": "615 rows/s"},
    ]
    return OverviewResponse(metrics={"events_per_second": throughput, "p99_latency_ms": latency, "consumer_lag": 238 if stream_status == "running" else 238, "buffer_usage_percent": 42.6 if stream_status == "running" else 48.1, "active_incidents": active_incidents}, points=points, nodes=nodes, stream_status=stream_status, generated_at=now)


@router.get("/pipelines", response_model=list[PipelineResource])
async def get_pipelines() -> list[PipelineResource]:
    await ensure_collection_data()
    rows = await db.pipeline_resources.find().sort("kind", 1).to_list(100)
    return [PipelineResource(**row) for row in rows]


@router.post("/pipelines", response_model=PipelineResource)
async def create_pipeline(input: PipelineCreate) -> PipelineResource:
    pipeline = PipelineResource(**input.model_dump(), status="processing", messages_per_second=0, lag=0, updated_at=utc_now())
    await db.pipeline_resources.insert_one(pipeline.model_dump())
    return pipeline


@router.get("/events", response_model=list[EventRecord])
async def get_events() -> list[EventRecord]:
    now = utc_now()
    templates = [
        ("INFO", "orders.ingress", "order.created", "Accepted order event into partition 08", {"order_id": "ord_8f21c", "amount": 149.2, "currency": "USD"}),
        ("INFO", "enrichment-worker", "profile.enriched", "Customer profile enrichment completed", {"customer_id": "cus_2d91a", "attributes": 14, "duration_ms": 21}),
        ("WARN", "realtime-cache", "cache.backpressure", "Cache writer is approaching lag threshold", {"lag": 184, "threshold": 150, "retry_in_ms": 500}),
        ("ERROR", "partner.webhooks", "webhook.retry", "Partner endpoint returned 503; retry scheduled", {"provider": "acme-partner", "attempt": 2, "status": 503}),
        ("INFO", "telemetry-archive", "batch.committed", "Batch committed to hypertable telemetry_events", {"rows": 512, "batch_id": "batch_44b0"}),
    ]
    offset = int(time.time() / 2)
    return [EventRecord(id=f"evt-{offset - index}", timestamp=now - timedelta(seconds=index * 3), level=template[0], source=template[1], topic="telemetry.events", partition=(offset - index) % 12, offset=offset - index, event_type=template[2], message=template[3], payload=template[4]) for index, template in enumerate(templates)]


@router.get("/alerts", response_model=list[Alert])
async def get_alerts() -> list[Alert]:
    await ensure_collection_data()
    rows = await db.alerts.find().sort("created_at", -1).to_list(100)
    return [Alert(**row) for row in rows]


@router.post("/alerts/{alert_id}/acknowledge", response_model=Alert)
async def acknowledge_alert(alert_id: str) -> Alert:
    updated = await db.alerts.find_one_and_update({"id": alert_id, "status": "active"}, {"$set": {"status": "acknowledged", "acknowledged_at": utc_now(), "operator": "ops@streampulse"}}, return_document=ReturnDocument.AFTER)
    if not updated:
        raise HTTPException(status_code=404, detail="Active alert not found")
    return Alert(**updated)


@router.post("/alerts/{alert_id}/resolve", response_model=Alert)
async def resolve_alert(alert_id: str, input: ResolutionNote) -> Alert:
    updated = await db.alerts.find_one_and_update({"id": alert_id, "status": {"$in": ["active", "acknowledged"]}}, {"$set": {"status": "resolved", "resolved_at": utc_now(), "resolution_note": input.resolution_note, "operator": "ops@streampulse"}}, return_document=ReturnDocument.AFTER)
    if not updated:
        raise HTTPException(status_code=404, detail="Open alert not found")
    return Alert(**updated)


@router.get("/stream", response_model=StreamState)
async def get_stream() -> StreamState:
    return StreamState(status=await get_stream_status(), updated_at=utc_now())


async def set_stream(status: str) -> StreamState:
    now = utc_now()
    await db.stream_state.update_one({"id": "global"}, {"$set": {"status": status, "updated_at": now}}, upsert=True)
    return StreamState(status=status, updated_at=now)


@router.post("/stream/pause", response_model=StreamState)
async def pause_stream() -> StreamState:
    return await set_stream("paused")


@router.post("/stream/resume", response_model=StreamState)
async def resume_stream() -> StreamState:
    return await set_stream("running")


@router.get("/integrations", response_model=list[IntegrationSummary])
async def get_integrations() -> list[IntegrationSummary]:
    await ensure_collection_data()
    rows = await db.integrations.find().sort("kind", 1).to_list(20)
    return [IntegrationSummary(**row) for row in rows]


@router.post("/integrations", response_model=IntegrationSummary)
async def save_integration(input: IntegrationWrite) -> IntegrationSummary:
    integration = IntegrationSummary(id=f"integration-{uuid.uuid4().hex[:10]}", **input.model_dump(), test_status="not_tested")
    await db.integrations.insert_one(integration.model_dump())
    return integration


@router.post("/integrations/{integration_id}/test", response_model=IntegrationTestResult)
async def test_integration(integration_id: str) -> IntegrationTestResult:
    integration = await db.integrations.find_one({"id": integration_id})
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    now = utc_now()
    await db.integrations.update_one({"id": integration_id}, {"$set": {"test_status": "failed", "last_tested_at": now}})
    return IntegrationTestResult(id=integration_id, kind=integration["kind"], ok=False, mocked=True, detail="External credentials are placeholders; connection test is not active in this environment.")
