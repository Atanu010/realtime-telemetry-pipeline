# StreamPulse — Real-Time Telemetry & Operations Console

StreamPulse is a modern, high-performance telemetry and event-processing operations platform. It provides real-time pipeline monitoring, source/consumer lifecycle management, live event streaming, incident triage, and connection topology configuration.

## Features

- **Pipeline Overview**: Live throughput (events/sec), P99 latency tracking, consumer lag, and buffer metrics.
- **Topology & Stage Inspection**: Status visualization across Ingress, Kafka Queues, Worker Processors, and Storage Sinks.
- **Sources & Consumers**: Manage partition count, streaming rate, offset lag, and retention policy.
- **Live Event Inspector**: Tail and filter real-time telemetry events by level (`INFO`, `WARN`, `ERROR`), source, and topic with interactive JSON inspection.
- **Incident Management**: Alert lifecycle tracking with severity classification (P1/P2/P3), operator acknowledgment, and resolution auditing.
- **Safety Controls**: Explicit global stream pause/resume emergency gate.
- **Connector Config**: Manage Kafka, Redis, and TimescaleDB connection profiles with connection diagnostics.
- **Operator Access Control**: Role-gated authentication safeguarding operator actions.

---

## Architecture

- **Backend**: FastAPI + Motor (Async MongoDB) / In-Memory fallback + Pydantic v2.
- **Frontend**: React 19 + TypeScript + Vite + Tailwind CSS v4 + Radix/Base-UI + Recharts.
- **API Protocol**: RESTful `/api` with Bearer token authentication.

```
realtime-telemetry-pipeline/
├── backend/               # FastAPI backend service
│   ├── lib/               # Database client & helper utilities
│   ├── models/            # Pydantic data schemas
│   ├── routers/           # API routes (telemetry, auth)
│   ├── server.py          # FastAPI application entrypoint
│   └── requirements.txt   # Python dependencies
├── frontend/              # React 19 + TypeScript operations UI
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── lib/           # API client, config, telemetry hooks
│   │   ├── pages/         # Operations console & Auth gate
│   │   └── App.tsx        # Main application root
│   └── package.json       # Node dependencies & build scripts
├── render.yaml            # Render deployment blueprint
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+ and npm
- MongoDB (optional; defaults to local/in-memory fallback when unconfigured)

### 1. Backend Setup

```bash
cd backend
python -m venv .venv
# Activate virtual environment:
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

# Run backend API server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to open the StreamPulse console.

---

## Authentication & Access Control

Access to the StreamPulse telemetry dashboard is restricted to authorized operators:
- Default Operator Passkey: `atanu-telemetry-2026`
- Configurable via `OPERATOR_KEY` environment variable in the backend.

---

## Production Deployment

### Render Blueprint

StreamPulse includes a pre-configured [render.yaml](render.yaml) blueprint:
1. Connect your repository to [Render](https://render.com).
2. Create a new Blueprint instance pointing to this repository.
3. Configure `MONGO_URL` and `OPERATOR_KEY` environment variables.
4. Render automatically provisions the API service and the static UI.
