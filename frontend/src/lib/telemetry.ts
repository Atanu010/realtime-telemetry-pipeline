import { apiGet, apiPost } from "@/lib/api";

export type PipelineStatus = "healthy" | "processing" | "warning" | "paused";
export type StreamStatus = "running" | "paused";

export interface MetricSnapshot {
  events_per_second: number;
  p99_latency_ms: number;
  consumer_lag: number;
  buffer_usage_percent: number;
  active_incidents: number;
}

export interface TelemetryPoint {
  timestamp: string;
  events_per_second: number;
  latency_ms: number;
}

export interface PipelineNode {
  id: string;
  label: string;
  kind: "source" | "queue" | "processor" | "sink";
  status: PipelineStatus;
  detail: string;
}

export interface OverviewResponse {
  metrics: MetricSnapshot;
  points: TelemetryPoint[];
  nodes: PipelineNode[];
  stream_status: StreamStatus;
  generated_at: string;
}

export interface PipelineResource {
  id: string;
  name: string;
  kind: "source" | "consumer";
  protocol: "Kafka" | "Redis" | "Postgres CDC" | "Webhook";
  status: PipelineStatus;
  partitions: number;
  messages_per_second: number;
  lag: number;
  retention_days: number;
  updated_at: string;
}

export interface PipelineCreate {
  name: string;
  kind: "source" | "consumer";
  protocol: PipelineResource["protocol"];
  partitions: number;
  retention_days: number;
}

export interface EventRecord {
  id: string;
  timestamp: string;
  level: "INFO" | "WARN" | "ERROR" | "CRITICAL";
  source: string;
  topic: string;
  partition: number;
  offset: number;
  event_type: string;
  message: string;
  payload: Record<string, unknown>;
}

export interface Alert {
  id: string;
  title: string;
  severity: "P1" | "P2" | "P3";
  status: "active" | "acknowledged" | "resolved";
  summary: string;
  affected_stage: string;
  created_at: string;
  acknowledged_at?: string | null;
  resolved_at?: string | null;
  resolution_note?: string | null;
  operator?: string | null;
}

export interface StreamState {
  status: StreamStatus;
  updated_at: string;
}

export interface IntegrationSummary {
  id: string;
  kind: "kafka" | "redis" | "timescaledb";
  name: string;
  endpoint: string;
  topic_or_database: string;
  security_mode: string;
  credential_state: "placeholder" | "configured";
  enabled: boolean;
  test_status: "not_tested" | "passed" | "failed";
  last_tested_at?: string | null;
}

export interface IntegrationWrite {
  kind: IntegrationSummary["kind"];
  name: string;
  endpoint: string;
  topic_or_database: string;
  security_mode: string;
  credential_state: "placeholder" | "configured";
  enabled: boolean;
}

export interface IntegrationTestResult {
  id: string;
  kind: IntegrationSummary["kind"];
  ok: boolean;
  mocked: boolean;
  detail: string;
}

export const telemetryApi = {
  overview: () => apiGet<OverviewResponse>("/overview"),
  pipelines: () => apiGet<PipelineResource[]>("/pipelines"),
  createPipeline: (payload: PipelineCreate) => apiPost<PipelineResource>("/pipelines", payload),
  events: () => apiGet<EventRecord[]>("/events"),
  alerts: () => apiGet<Alert[]>("/alerts"),
  acknowledge: (id: string) => apiPost<Alert>(`/alerts/${id}/acknowledge`),
  resolve: (id: string, resolution_note: string) => apiPost<Alert>(`/alerts/${id}/resolve`, { resolution_note }),
  stream: () => apiGet<StreamState>("/stream"),
  pause: () => apiPost<StreamState>("/stream/pause"),
  resume: () => apiPost<StreamState>("/stream/resume"),
  integrations: () => apiGet<IntegrationSummary[]>("/integrations"),
  saveIntegration: (payload: IntegrationWrite) => apiPost<IntegrationSummary>("/integrations", payload),
  testIntegration: (id: string) => apiPost<IntegrationTestResult>(`/integrations/${id}/test`),
};