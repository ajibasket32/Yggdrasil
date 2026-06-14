# YGGDRASIL CHRONICLES

# Master Release Task List

Version: 3.0
Status: Planning
Last reviewed: 2026-06-14

---

## Task Authority

This file is the source of truth for task status. Valid statuses are `TODO`,
`IN_PROGRESS`, `DONE`, and `BLOCKED`. Only tasks in the first unfinished release
in `MVP_ROADMAP.md` may move to `IN_PROGRESS`.

## v0.1 Foundation

| ID | Release | Status | Description | Acceptance Criteria | Dependencies | Notes |
|---|---|---|---|---|---|---|
| FND-001 | v0.1 | DONE | Create the mandatory monorepo directory structure and baseline configuration. | Required root directories exist and configuration contains no secrets. | None | Required directories and environment-only baseline configuration verified on 2026-06-13. |
| FND-002 | v0.1 | DONE | Create minimal FastAPI and React/Vite applications. | Both applications start and expose a basic healthy response/view. | FND-001 | Container and browser smoke checks passed on 2026-06-13. |
| FND-003 | v0.1 | DONE | Define the Docker Compose development stack. | Frontend, backend, PostgreSQL, Redis, Qdrant, Ollama, and Nginx start with one command. | FND-001, FND-002 | `docker compose up --build -d` started all seven services; health checks passed. |
| FND-004 | v0.1 | DONE | Add logging, request IDs, health endpoints, and baseline observability. | Required health checks and structured logs are verified by tests. | FND-002, FND-003 | Live dependency probes, Prometheus metrics, request IDs, and JSON logs verified. |
| FND-005 | v0.1 | DONE | Add formatting, linting, type checking, test harnesses, and CI. | Frontend/backend quality commands and baseline tests pass in CI. | FND-001, FND-002 | Backend and frontend Actions jobs passed in a local runner; dependency and secret scans passed. |

## v0.2 Save System and Persistence

| ID | Release | Status | Description | Acceptance Criteria | Dependencies | Notes |
|---|---|---|---|---|---|---|
| SAV-001 | v0.2 | DONE | Configure SQLAlchemy, PostgreSQL repositories, and Alembic migrations. | Migration upgrade/downgrade and repository integration tests pass. | v0.1 | Revision `0001_save_system` upgraded, downgraded, and upgraded successfully; routes contain no SQL. |
| SAV-002 | v0.2 | DONE | Implement the complete versioned save snapshot contract. | Snapshot schema covers every logical save component required by `AGENTS.md`. | SAV-001 | Schema v1 includes all 11 required logical components with empty values allowed. |
| SAV-003 | v0.2 | DONE | Implement transactional save creation, loading, validation, and deletion. | Failure at any write step leaves no partial save; load restores one coherent version. | SAV-001, SAV-002 | Atomic service/repository flow, checksums, idempotency, player scoping, and soft deletion verified. |
| SAV-004 | v0.2 | DONE | Implement save migration and rollback behavior. | Supported old fixtures migrate or fail safely with an actionable error. | SAV-002, SAV-003 | Schema v0 migrates atomically to v1; unsupported versions and corrupt snapshots fail closed. |
| SAV-005 | v0.2 | DONE | Add save unit, integration, and regression tests. | Restart, concurrency, corruption, rollback, and deletion cases pass. | SAV-003, SAV-004 | 22 backend tests pass at 83.59% coverage; live process restart/load and migration rollback also passed. |

## v0.3 AI Provider Layer and Fallback

| ID | Release | Status | Description | Acceptance Criteria | Dependencies | Notes |
|---|---|---|---|---|---|---|
| AIP-001 | v0.3 | DONE | Define provider-neutral request, response, adapter, and error contracts. | Contracts validate structured narrative data without gameplay mutation fields. | v0.2 | Frozen Pydantic request/output contracts reject extra gameplay mutation fields. |
| AIP-002 | v0.3 | DONE | Implement configured provider adapters behind the adapter interface. | Direct provider SDK calls exist only under `backend/app/ai/adapters/`. | AIP-001 | Gemini, Groq, OpenAI, Anthropic, OpenRouter, Ollama, and cached adapters implemented; source scan found HTTP calls only in adapter files. |
| AIP-003 | v0.3 | DONE | Implement orchestrator routing, timeout, retry, and fallback behavior. | Failure tests traverse configured cloud providers, Ollama, and cached narrative. | AIP-001, AIP-002 | Configured order, bounded retries/timeouts, provider advancement, and final cached degradation verified. |
| AIP-004 | v0.3 | DONE | Add output validation, budgets, logging, metrics, and secret-safe configuration. | Invalid/state-changing output fails closed and secrets never enter logs. | AIP-001, AIP-003 | Entity scope, schema, gameplay-authority, Redis budget, structured metrics, and secret-safe error logging tests pass. |
| AIP-005 | v0.3 | DONE | Add unit, integration, and regression coverage for provider independence. | Single-provider and all-cloud failure scenarios pass. | AIP-002, AIP-003, AIP-004 | 46 backend tests pass at 85.82% coverage; provider, outage, validation, budget, and isolation scenarios included. |

