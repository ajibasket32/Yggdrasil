# Yggdrasil Chronicles

Version: 2.0 -- Enterprise Edition
Status: Informational
Last reviewed: 2026-06-14

Yggdrasil Chronicles is a browser-based JRPG with deterministic game systems and an AI narrative layer. The game engine owns all gameplay outcomes. AI may enrich dialogue, lore, and narration, but it never controls damage, rewards, progression, loot, quest state, or persistence.

## Project Status

Current phase: v0.9 Asset Discovery and License Tracking complete. No release is
currently in progress; v0.10 Playable Vertical Slice is the next
recommended release.

The implementation is not release-ready. `RELEASE_CHECKLIST.md` governs
Markdown cleanliness only; software release still requires the implementation,
test, security, legal, and operational evidence described by the canonical
contracts.

## Core Law

```text
ENGINE FIRST. AI SECOND. ALWAYS.
```

If gameplay and AI conflict, gameplay wins.

## Documentation Map

Read these documents in this order:

1. [`AGENTS.md`](AGENTS.md) -- architectural law, AI boundaries, contributor rules
2. [`ARCHITECTURE.md`](ARCHITECTURE.md) -- system layers and runtime boundaries
3. [`DATABASE_SCHEMA.md`](DATABASE_SCHEMA.md), [`API_SPEC.md`](API_SPEC.md), [`CODING_STANDARDS.md`](CODING_STANDARDS.md), [`SECURITY_GUIDELINES.md`](SECURITY_GUIDELINES.md), [`TESTING_STRATEGY.md`](TESTING_STRATEGY.md) -- implementation contracts
4. [`COMBAT_DESIGN.md`](COMBAT_DESIGN.md), [`JOB_SYSTEM.md`](JOB_SYSTEM.md), [`RAG_DESIGN.md`](RAG_DESIGN.md) -- system design
5. [`DOCUMENTATION_GOVERNANCE.md`](DOCUMENTATION_GOVERNANCE.md), [`DATA_GOVERNANCE.md`](DATA_GOVERNANCE.md), [`SERVICE_LEVEL_OBJECTIVES.md`](SERVICE_LEVEL_OBJECTIVES.md), [`ACCESSIBILITY.md`](ACCESSIBILITY.md), [`SECURITY.md`](SECURITY.md), [`OBSERVABILITY.md`](OBSERVABILITY.md), [`OPERATIONS_RUNBOOK.md`](OPERATIONS_RUNBOOK.md), [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md), [`CONTRIBUTING.md`](CONTRIBUTING.md) -- governance, operations, and contribution rules
6. [`RELEASE_PROCESS.md`](RELEASE_PROCESS.md), [`MVP_ROADMAP.md`](MVP_ROADMAP.md), [`TASKS.md`](TASKS.md), [`RELEASE_STATUS.md`](RELEASE_STATUS.md), [`TECH_DEBT.md`](TECH_DEBT.md), [`RISK_REGISTER.md`](RISK_REGISTER.md) -- release execution, planning, and risk control
7. [`WORLD_BIBLE.md`](WORLD_BIBLE.md), [`PRODUCT_VISION.md`](PRODUCT_VISION.md) -- lore and product vision

Supporting records: [`CHANGELOG.md`](CHANGELOG.md), [`RELEASE_NOTES.md`](RELEASE_NOTES.md), [`assets/CATALOG.md`](assets/CATALOG.md), [`docs/adr/`](docs/adr/), and [`DOCUMENTATION_AUDIT.md`](DOCUMENTATION_AUDIT.md).

## Target Stack

- Frontend: React 18, TypeScript strict mode, Vite, Phaser 3, Zustand
- Backend: FastAPI, Python 3.12+, SQLAlchemy 2.x, Alembic, Pydantic v2
- Infrastructure: PostgreSQL 16, Redis 7, Qdrant, Docker Compose, Nginx, Ollama
- AI: Provider-agnostic orchestrator with adapters only under `backend/app/ai/adapters/`

## Development Start

Start the complete foundation stack:

```bash
docker compose up --build
```

Development endpoints:

- Application through Nginx: `http://localhost:8080`
- Frontend static container: `http://localhost:3000` (API proxy is not
  available on this direct port; use the Nginx application URL for gameplay)
- Backend directly: `http://localhost:8000`
- Health summary: `http://localhost:8000/health`
- Metrics: `http://localhost:8000/metrics`

The committed `.env.example` contains development-only sample values. Never
commit a real `.env` file or production credentials.

## MVP Definition

A valid MVP lets a player create a character, explore, fight, progress, accept and complete quests, talk to NPCs, save, load, and continue after cloud AI providers fail.

NPC memory and AI narration are valuable, but they are not allowed to replace deterministic gameplay systems.

## Release Gates

Before any public or stakeholder release:

- `docker compose up --build` starts the complete stack.
- Unit, integration, regression, and E2E tests pass.
- Coverage meets the thresholds in `TESTING_STRATEGY.md`.
- Security scanning passes with no high-severity unresolved findings.
- Save/load is transactional and verified.
- No direct AI provider calls exist outside provider adapters.
- Observability, audit logging, backup, rollback, and incident response are documented and tested.
- Release evidence includes artifact digests, SBOM, provenance, security/license scans, RPO/RTO results, and signed approvals.
- Data inventory, privacy lifecycle, accessibility, originality/IP review, and active risks pass their gates.

## Contributor Start

Before writing code, read:

1. `PRODUCT_VISION.md`
2. `MVP_ROADMAP.md`
3. `TASKS.md`
4. `AGENTS.md`
5. `RELEASE_CHECKLIST.md`
6. `ARCHITECTURE.md`
7. `CODING_STANDARDS.md`
8. The system document related to the selected release

Generated code that violates the engine-first boundary must be rejected and regenerated.
Complete only the first unfinished release and stop before starting the next.
