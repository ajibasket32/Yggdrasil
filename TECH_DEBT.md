# TECH_DEBT.md

# YGGDRASIL CHRONICLES

Technical Debt Register

Version: 2.0 -- Enterprise Edition
Status: Planning
Last reviewed: 2026-06-13

---

# PURPOSE

This document tracks known technical debt, architectural compromises, temporary implementations, postponed features, and scalability concerns.

Technical debt is acceptable when:

* It accelerates MVP delivery.
* It is documented.
* It has a future resolution plan.

Technical debt is NOT acceptable when:

* It is hidden.
* It creates data corruption risk.
* It threatens save compatibility.
* It threatens world consistency.

---

# DEBT PRIORITY LEVELS

CRITICAL

Must be resolved before public release.

HIGH

Must be resolved before Version 1.0.

MEDIUM

Can be postponed after Version 1.0.

LOW

Can remain indefinitely.

---

# MVP PHILOSOPHY

The first goal is to create a playable game.

Not a perfect game.

Not a scalable MMO.

Not an overbuilt platform.

The MVP should prioritize:

* Gameplay
* Stability
* Save System
* Core RPG Loop

Over:

* Massive Scale
* Complex AI
* Dynamic Politics
* Multiplayer

---

# CURRENT ACCEPTED DEBTS

---

## TD-001

Title:

Single World Server

Priority:

MEDIUM

Description:

The entire game world runs on a single backend process.

Reason:

Reduces infrastructure complexity.

Risk:

Limited scalability.

Future Resolution:

Move World Engine to dedicated microservice.

---

## TD-002

Title:

Simplified Economy Simulation

Priority:

MEDIUM

Description:

NPC economies will use predefined values rather than full supply-demand simulation.

Reason:

Allows economy features without expensive calculations.

Risk:

Economy may feel artificial.

Future Resolution:

Replace with regional simulation system.

---

## TD-003

Title:

Static NPC Daily Schedules

Priority:

LOW

Description:

NPC schedules are rule-based.

Reason:

Faster implementation.

Risk:

NPC behavior may become predictable.

Future Resolution:

Introduce richer deterministic, engine-owned schedule policies.

---

## TD-004

Title:

Single Continent Launch

Priority:

LOW

Description:

Version 1.0 launches with one continent.

Reason:

Content production constraints.

Risk:

Limited exploration variety.

Future Resolution:

Additional continents.

---

## TD-005

Title:

No Multiplayer Support

Priority:

LOW

Description:

Single-player only.

Reason:

Focus on gameplay foundation.

Risk:

None.

Future Resolution:

Version 3.0 multiplayer architecture.

---

## TD-006

Title:

Limited Voice Support

Priority:

LOW

Description:

No voice generation at launch.

Reason:

Cost and complexity.

Risk:

None.

Future Resolution:

Optional AI voice module.

---

# AI TECH DEBT

---

## TD-AI-001

Title:

Context Window Constraints

Priority:

HIGH

Description:

AI providers have finite context windows.

Reason:

Provider limitations.

Risk:

Large world histories may exceed limits.

Mitigation:

Memory summarization pipeline.

Future Resolution:

Hierarchical memory retrieval.

---

## TD-AI-002

Title:

Provider Output Variability

Priority:

HIGH

Description:

Different providers generate different outputs.

Reason:

Model behavior differences.

Risk:

Lore inconsistency.

Mitigation:

Output validation layer.

Future Resolution:

Fine-tuned narrative model.

---

## TD-AI-003

Title:

Hallucinated Content

Priority:

HIGH

Description:

AI may generate entities that do not exist.

Reason:

LLM limitations.

Risk:

World inconsistency.

Mitigation:

Entity validation system.

Future Resolution:

Structured generation pipeline.

---

# MEMORY SYSTEM DEBT

---

## TD-MEM-001

Title:

Duplicate Memories

Priority:

MEDIUM

Description:

Multiple similar events may create duplicate memory entries.

Reason:

Initial implementation simplicity.

Risk:

Retrieval noise.

Future Resolution:

Memory deduplication service.

---

## TD-MEM-002

Title:

Memory Growth

Priority:

HIGH

Description:

World memories will continuously increase.

Reason:

Persistent world design.

Risk:

Storage expansion.

Future Resolution:

Memory compression layers.

---

## TD-MEM-003

Title:

Memory Ranking Accuracy

Priority:

MEDIUM

Description:

Retrieval ranking may not always return ideal memories.

Reason:

Embedding limitations.

