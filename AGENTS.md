# AGENTS.md
# YGGDRASIL CHRONICLES
# AI Agent & Contributor Guidelines
Version: 2.0 -- Enterprise Edition
Status: Normative
Last reviewed: 2026-06-13

---

## 1. PROJECT IDENTITY

Yggdrasil Chronicles is a **browser-based JRPG** inspired by the MMORPG world of Yggdrasil from *Overlord*.

This is a **real game**, not a chatbot. Not an AI roleplay simulator. Not a text adventure.

The game engine is the single source of truth for all gameplay state. AI is a narrative enhancement layer only. Every feature must be playable without AI.

### Documentation Authority Order

When documents conflict, resolve them in this order:

1. `AGENTS.md` - architectural law, AI boundaries, contributor rules
2. `ARCHITECTURE.md` - system layering and runtime boundaries
3. `DATABASE_SCHEMA.md`, `API_SPEC.md`, `CODING_STANDARDS.md`, `SECURITY_GUIDELINES.md`, `TESTING_STRATEGY.md` - implementation contracts
4. System design documents such as `COMBAT_DESIGN.md`, `JOB_SYSTEM.md`, and `RAG_DESIGN.md`
5. Governance and operational documents such as `DOCUMENTATION_GOVERNANCE.md`, `DATA_GOVERNANCE.md`, `SERVICE_LEVEL_OBJECTIVES.md`, `ACCESSIBILITY.md`, `SECURITY.md`, `OBSERVABILITY.md`, `OPERATIONS_RUNBOOK.md`, `RELEASE_PROCESS.md`, `RELEASE_CHECKLIST.md`, and `CONTRIBUTING.md`
6. Planning and status documents such as `MVP_ROADMAP.md`, `TASKS.md`, `RELEASE_STATUS.md`, `RELEASE_NOTES.md`, `CHANGELOG.md`, `TECH_DEBT.md`, and `RISK_REGISTER.md`
7. Lore documents such as `WORLD_BIBLE.md` and `PRODUCT_VISION.md`

Lower-priority documents must be updated when higher-priority contracts change.

---

## 2. PRIMARY DESIGN LAW

```
ENGINE FIRST. AI SECOND. ALWAYS.
```

| Authority Layer | Responsibility |
|---|---|
| Game Engine | Damage, XP, loot, progression, quest state, combat outcomes |
| Database | World state, persistence, history |
| AI | Dialogue, lore, narration, descriptions |
| Frontend | Rendering, input handling, UI display |

These boundaries are absolute. Violating them creates architectural debt that cannot be accepted.

---

## 3. ABSOLUTE PROHIBITIONS -- AI MUST NEVER

AI systems are **strictly prohibited** from determining or influencing:

- Damage values (physical or magical)
- Experience point rewards
- Gold or currency rewards
- Loot table outcomes or item drops
- Combat turn order or combat results
- Skill effects or skill activation outcomes
- Item or equipment base statistics
- Level-up stat allocations
- Crafting results or success/failure rates
- Quest completion conditions or quest rewards
- Character progression milestones

Violation of any of the above is a **critical bug**, not a design choice.

---

## 4. AI PERMITTED RESPONSIBILITIES

AI may generate the following **narrative content only**:

- NPC dialogue (greetings, story dialogue, reactions)
- Item lore and flavor text
- Quest descriptions and story framing
- City, region, and dungeon atmospheric descriptions
- Books, journals, and in-world readable texts
- Rumors and gossip spread between NPCs
- Faction propaganda and political messaging
- Story narration (intro, chapter breaks, epilogues)
- World event narration (after-action storytelling)
- Codex and encyclopedia entries
- Victory and defeat narration (cosmetic only)
- Boss introduction monologues (cosmetic only)

**AI output must never write directly to game state.** All AI output must pass through validation before any storage.

---

## 5. TARGET GAME FEEL

### Should feel like:
- Final Fantasy IX
- Suikoden II
- Breath of Fire IV
- Golden Sun
- Dragon Quest XI

### Must NOT feel like:
- ChatGPT RPG
- AI Dungeon
- Character AI
- Interactive fiction / text adventure chatbot

If a playtester describes the game as "an AI chatbot," that is a design failure.

---

## 6. TARGET TECHNICAL STACK

### Frontend
| Technology | Purpose |
|---|---|
| React 18+ | UI, menus, HUD, inventory, journal |
| TypeScript (strict) | All frontend code |
| Vite | Build tooling |
| Phaser 3 | Game scenes, maps, movement, combat animations |
| Zustand | Global state management |