## v0.4 RAG and Memory

| ID | Release | Status | Description | Acceptance Criteria | Dependencies | Notes |
|---|---|---|---|---|---|---|
| RAG-001 | v0.4 | DONE | Implement canonical memory records and deduplication. | PostgreSQL stores versioned memory records before any embedding job is queued. | v0.3 | Canonical player-scoped rows, exact logical deduplication, typed links, and reversible migration verified. |
| RAG-002 | v0.4 | DONE | Implement asynchronous embedding and Qdrant indexing. | Failed indexing is retryable and cannot lose canonical memory data. | RAG-001 | Durable PostgreSQL jobs, Celery processing, retries, stale-job recovery, and nine rebuildable Qdrant collections verified. |
| RAG-003 | v0.4 | DONE | Implement scoped retrieval, ranking, filtering, and context limits. | Retrieval tests enforce player/entity scope, privacy filters, and token limits. | RAG-001, RAG-002 | Player/entity/tag filters, canonical-row revalidation, documented scoring, 20-memory limit, and 6,000-token limit pass. |
| RAG-004 | v0.4 | DONE | Implement cache, deletion, and full index rebuild behavior. | Deleted data is removed and the vector index rebuilds from PostgreSQL. | RAG-002, RAG-003 | Redis cache invalidation, canonical-first deletion, retryable vector removal, and full PostgreSQL rebuild pass. |
| RAG-005 | v0.4 | DONE | Add memory/RAG unit, integration, and regression tests. | PostgreSQL, worker, Redis, and Qdrant failure/recovery cases pass. | RAG-001 through RAG-004 | 57 backend tests pass at 84.88% coverage; live Celery-to-Qdrant indexing smoke test passed. No narrative integration added. |

## v0.5 Character Creation and Job System

| ID | Release | Status | Description | Acceptance Criteria | Dependencies | Notes |
|---|---|---|---|---|---|---|
| CHR-001 | v0.5 | DONE | Implement race, job, skill, and character schemas and seed definitions. | Definitions satisfy required fields and support branching prerequisites. | v0.4 | Revision `0003_character_system` adds canonical definitions, stable seeds, constraints, and nested `all`/`any` prerequisites. |
| CHR-002 | v0.5 | DONE | Implement deterministic character creation and stat calculation. | Identical valid inputs produce identical character state. | CHR-001 | Atomic idempotent creation derives stats, resources, starter job, skill, items, slots, and location without AI. |
| CHR-003 | v0.5 | DONE | Implement deterministic XP, level, job, and skill progression. | Unlock and progression tests match engine-owned rules. | CHR-001, CHR-002 | Engine-owned XP formulas, level growth, job prerequisites, job changes, and skill unlocks pass. |
| CHR-004 | v0.5 | DONE | Implement inventory and equipment foundations. | Stack, unique, quest item, equip, and atomic save/load cases pass. | v0.2, CHR-002 | Stack, unique-instance, protected-item, sorting, equipment validation, and canonical save restore cases pass. |
| CHR-005 | v0.5 | DONE | Implement location graph, travel validation, and discovery state. | Invalid travel is rejected and discovery survives save/load. | v0.2, CHR-002 | Directed routes reject invalid movement; permanent per-character discoveries and location restore pass. |
| CHR-006 | v0.5 | DONE | Add character creation and state inspection UI plus full tests. | Browser flow and unit/integration/regression coverage pass. | CHR-002 through CHR-005 | React creation/archive flow displays server-owned state; 70 backend and 10 frontend tests plus deployed create/travel/save/load smoke pass. |

## v0.6 Combat System