Risk:

Less coherent dialogue.

Future Resolution:

Hybrid retrieval architecture.

---

## TD-MEM-004

Title:

Deterministic Development Embedder

Priority:

HIGH

Description:

The v0.4 memory index uses a deterministic local feature-hash embedder.

Reason:

It keeps offline development, tests, rebuilds, and provider independence
reproducible without selecting a production embedding provider early.

Risk:

Semantic retrieval quality will be lower than a deployment-grade embedding
model.

Future Resolution:

Select and evaluate a deployment embedding model, version its configuration,
and perform a controlled full Qdrant reindex.

---

# WORLD SIMULATION DEBT

---

## TD-WORLD-001

Title:

Simplified Faction Politics

Priority:

MEDIUM

Description:

Faction behavior uses rule systems.

Reason:

Avoid excessive complexity.

Risk:

Politics may feel predictable.

Future Resolution:

Goal-based simulation.

---

## TD-WORLD-002

Title:

Limited Kingdom AI

Priority:

MEDIUM

Description:

Kingdom decisions use weighted rules.

Reason:

Performance concerns.

Risk:

Reduced realism.

Future Resolution:

Strategic simulation engine.

---

## TD-WORLD-003

Title:

Simplified Weather

Priority:

LOW

Description:

Weather generated using predefined patterns.

Reason:

MVP scope reduction.

Risk:

Minimal.

Future Resolution:

Regional climate simulation.

---

# DATABASE DEBT

---

## TD-DB-001

Title:

Single PostgreSQL Instance

Priority:

MEDIUM

Description:

Single database deployment.

Reason:

Operational simplicity.

Risk:

Scaling limitations.

Future Resolution:

Read replicas.

---

## TD-DB-002

Title:

Memory Tables Growth

Priority:

HIGH

Description:

Memory-related tables may become extremely large.

Reason:

Persistent history design.

Risk:

Query performance degradation.

Future Resolution:

Archival strategy.

---

# COMBAT DEBT

---

## TD-COMBAT-001

Title:

Simple Threat System

Priority:

LOW

Description:

Threat calculations simplified.

Reason:

Reduce implementation complexity.

Risk:

Limited tactical depth.

Future Resolution:

Advanced aggro simulation.

---

## TD-COMBAT-002

Title:

No Combat Replay System

Priority:

LOW

Description:

Battle replay unavailable.

Reason:

Not essential for MVP.

Risk:

None.

Future Resolution:

Replay recording architecture.

---

# CONTENT DEBT

---

## TD-CONTENT-001

Title:

Limited Dungeon Variety

Priority:

MEDIUM

Description:

Initial dungeon generation templates limited.

Reason:

Content creation time.

Risk:

Repetition.

Future Resolution:

Expanded dungeon library.

---

## TD-CONTENT-002

Title:

Limited Monster Families

Priority:

MEDIUM

Description:

Launch includes limited monster archetypes.

Reason:

Development schedule.

Risk:

Reduced diversity.

Future Resolution:

Expanded bestiary.

---

# ASSET PIPELINE DEBT

---

## TD-ASSET-001

Title:

Manual Asset Review

Priority:

LOW

Description:

Downloaded assets require human verification.

Reason:

Prevent low-quality assets.

Risk:

Slower content growth.

Future Resolution:

Automated quality analysis.

---

# PERFORMANCE DEBT

---

## TD-PERF-001

Title:

NPC Update Frequency

Priority:

HIGH

Description:

Not every NPC updates every tick.

Reason:

Performance optimization.

Risk:

Simulation fidelity reduction.

Future Resolution:

Distributed simulation scheduler.

---

## TD-PERF-002

Title:

Large Save File Size

Priority:

MEDIUM

Description:

Persistent world generates large save files.

Reason:

Comprehensive world state.

Risk:

Longer save operations.

Future Resolution:

Delta save architecture.

---

# RELEASE BLOCKERS

The following debts MUST meet their resolution criteria or be removed before Version 1.0:

TD-AI-001

TD-AI-002

TD-AI-003

TD-MEM-002

TD-DB-002

TD-PERF-001

---

# DEBT CONTROL MATRIX

This matrix supplies the mandatory control fields for every legacy entry. The detailed sections above remain the source for description, reason, and risk.

