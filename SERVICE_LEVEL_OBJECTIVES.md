# SERVICE_LEVEL_OBJECTIVES.md
# YGGDRASIL CHRONICLES
# Reliability Targets, SLIs, SLOs, and Error Budgets
Version: 2.0 -- Enterprise Edition
Status: Operational
Last reviewed: 2026-06-13

---

## 1. PURPOSE

This document converts performance and reliability expectations into measurable production objectives. SLOs are release and operations controls, not marketing promises or contractual SLAs.

---

## 2. CRITICAL USER JOURNEYS

The protected journeys are:

1. authenticate and resume a session;
2. load a valid save;
3. mutate inventory/equipment safely;
4. complete a combat action;
5. transition a quest;
6. create a save;
7. continue gameplay when cloud AI is unavailable.

---

## 3. SERVICE LEVEL INDICATORS

| SLI | Good Event |
|---|---|
| API availability | Non-5xx response, excluding invalid client requests |
| Save correctness | Save commits completely and passes post-write validation |
| Load correctness | Load restores the expected versioned snapshot completely |
| Gameplay mutation correctness | Authorized mutation commits exactly once |
| API latency | Request completes below endpoint threshold |
| Narrative availability | Valid AI or approved cached/template response is returned |

Synthetic checks must not be the only source of availability data. Production telemetry and critical-flow probes are both required.

---

## 4. MVP PRODUCTION SLOS

Measured over a rolling 28-day window:

| Objective | Target |
|---|---|
| Core gameplay API availability | 99.9% |
| Successful transactional saves | 99.99% |
| Successful loads of valid compatible saves | 99.99% |
| Exactly-once outcome for idempotent critical mutations | 99.999% |
| Core API latency | p95 < 200ms and p99 < 1000ms |
| Qdrant retrieval latency | p95 < 500ms |
| Narrative response, including fallback | 99.0% |
| Combat determinism | 100%; any confirmed mismatch is P0 |

Save corruption, unauthorized state mutation, and deterministic mismatch have zero tolerated error budget.

---

## 5. ERROR BUDGET POLICY

When a 28-day SLO consumes:

- 50% of budget before day 14: reliability review required;
- 75% of budget: freeze risky feature releases affecting that journey;
- 100% of budget: feature releases stop until reliability is restored and approved.

Security incidents, save corruption, or AI gameplay influence trigger a release freeze regardless of remaining budget.

---

## 6. RECOVERY OBJECTIVES

| System | RPO | RTO |
|---|---|---|
| PostgreSQL canonical state | <= 5 minutes | <= 60 minutes |
| Authentication/session service | <= 15 minutes | <= 60 minutes |
| Qdrant vectors | Rebuildable from PostgreSQL; <= 24 hours of index lag | <= 4 hours |
| Redis cache/queues | No canonical state loss | <= 30 minutes |
| Static assets and release artifacts | Zero for released versioned artifacts | <= 60 minutes |

An environment that cannot meet these objectives must not claim production readiness.

---

## 7. MEASUREMENT

- Exclude planned maintenance only when announced, bounded, and separately reported.
- Do not exclude dependency failures if they affect the player journey.
- Report SLOs by environment, version, region, and endpoint class.
- Alert calculations must use the same metric definitions as reports.
- Changes to SLI formulas require review under `DOCUMENTATION_GOVERNANCE.md`.

---

## 8. RELEASE GATES

Each release candidate must provide:

- baseline and candidate performance comparison;
- critical journey smoke-test results;
- expected SLO impact;
- capacity headroom;
- rollback thresholds;
- dashboard and alert verification.

---

## 9. FINAL RULE

Reliability claims require measured user outcomes, not merely healthy containers.