| ID | Release | Status | Description | Acceptance Criteria | Dependencies | Notes |
|---|---|---|---|---|---|---|
| CMB-001 | v0.6 | DONE | Implement deterministic turn order and combat state transitions. | Identical inputs/seeds produce identical turn sequences. | v0.5 | Seeded pure engine, stable initiative tie-break, canonical encounters/participants, and restart persistence verified. |
| CMB-002 | v0.6 | DONE | Implement actions, damage, skills, status effects, and enemy behavior. | Formula and effect tests pass without AI or network access. | CMB-001 | Attack, active skills, items, guard, wait, burn/control ticks, escape, and deterministic enemy policy pass without AI/network imports. |
| CMB-003 | v0.6 | DONE | Implement deterministic victory, defeat, loot, XP, and combat events. | Rewards and results replay exactly from recorded inputs. | CMB-001, CMB-002 | Victory rewards, defeat recovery, immutable logs, shared outbox events, retry safety, and save capture after completion are atomic. |
| CMB-004 | v0.6 | DONE | Implement combat UI and replayable combat log. | Player can complete victory and defeat flows in browser tests. | CMB-001 through CMB-003 | Browser combat screen renders canonical resources/actions/logs, survives refresh, and passed deployed victory plus automated defeat flows. |
| CMB-005 | v0.6 | DONE | Add combat unit, integration, and regression tests. | Determinism, persistence, disconnect, and edge-case suites pass. | CMB-001 through CMB-004 | 90 backend and 22 frontend tests pass; overall backend coverage is 84.32%, combat engine is 95%, and combat service is 86% covered. |

## v0.7 World, NPC, and Quest System

| ID | Release | Status | Description | Acceptance Criteria | Dependencies | Notes |
|---|---|---|---|---|---|---|
| WQP-001 | v0.7 | DONE | Implement Quest Engine states, steps, validation, and rewards. | Only valid state transitions occur and rewards are engine-owned. | v0.6 | Pure state transitions, ordered objectives, prerequisite checks, deterministic XP/gold/reputation, and invalid-transition tests pass. |
| WQP-002 | v0.7 | DONE | Implement persistent locations, dungeons, factions, and world events. | State survives save/load with no silent resets. | v0.5, WQP-001 | Canonical faction, dungeon, character state, immutable world events, and permanent-clear restore rules pass migration and regression tests. |
| WQP-003 | v0.7 | DONE | Implement NPC profiles, schedules, knowledge, and roles. | Deterministic NPC behavior works without AI. | WQP-002 | UUID-backed profiles, schedules, knowledge, roles, location presence, and menu actions run without AI calls. |
| WQP-004 | v0.7 | DONE | Implement numeric relationships and event-driven memory candidates. | Engine events update relationships and create canonical memory candidates. | v0.4, WQP-001, WQP-003 | Six bounded numeric dimensions, non-farmable help actions, canonical memories, and durable index jobs commit atomically. |
| WQP-005 | v0.7 | DONE | Implement quest journal and NPC interaction UI. | Browser tests cover accept, progress, fail, complete, archive, and interaction. | WQP-001 through WQP-004 | Menu-driven quest, NPC, faction, dungeon, and chronicle UI passes 28 frontend tests and deployed browser completion with no console errors. |
| WQP-006 | v0.7 | DONE | Add world/NPC/quest integration and regression tests. | Persistence, state-machine, authorization, and permanent-state cases pass. | WQP-001 through WQP-005 | 97 backend tests pass at 84.55% coverage; authorization, save/load, idempotency, memory, and no-resurrection cases are covered. |

## v0.8 AI Narrative and Dialogue

| ID | Release | Status | Description | Acceptance Criteria | Dependencies | Notes |
|---|---|---|---|---|---|---|
| NAR-001 | v0.8 | DONE | Implement versioned prompts and narrative context builders. | Context includes relevant memory, NPC, faction, quest, relationship, and location data. | v0.7 | Player-scoped builders merge Qdrant-ranked and pending PostgreSQL memories into versioned, canonically hashed context packages. |
| NAR-002 | v0.8 | DONE | Implement validated NPC dialogue and narration services. | Output cannot modify canonical state or introduce invalid entities. | v0.3, v0.4, NAR-001 | Dialogue and description services use the orchestrator, strict schemas, entity boundaries, idempotency, and separate cosmetic persistence. |
| NAR-003 | v0.8 | DONE | Implement lore and quest-framing generation with caching. | Generated content passes schema/lore validation and degrades to approved local content. | NAR-001, NAR-002 | Lore, framing, and location descriptions use prompt/context cache keys and approved local fallback content. |
| NAR-004 | v0.8 | DONE | Implement JRPG dialogue presentation and fallback UX. | Interaction remains menu/game driven and works with AI disabled. | NAR-002, NAR-003 | Fixed dialogue topics and story panels expose fallback/cache status without any free-form chat input. |
| NAR-005 | v0.8 | DONE | Add safety, grounding, fallback, and regression tests. | Injection, hallucination, timeout, provider outage, and state-write attempts fail safely. | NAR-001 through NAR-004 | 108 backend tests pass at 84.90% coverage and 33 frontend tests pass at 94.75% statements and 80.43% branches. |

