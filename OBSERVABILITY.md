# OBSERVABILITY.md
# YGGDRASIL CHRONICLES
# Observability, Logging, Metrics, and Alerting
Version: 2.0 -- Enterprise Edition
Status: Operational
Last reviewed: 2026-06-14

---

## 1. PURPOSE

Observability exists to prove that the game is healthy, deterministic, secure, and recoverable.

The system must make the following questions easy to answer:

- Is the game playable right now?
- Are saves completing transactionally?
- Are gameplay engines producing deterministic results?
- Are AI providers failing, timing out, or returning rejected output?
- Are database, Redis, and Qdrant within performance targets?
- Are players encountering errors or degraded gameplay?

---

## 2. LOGGING STANDARD

All backend logs must be structured JSON. `print()` is forbidden in production code.

Every log entry must include:

- `timestamp`
- `level`
- `service`
- `environment`
- `request_id`
- `event_name`
- `message`

When applicable, include:

- `player_id`
- `character_id`
- `combat_id`
- `quest_id`
- `npc_id`
- `world_tick`
- `duration_ms`
- `error_code`

Never log:

- passwords
- JWTs
- refresh tokens
- AI provider keys
- raw payment data
- full prompt payloads that include private player data

---

## 3. REQUIRED LOG CATEGORIES

| Category | Purpose |
|---|---|
| `SYSTEM` | startup, shutdown, health, configuration |
| `DATABASE` | connection state, migration state, slow queries |
| `SAVE` | save/load creation, rollback, validation failures |
| `COMBAT` | deterministic combat resolution summaries |
| `QUEST` | state transitions and invalid transition attempts |
| `NPC` | dialogue lifecycle without raw sensitive payloads |
| `AI` | provider routing, fallback, timeout, validation outcome |
| `RAG` | retrieval latency, memory count, Qdrant status |
| `SECURITY` | auth events, rate limits, suspicious input |
| `PERF` | p95/p99 latency and bottleneck events |
| `ERROR` | classified exceptions and recovery path |

---

## 4. METRICS

Expose Prometheus-compatible metrics at `GET /metrics`. This endpoint is internal-only.

Required service metrics:

- `http_requests_total`
- `http_request_duration_seconds`
- `http_errors_total`
- `db_query_duration_seconds`
- `redis_operation_duration_seconds`
- `qdrant_query_duration_seconds`
- `celery_task_duration_seconds`
- `celery_task_failures_total`

Required gameplay metrics:

- `save_attempts_total`
- `save_failures_total`
- `save_duration_seconds`
- `load_duration_seconds`
- `combat_actions_total`
- `combat_encounters_total`
- `combat_determinism_failures_total`
- `quest_transitions_total`
- `npc_interactions_total`
- `dungeon_operations_total`
- `world_events_total`
- `memory_records_created_total`
- `memory_index_jobs_total`
- `rag_cache_operations_total`
- `character_operations_total`
- `inventory_operations_total`
- `travel_operations_total`

Required AI metrics:

- `ai_requests_total`
- `ai_provider_failures_total`
- `ai_provider_latency_seconds`
- `ai_output_rejections_total`
- `ai_fallback_uses_total`
- `ai_cached_template_uses_total`
- `narrative_generations_total{kind,outcome}`

---

## 5. TRACING

Every external request must receive a request ID. The request ID must propagate through:

```text
Frontend -> API -> Service -> Engine -> Repository -> Event Bus -> Background Task
```

Trace spans must be created for:

- API request handling
- service orchestration
- engine execution
- database queries
- Redis calls
- Qdrant retrieval
- AI provider calls
- save/load transactions

---

## 6. HEALTH CHECKS

Required endpoints:

```text
GET /health
GET /health/db
GET /health/redis
GET /health/qdrant
GET /health/ai
GET /health/worker
```

Health states:

| State | Meaning |
|---|---|
| `healthy` | service meets all requirements |
| `degraded` | game remains playable with reduced capability |
| `unhealthy` | required gameplay or persistence dependency is unavailable |

Cloud AI provider failure may degrade narrative features, but it must not make the game unplayable while deterministic gameplay systems remain online.

---

## 7. ALERTS

P0 alerts:

- save transaction failures exceed 1% over 5 minutes
- database unavailable
- authentication bypass suspected
- secret exposure detected
- combat determinism failure detected

P1 alerts:

- API p95 latency exceeds 200ms for 10 minutes
- API p99 latency exceeds 1000ms for 5 minutes
- Qdrant retrieval p95 exceeds 500ms for 10 minutes
- all cloud AI providers unavailable and Ollama fallback unavailable
- error rate exceeds 5% for 5 minutes

P2 alerts:

- AI output rejection rate exceeds 15% for 30 minutes
- memory embedding backlog exceeds threshold
- Redis cache unavailable but database remains healthy

Alerts must define owner, runbook link, paging route, deduplication key, and tested escalation policy. An alert without a response action is telemetry, not an operational control.

---

## 8. DASHBOARDS

Minimum dashboards:

- System health
- API latency and errors
- Database performance
- Save/load reliability
- Combat and quest engine events
- AI provider health and fallback usage
- RAG retrieval latency and memory volume
- Security audit events
- Background worker queue depth

---

## 9. RETENTION

| Data Type | Minimum Retention |
|---|---|
| Application logs | 30 days |
| Security audit logs | 1 year |
| Metrics | 90 days |
| Traces | 14 days |
| Release artifacts | 1 year |
| Incident reports | permanent |

Security audit logs must be append-only from application code.

Retention and deletion must follow `DATA_GOVERNANCE.md`. Telemetry must use data minimization, pseudonymous identifiers where possible, and tested deletion/tombstone behavior.

---

## 10. SLO REPORTING

SLIs and SLOs are defined in `SERVICE_LEVEL_OBJECTIVES.md`.

Required reporting:

- rolling 28-day SLO attainment;
- error-budget consumption and burn rate;
- release annotations on dashboards;
- per-version save/load failure rate;
- availability separated between core gameplay and narrative features;
- capacity headroom for PostgreSQL, workers, queues, Redis, Qdrant, and storage.

Dashboard health alone is insufficient. Release gates must link to the underlying metric query and time window.

---

## 11. FINAL RULE

If the system cannot explain what happened, when it happened, and whether player state was preserved, it does not satisfy the operational evidence requirements.