### Backend
| Technology | Purpose |
|---|---|
| FastAPI | REST API, routing, auth |
| Python 3.12+ | All backend code |
| SQLAlchemy 2.x | ORM |
| Alembic | Database migrations |
| Celery + Redis | Background task queue |
| Pydantic v2 | Schema validation |

### Infrastructure
| Technology | Purpose |
|---|---|
| PostgreSQL 16 | Primary relational database |
| Redis 7 | Cache, sessions, message broker |
| Qdrant | Vector database for RAG memory |
| Docker + Docker Compose | Containerization |
| Nginx | Reverse proxy |
| Ollama | Local LLM for offline fallback |

### AI Providers (via abstraction layer)
- OpenAI
- Google Gemini
- Anthropic
- Groq
- OpenRouter (multi-model routing)
- Ollama (local, offline fallback)

**All AI calls must pass through the AI Orchestrator. No direct provider calls permitted outside adapter files.**

Concrete model IDs are deployment configuration, not architectural contracts. Model changes require compatibility, safety, cost, latency, and output-validation evaluation.

---

## 7. MANDATORY PROJECT STRUCTURE

```
yggdrasil-chronicles/
+-- frontend/
|   +-- src/
|       +-- components/       # Reusable UI components
|       +-- pages/            # Route-level page components
|       +-- scenes/           # Phaser game scenes
|       +-- systems/          # Frontend game system logic
|       +-- hooks/            # Custom React hooks
|       +-- services/         # API client services
|       +-- stores/           # Zustand state stores
|       +-- types/            # TypeScript interfaces
|       +-- assets/           # Static assets
+-- backend/
|   +-- app/
|       +-- api/              # Route handlers (no business logic)
|       +-- core/             # Config, logging, middleware
|       +-- models/           # SQLAlchemy ORM models
|       +-- schemas/          # Pydantic request/response schemas
|       +-- services/         # Business logic layer
|       +-- repositories/     # Database access layer
|       +-- engines/          # Game systems (combat, quest, inventory...)
|       +-- rag/              # Memory retrieval, embeddings
|       +-- ai/               # Provider adapters, orchestrator
|       +-- events/           # Event bus, event handlers
+-- database/
|   +-- migrations/           # Alembic migration files
|   +-- seeds/                # Seed data scripts
+-- docker/
|   +-- frontend/
|   +-- backend/
|   +-- nginx/
+-- docs/                     # Supplemental docs, diagrams, archives
+-- assets/                   # Raw game assets (sprites, audio, maps)
+-- tests/
|   +-- unit/
|   +-- integration/
|   +-- e2e/
+-- tools/                    # Developer scripts and utilities
+-- shared/                   # Shared types/contracts (frontend + backend)
```

Root-level Markdown files listed in the Documentation Authority Order are canonical project contracts. Do not duplicate them into `docs/` unless the duplicate is generated or clearly marked non-canonical.

---

## 8. GAMEPLAY DEVELOPMENT PRIORITY ORDER

This order is non-negotiable. Never build a subsequent layer before a prior one is stable.

| Priority | System | Reason |
|---|---|---|
| 1 | Save System | Without saves, nothing persists |
| 2 | Character System | Foundation of all gameplay |
| 3 | Inventory | Required for item gameplay |
| 4 | Equipment | Requires inventory |
| 5 | Map & Navigation | Requires character position |
| 6 | Combat | Requires characters + enemies |
| 7 | Quest System | Requires combat + exploration |
| 8 | NPC System | Requires quests + location |
| 9 | AI Narrative | Requires NPC system |
| 10 | Dynamic World | Requires all prior systems |

---

## 9. WORLD PERSISTENCE RULES

The world is **permanently persistent**. No silent resets. No "convenient" respawns.

| Event | Expected Behavior |
|---|---|
| Player kills a boss | Boss remains dead permanently |
| Player burns a village | Village remains burned |
| Player joins a faction | Faction relationship persists forever |
| Player steals an artifact | NPC remembers, consequences persist |
| Player defeats a world boss | World event created, chronicle updated |

Any feature that "resets" world state without player-initiated action is a bug.

---

## 10. DATABASE DESIGN RULES

Every entity in the database must have:
- `id` -- UUID, primary key, generated by `uuid-ossp`
- `created_at` -- UTC timestamp
- `updated_at` -- UTC timestamp, auto-updated on change