## v0.9 Asset Discovery and License Tracking

| ID | Release | Status | Description | Acceptance Criteria | Dependencies | Notes |
|---|---|---|---|---|---|---|
| AST-001 | v0.9 | DONE | Define vertical-slice asset needs and approved source/license rules. | Asset checklist maps every need to permitted license categories. | v0.8 | Mapping the current browser slice to a minimal CC0 interface, character, enemy, item, and environment set. |
| AST-002 | v0.9 | DONE | Discover, review, and select local assets. | Selected assets pass suitability, originality, and license review. | AST-001 | Sources limited by `AGENTS.md`. |
| AST-003 | v0.9 | DONE | Import, optimize, and integrate selected assets locally. | No gameplay runtime download is required and performance budgets are met. | AST-002 | Preserve original source files where required. |
| AST-004 | v0.9 | DONE | Complete asset catalog and attribution evidence. | Every shipped asset has complete provenance and license metadata. | AST-002, AST-003 | Block release on missing evidence. |

## v0.10 Playable Vertical Slice

| ID | Release | Status | Description | Acceptance Criteria | Dependencies | Notes |
|---|---|---|---|---|---|---|
| VSL-001 | v0.10 | TODO | Define vertical slice region and boundary. | Regional map (Valeris) and Forest dungeon boundary defined. | v0.9 | Starting region: Valeria. |
| VSL-002 | v0.10 | TODO | Implement Character Creation with assets. | Screen uses GrafxKid portraits and RPG UI elements. | VSL-001 | |
| VSL-003 | v0.10 | TODO | Implement Exploration and NPC Interaction. | Player can move between Valeris and Forest; NPC "Elara" provides a quest. | VSL-002 | |
| VSL-004 | v0.10 | TODO | Implement Combat Encounter with sprites. | Combat with "Slime" or "Goblin" uses Redshrike sprites. | VSL-003 | |
| VSL-005 | v0.10 | TODO | Implement Quest Completion and Rewards. | Defeating monster progresses quest; NPC grants XP/Gold. | VSL-004 | |
| VSL-006 | v0.10 | TODO | Integrate transactional Save/Load. | State preserved after browser refresh or server restart. | VSL-005 | |
| VSL-007 | v0.10 | TODO | Integrate Narrative and AI Fallback. | NPC dialogue uses AI if available, otherwise approved local fallback. | VSL-006 | |
| VSL-008 | v0.10 | TODO | Complete E2E verification and release gates. | Critical journey passes; performance/accessibility gates met. | VSL-007 | |

## v1.0 MVP Release

| ID | Release | Status | Description | Acceptance Criteria | Dependencies | Notes |
|---|---|---|---|---|---|---|
| MVP-001 | v1.0 | TODO | Expand content to the bounded MVP targets. | Required MVP capabilities exist without exceeding documented limits. | v0.10 | Avoid post-MVP scope. |
| MVP-002 | v1.0 | TODO | Harden migrations, save compatibility, backup, restore, and rollback. | Drills pass against release-candidate data with recorded RPO/RTO evidence. | MVP-001 | Release-blocking gate. |
| MVP-003 | v1.0 | TODO | Complete security, privacy, dependency, license, and provenance evidence. | Required scans/reviews pass or have approved current exceptions. | MVP-001 | No unowned risk. |
| MVP-004 | v1.0 | TODO | Complete accessibility, performance, SLO, and observability validation. | Targets pass with dashboards, alerts, and test evidence. | MVP-001 | Release-blocking gate. |
| MVP-005 | v1.0 | TODO | Complete full unit, integration, regression, and E2E suites. | Coverage thresholds and every critical journey pass. | MVP-001 through MVP-004 | Include AI-offline gameplay. |
| MVP-006 | v1.0 | TODO | Assemble release notes, evidence, approvals, and packaged artifacts. | Every applicable release gate has traceable evidence and sign-off. | MVP-002 through MVP-005 | Stop after v1.0 completion. |