| Debt ID | Owner | Mitigation | Target Release | Resolution Criteria |
|---|---|---|---|---|
| TD-001 | Architecture Owner | Capacity limits, health checks, restart-safe ticks | Post-1.0 | Measured scaling demand justifies extraction and event contracts pass migration tests |
| TD-002 | Gameplay Owner | Versioned deterministic price tables | 1.1 | Economy expansion ships with deterministic tests and save migration |
| TD-003 | NPC System Owner | Versioned schedule rules | Post-1.0 | Richer deterministic schedules meet performance and save tests |
| TD-004 | Product Owner | Enforce MVP content limits | Post-1.0 | Additional continent passes content, migration, and performance gates |
| TD-005 | Architecture Owner | Keep identity/event contracts multiplayer-compatible | 3.0 | Multiplayer threat model and consistency model are approved |
| TD-006 | Product Owner | Text equivalents and optional audio architecture | Post-1.0 | Accessible, licensed voice pipeline passes cost/privacy review |
| TD-AI-001 | AI System Owner | Retrieval budgets, summarization, bounded context | 1.0 | Worst-case context remains within limits and fallback tests pass |
| TD-AI-002 | AI System Owner | Structured schemas, golden evaluations, provider parity tests | 1.0 | Approved evaluation set meets consistency threshold across fallback providers |
| TD-AI-003 | AI System Owner | Entity allowlists and output validation | 1.0 | Hallucinated canonical entities are rejected in adversarial regression tests |
| TD-MEM-001 | Data Owner | Idempotency keys and similarity-based deduplication | 1.1 | Duplicate rate remains below approved threshold under load |
| TD-MEM-002 | Data Owner | Retention tiers, archival, capacity alerts | 1.0 | Capacity model and archival drill meet SLO horizon |
| TD-MEM-003 | AI System Owner | Hybrid retrieval evaluation and relevance monitoring | 1.1 | Golden retrieval set meets approved precision/recall targets |
| TD-MEM-004 | AI System Owner | Keep PostgreSQL canonical, version vector dimensions, and support full rebuild | 1.0 | Selected embedding model passes privacy, cost, latency, offline-fallback, and relevance gates; controlled reindex succeeds |
| TD-WORLD-001 | Gameplay Owner | Deterministic faction rules and explainable events | Post-1.0 | Expanded simulation passes determinism and save compatibility |
| TD-WORLD-002 | Gameplay Owner | Bounded weighted rules and tick budgets | Post-1.0 | Strategic simulation meets tick SLO and replay determinism |
| TD-WORLD-003 | Gameplay Owner | Versioned climate tables | Post-1.0 | Regional climate ships without schema redesign |
| TD-DB-001 | Operations Owner | PITR, monitored backups, tested restore | Post-1.0 | Availability/capacity data requires replicas and failover drill passes |
| TD-DB-002 | Data Owner | Partitioning plan, indexes, archive policy | 1.0 | Five-year growth model meets query and storage SLOs |
| TD-COMBAT-001 | Combat Owner | Versioned deterministic threat formula | Post-1.0 | Advanced threat ships with replay-compatible regression fixtures |
| TD-COMBAT-002 | Combat Owner | Persist ordered combat log and RNG seed | 1.1 | Replay reconstructs identical outcomes from versioned inputs |
| TD-CONTENT-001 | Content Owner | Scope cap and playtest repetition metrics | 1.1 | Content diversity meets approved playtest threshold |
| TD-CONTENT-002 | Content Owner | Scope cap and encounter composition variety | 1.1 | Bestiary diversity meets approved playtest threshold |
| TD-ASSET-001 | Art Owner | Catalog, license scan, human approval | Post-1.0 | Automated checks augment, but do not remove, final human review |
| TD-PERF-001 | World System Owner | Priority buckets, bounded tick work, lag metrics | 1.0 | NPC update policy meets simulation SLO without inconsistent state |
| TD-PERF-002 | Save System Owner | Compression, checksums, size budgets | 1.1 | Representative saves meet p99 size/latency targets; delta format has migration tests |

---

# DEBT REVIEW POLICY

Every major release must include:

Debt Added

Debt Resolved

Debt Escalated

Debt Deferred

Technical debt must always remain visible.

Each new debt entry must include:

Debt ID

Owner

Priority

Risk

Mitigation

Target Release

Resolution Criteria

Release-blocking debts must appear in `RELEASE_CHECKLIST.md` before the release candidate is approved.

Hidden debt is considered a project failure.

Missing owner, mitigation, target release, or resolution criteria prevents a debt item from being accepted as a release exception.

---

# FINAL PRINCIPLE

A documented compromise is acceptable.

An undocumented compromise is a bug waiting to happen.
