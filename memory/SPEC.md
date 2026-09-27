# StreamPulse Living Spec

## Product
StreamPulse is a dark operations console for a generic real-time telemetry and event-processing pipeline. It provides a cohesive operator flow across pipeline overview, sources/consumers, live event inspection, incident triage, and connection/storage configuration.

## Data model
- `PipelineResource`: source or consumer with protocol, partitions, rate, lag, status, and retention days.
- `EventRecord`: normalized event metadata plus a JSON payload.
- `Alert`: severity, status, affected stage, operator audit fields, and optional resolution note.
- `StreamState`: global running/paused state.
- `IntegrationSummary`: Kafka, Redis, or TimescaleDB connection profile metadata; credentials are never returned to the UI.

## Key flows
1. Open the Overview tab to inspect metrics, topology, system health, and open incidents.
2. Add a source or consumer from Sources & Consumers; resource configuration persists through the API.
3. Tail and filter the Live Event Inspector, then select an event to inspect JSON.
4. Acknowledge or resolve an alert. Resolving requires an operator note.
5. Pause all stream processing using the explicit `CONFIRM PAUSE` safety gate, or resume it from the header/banner.
6. Save connector profiles under Connection & Storage Config and request a one-shot connection test.

## Auth
Operator authentication and access gating is implemented. The operations console requires an authorized operator key (`OPERATOR_KEY`) to access metrics, manage resources, and perform mutations.

## Integrations
The pod has no user-provided external credentials. Kafka, Redis, and TimescaleDB cards are configured with redacted placeholder endpoints. Connection test responses are **MOCKED** and explicitly report that external credentials are not active. The telemetry feed and metrics are **MOCKED** demo data; no live Kafka consumer or TimescaleDB writer starts until real credentials and adapters are supplied.