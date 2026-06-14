# YGGDRASIL CHRONICLES

# Minimum Viable Product Roadmap

Version: 3.0
Status: Planning
Last reviewed: 2026-06-14

---

## Purpose

This roadmap is the source of truth for MVP release order. Releases are
implemented sequentially. A release is unfinished until every acceptance
criterion is supported by evidence and its tasks in `TASKS.md` are `DONE`.

Status values: `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`.

## Release Selection Rule

The first release below whose status is not `DONE` is the only release that may
be implemented. As of 2026-06-14, that release is
**v0.7 World, NPC, and Quest System**. It
may begin only under a new user prompt.

## MVP Boundaries

- The product is a single-player browser JRPG, not a chatbot.
- The engine owns gameplay outcomes and canonical state.
- PostgreSQL is canonical; Redis and Qdrant are supporting systems.
- Cloud AI failure must not prevent gameplay.
- Post-MVP systems such as multiplayer, housing, player markets, guild wars,
  and full political or economic simulation are excluded.

---

## v0.1 Foundation

**Status:** DONE

**Goal:** Establish a reproducible repository and runtime foundation.

**Scope:**
- Required monorepo directories and baseline project configuration.
- Docker Compose services for frontend, backend, PostgreSQL, Redis, Qdrant,
  Ollama, and Nginx.
- Minimal React/Vite and FastAPI applications, health checks, logging, test
  harnesses, and CI quality gates.

**Tasks:**
- Complete tasks `FND-001` through `FND-005` in `TASKS.md`.

**Acceptance Criteria:**
- `docker compose up --build` starts the defined stack without errors.
- Frontend and backend health checks succeed.
- Formatting, linting, type checking, and baseline tests run in CI.
- No gameplay, persistence, RAG, or AI-provider feature is implemented.

**Excluded Future Work:**
- Save data, game entities, AI adapters, memory retrieval, character systems,
  combat, quests, NPCs, and production game content.

---

## v0.2 Save System and Persistence

**Status:** DONE

**Goal:** Make persistence and transactional save/load the first gameplay
foundation.

**Scope:**
- SQLAlchemy/Alembic infrastructure and the minimum canonical schema needed for
  complete save snapshots.
- Transactional save creation, loading, validation, deletion, versioning,
  migration, and rollback behavior.
- Save API/service/repository boundaries and persistence tests.

**Tasks:**
- Complete tasks `SAV-001` through `SAV-005`.

**Acceptance Criteria:**
- A complete logical save is committed atomically or rolled back completely.
- Save/load survives service restart and preserves a coherent world version.
- Compatibility and rollback tests pass against supported save versions.
- Controllers contain no database access or business logic.

**Excluded Future Work:**
- Playable character creation, inventory UI, combat, quests, NPC dialogue, RAG,
  and narrative generation.

---

## v0.3 AI Provider Layer and Fallback

**Status:** DONE

**Goal:** Build provider-independent narrative infrastructure without enabling
AI gameplay authority.

**Scope:**
- AI Orchestrator contracts, adapter interface, provider registry, configured
  adapters, timeouts, validation boundary, observability, and fallback chain.
- Ollama and cached narrative degradation paths.
- Synthetic narrative requests only; no gameplay integration.

**Tasks:**
- Complete tasks `AIP-001` through `AIP-005`.

**Acceptance Criteria:**
- All provider calls occur only inside adapter files.
- Failure of one provider advances to the next configured provider.
- Failure of all cloud providers reaches Ollama, then approved cached content.
- Tests prove AI output cannot write game state or determine gameplay values.

**Excluded Future Work:**
- RAG retrieval, live NPC dialogue, quest text integration, lore generation,
  and all gameplay systems.

---

## v0.4 RAG and Memory

**Status:** DONE

**Goal:** Establish durable memory capture and provider-neutral retrieval for
future narrative context.

**Scope:**
- Canonical PostgreSQL memory records, asynchronous embedding, Qdrant indexing,
  rebuild/deletion behavior, ranking, filtering, caching, and context packages.
- Synthetic fixtures and infrastructure integration only.

**Tasks:**
- Complete tasks `RAG-001` through `RAG-005`.

**Acceptance Criteria:**
- Memory records persist canonically before indexing.
- Qdrant can be rebuilt from PostgreSQL without loss of canonical data.
- Retrieval enforces scope/privacy filters and documented context limits.
- Narrative context is provider-neutral and cannot mutate gameplay state.

**Excluded Future Work:**
- Character-specific gameplay memories, NPC conversations, relationship
  mutation, quest generation, and dynamic world simulation.

---

## v0.5 Character Creation and Job System

**Status:** DONE

**Goal:** Deliver deterministic character progression and the prerequisite
item, equipment, and navigation foundations required before combat.

**Scope:**
- Character creation, race/job definitions, branching prerequisites,
  deterministic stats, XP, levels, and skill unlocks.
- Inventory, equipment, and location/navigation foundations with atomic save
  compatibility.
- Minimal browser screens for character creation and state inspection.

**Tasks:**
- Complete tasks `CHR-001` through `CHR-006`.

**Acceptance Criteria:**
- Identical character inputs produce identical stats and unlocks.
- Inventory/equipment changes are atomic and survive save/load.
- Travel is limited to valid routes and discovery state persists.
- AI is absent from progression, item stats, skill effects, and navigation.

**Excluded Future Work:**
- Combat encounters, quest transitions, NPC behavior, AI dialogue, and dynamic
  world simulation.