Display names are **never** used as primary keys. Names change. UUIDs do not.

---

## 11. REQUIRED ENTITY LIST

The following entities must exist in the database schema at MVP:

`Player` , `Character` , `Race` , `Job` , `Skill` , `Item` , `Equipment`
`Inventory` , `NPC` , `Faction` , `Location` , `Dungeon` , `Quest` , `QuestStep`
`Monster` , `Boss` , `Guild` , `CraftRecipe` , `WorldEvent` , `JournalEntry`
`Relationship` , `DialogueMemory` , `WorldMemory` , `SaveGame` , `WorldState`

---

## 12. SYSTEM DESIGN RULES

### Character System
- Progression must be fully deterministic
- No AI involvement in stat calculation
- All character data stored in PostgreSQL

### Race System
Every race definition must include: `description`, `lore`, `racial_bonuses`, `racial_penalties`, `racial_passives`. No hardcoded race logic in UI components.

### Job System
Every job definition must include: `prerequisites`, `skill_unlocks`, `passive_unlocks`, `stat_modifiers`. The job tree must support branching, multiple requirements, and future expansion without schema changes.

### Skill System
Every skill must define: `skill_id`, `name`, `description`, `mana_cost`, `cooldown`, `target_type`, `effect_definitions`. Skill effects belong to the engine. Descriptions belong to AI.

### Combat System
- Must be fully deterministic
- Identical inputs must always produce identical outputs
- Zero AI calls during combat calculations
- Must be executable in offline mode

### Inventory System
Supports: stackable items, unique items, quest items (non-droppable), sorting, filtering. Inventory state must always be saveable atomically.

### Item System
Every item requires: `item_id`, `rarity`, `type`, `base_stats`, `weight`, `value`, `lore`. Lore: AI-generated. Stats: engine-generated. No exceptions.

### Quest State Machine
```
NOT_STARTED -> ACTIVE -> COMPLETED
                    \-> FAILED -> ARCHIVED
```
No other states permitted. Only the Quest Engine may transition quest states.

### NPC System
Every NPC must have: `UUID`, `persistent_memory`, `relationship_values`, `faction`, `personality_profile`, `schedule`. NPC memory persists forever.

### Relationship System
Track: `trust`, `friendship`, `respect`, `fear`, `hatred`, `loyalty`. All stored as numeric values. AI reads values. AI never modifies values.

---

## 13. MEMORY SYSTEM

All significant player actions must create memory records.

Examples of memory-worthy events:
- Player defeats named boss
- Player steals from an NPC
- Player marries a noble
- Player becomes guild leader
- Player causes or prevents a world event

All memories must be:
1. Stored in PostgreSQL (`memories` table)
2. Embedded and indexed in Qdrant (vector search)

---

## 14. RAG RETRIEVAL RULES

Before any AI generates dialogue, quest text, lore, or story content, the system **must** retrieve:
- Relevant world memories
- Relevant NPC-specific memories
- Relevant faction memories
- Current quest context

Never generate narrative from empty context when memories exist.

---

## 15. SAVE SYSTEM CONTRACT

A valid save must include:
`Character` , `Inventory` , `Equipment` , `World State` , `Quest State`
`NPC State` , `Faction State` , `Relationships` , `Journal` , `Memories` , `Dungeon State`

All save operations must be **transactional**. No partial saves. A failed save must roll back completely.

Save compatibility is a release gate. Any schema or engine change that affects saved data must define migration, rollback, and regression-test coverage before merge.

---

## 16. PERFORMANCE TARGETS

| System | Target |
|---|---|
| Frontend frame rate | 60 FPS |
| API average response time | < 200ms (p95) |
| API max response time | < 1000ms (p99) |
| Database query time | < 50ms for indexed queries |
| Memory retrieval (Qdrant) | < 500ms |
| AI generation timeout | 10s (then fallback) |

---

## 17. AI PROVIDER INDEPENDENCE

The game must function when any single AI provider fails. All AI calls route through the AI Orchestrator.

**Fallback chain (default):**
```
Gemini -> Groq -> OpenAI -> Anthropic -> OpenRouter -> Ollama -> Cached Narrative
```

Offline mode via Ollama must always be supported. No AI provider-specific code may exist outside the `/ai/adapters/` directory.

---

## 18. ASSET RULES