---

## v0.6 Combat System

**Status:** DONE

**Goal:** Deliver deterministic, offline-capable JRPG combat.

**Scope:**
- Turn order, actions, skills, status effects, seeded randomness, enemy
  behavior, victory/defeat, deterministic rewards, combat logs, and combat UI.
- Persistence and regression coverage for combat outcomes.

**Tasks:**
- Complete tasks `CMB-001` through `CMB-005`.

**Acceptance Criteria:**
- Identical inputs and seeds produce identical complete combat results.
- Combat executes with zero AI calls and without network access.
- Rewards are engine-owned and save consistently.
- Victory, defeat, and replayable combat-log tests pass.

**Excluded Future Work:**
- Quest state, NPC schedules, world events, narrative dialogue, and final
  content balancing.

---

## v0.7 World, NPC, and Quest System

**Status:** DONE

**Goal:** Add deterministic exploration content, quests, and NPC entities on
top of stable saves, characters, and combat.

**Scope:**
- Quest Engine state machine and rewards.
- Locations, dungeon state, NPC profiles, schedules, knowledge, factions, and
  numeric relationships.
- Event-driven memory candidates and minimal UI for quests/NPC interaction.

**Tasks:**
- Complete tasks `WQP-001` through `WQP-006`.

**Acceptance Criteria:**
- Only the Quest Engine performs valid quest transitions.
- NPC schedules, relationships, faction state, and dungeon state survive
  save/load.
- Significant actions create canonical memory candidates.
- NPC and world systems function without AI dialogue.

**Excluded Future Work:**
- AI-generated dialogue, lore, full autonomous world simulation, unlimited
  procedural quests, and post-MVP economy/politics.

---

## v0.8 AI Narrative and Dialogue

**Status:** DONE

**Goal:** Add validated, context-grounded narrative content without changing
gameplay authority.

**Scope:**
- NPC dialogue, narration, lore, quest framing, context building, prompt
  versioning, output validation, caching, and non-AI fallback presentation.

**Tasks:**
- Complete tasks `NAR-001` through `NAR-005`.

**Acceptance Criteria:**
- Existing memories, relationships, faction state, and quest context are
  retrieved before generation.
- Invalid or state-changing output is rejected safely.
- The game remains playable when all AI providers are unavailable.
- Playtesting presents a JRPG interface, not a chatbot interface.

**Excluded Future Work:**
- AI-authored rewards or outcomes, free-form text-adventure control, unlimited
  generated content, and final release content.

---

## v0.9 Asset Discovery and License Tracking

**Status:** TODO

**Goal:** Select a legally usable local asset set for the vertical slice.

**Scope:**
- Asset discovery, provenance, license review, attribution, local import,
  cataloging, optimization, and replacement tracking.

**Tasks:**
- Complete tasks `AST-001` through `AST-004`.

**Acceptance Criteria:**
- Every included asset has source, author, license, attribution, and local path
  recorded in `assets/CATALOG.md`.
- Runtime performs no asset downloads.
- Originality/IP review finds no copied protected identity or unlicensed asset.

**Excluded Future Work:**
- Full-game art production, paid asset acquisition, post-MVP regions, and
  cosmetic expansion.

---

## v0.10 Playable Vertical Slice

**Status:** TODO

**Goal:** Integrate the systems into one short, complete browser-playable loop.

**Scope:**
- One bounded region, character creation, exploration, NPC interaction, quest,
  dungeon/combat, rewards, progression, narrative, and save/load.
- Accessibility, performance, error handling, telemetry, and focused content
  polish for the slice.

**Tasks:**
- Complete tasks `VSL-001` through `VSL-005`.

**Acceptance Criteria:**
- A new player can complete the vertical slice entirely in the browser.
- Save/load works at defined checkpoints and after restart.
- The slice remains completable with cloud AI disabled.
- E2E, accessibility, performance, and regression gates pass.

**Excluded Future Work:**
- Full MVP content volume, all regions/quests/NPCs, multiplayer, and broad
  post-MVP simulation.

---

## v1.0 MVP Release

**Status:** TODO

**Goal:** Expand the proven slice to the bounded MVP and produce release
evidence.

**Scope:**
- MVP content within documented limits.
- Hardening, migrations, backup/restore/rollback, security, observability,
  accessibility, legal review, packaging, and release sign-off.
- Minimal deterministic world advancement only after all preceding systems are
  stable.

**Tasks:**
- Complete tasks `MVP-001` through `MVP-006`.

**Acceptance Criteria:**
- All MVP capabilities and content limits are met.
- Required unit, integration, regression, and E2E tests pass at required
  coverage.
- Save compatibility, backup, restore, rollback, security, accessibility,
  legal, observability, and release evidence gates pass.
- `RELEASE_CHECKLIST.md` and every applicable software release gate have
  traceable evidence and approval.

**Excluded Future Work:**
- Multiplayer, shared worlds, player housing/markets, guild wars, full kingdom
  simulation, advanced economy, and content beyond MVP limits.

---

## MVP Content Limits

| Content | Maximum |
|---|---:|
| Regions | 5 |
| Playable races | 4 |
| Starting jobs | 8 |
| NPCs | 50 |
| Quests | 100 |
| Dungeons | 5 |
| World bosses | 1 |
| Factions | 5 |
| World items | 3 |

Target playtime: 20-40 hours per character before major content repetition.