- All assets must be local -- no runtime downloads during gameplay
- Permitted sources: Kenney, OpenGameArt, CC0, Public Domain
- All downloaded assets must be catalogued in `/assets/CATALOG.md`

---

## 19. TESTING REQUIREMENTS

Every system requires:
- Unit tests (logic in isolation)
- Integration tests (system interactions)
- Regression tests (preventing reintroduction of fixed bugs)

No feature is considered **Done** until all three exist and pass.

Minimum coverage: **80%**. Target: **90%+**.

---

## 20. DEFINITION OF DONE

A feature is **Done** only when all of the following are true:

- [ ] Implemented according to architecture
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] Documented (public interfaces, complex logic)
- [ ] Save-system compatible
- [ ] Docker-compatible
- [ ] No secrets committed
- [ ] Code review approved
- [ ] No direct AI provider calls outside adapters
- [ ] No business logic in controllers or UI components
- [ ] Observability added for critical paths
- [ ] Security and authorization reviewed
- [ ] Release checklist impact reviewed

---

## 21. AGENT & AI CODE GENERATOR RULES

Any AI agent (Claude Code, Cursor, Copilot, OpenHands, Codex, or similar) operating on this codebase must:

1. Read and comply with `CODING_STANDARDS.md` before generating any code
2. Read and comply with `ARCHITECTURE.md` before creating any new module
3. Never generate code that bypasses the Game Engine for gameplay outcomes
4. Never generate code that calls AI providers directly (must use Orchestrator)
5. Never generate code that accesses the database from controllers
6. Never generate code with hardcoded secrets or API keys
7. Generated code that violates these rules must be rejected and regenerated
8. Update every affected Markdown contract when behavior, schema, API, release gates, or operational requirements change
9. Treat save corruption, direct AI gameplay influence, and world-state reset behavior as release-blocking critical defects

---

## Release-Based Development Workflow

- This repository uses release-based development.
- `MVP_ROADMAP.md` is the source of truth for release order.
- `TASKS.md` is the source of truth for task status.
- `CHANGELOG.md` is the source of truth for completed changes.
- `RELEASE_NOTES.md` is the source of truth for user-facing release summaries.
- Work only on the first unfinished release.
- Do not implement future release features.
- Do not rewrite documentation unless needed by the current release.
- Do not mark a release complete unless its acceptance criteria pass.
- Stop after completing one release.

Follow `RELEASE_PROCESS.md` for release selection, execution, evidence, reporting,
and the mandatory stop condition. Early AI-provider and memory releases are
infrastructure-only; they do not authorize AI narrative integration or any AI
influence over gameplay.

---

## 22. ENTERPRISE RELEASE LAW

A release is blocked if any of the following are true:

- Player progress can be silently lost, reset, or partially saved
- AI can influence deterministic gameplay outcomes
- Database migrations cannot be verified against save/load flows
- Secrets, credentials, or provider keys are present in committed files
- Tests, security scans, observability, backup, restore, or rollback gates are incomplete

`RELEASE_CHECKLIST.md` is mandatory for public, stakeholder, or packaged releases.

Release approval also requires:

- traceable evidence for every completed critical gate
- SBOM, dependency/license scan, secret scan, and build provenance
- documented ownership and sign-off
- tested RPO/RTO, backup, restore, rollback, and data-deletion behavior
- current data inventory, risk register, and accepted-exception register

Unchecked gates, missing evidence, expired exceptions, or unowned release-significant risks block release.

---

## Documentation Release Quality Gate

- `RELEASE_CHECKLIST.md` is the only source of truth for whether Markdown docs are clean.
- Do not use subjective standards such as enterprise grade, best practice, or production ready unless mapped to a checklist item.
- Do not invent new documentation requirements during audit.
- Do not create new Markdown files unless required by `RELEASE_CHECKLIST.md`.
- Do not rewrite stable content only for tone, wording, or style.
- Fix only concrete checklist failures.
- Optional improvements are not release blockers.
- Every documentation audit must update `DOCUMENTATION_AUDIT.md`.
- Each audit item must include status, evidence, affected file/section, and minimal fix if failed.
- If all applicable checklist items pass, output exactly:

`NO CHANGES REQUIRED — RELEASE CHECKLIST PASSED.`

---

## 23. FINAL LAW

```
Build a JRPG.
Do not build a chatbot.

If there is ever a conflict between GAMEPLAY and AI:
Always choose GAMEPLAY.
```
