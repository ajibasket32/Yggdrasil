# Changelog

All notable completed changes are recorded here. Planned work belongs in
`TASKS.md`, not this file.

## [1.2.0-rc.1] - 2026-06-20

### Added
- Content Pipeline: Implemented a deterministic, AI-light content generation pipeline foundation for post-launch expansion packs.
- Ready-to-use Startup: Added beginner-friendly `start-game.ps1`, `verify-ready.ps1`, and `stop-game.ps1` scripts.
- Content Workflow: Added one-command pipeline reporting and safe content import dry-run tooling.
- E2E Coverage: Added a ready-to-use gameplay smoke test path for title, new game, quests, shop, inn, combat, save, and continue.
- Content Tooling: Added `generate_content_pack.py`, `validate_content_pack.py`, `resolve_asset_manifest.py`, and `content_ai_orchestrator.py`.
- Shop System: Merchant Silas added to Valeris with a deterministic item catalog and purchasing flow.
- Inn System: Innkeeper Elena added to Greenwood with a rest mechanic to restore HP and MP for gold.
- Quest Expansion: Expanded "The Blacksmith's Request" and "Scouting the Border" with new multi-step objectives.
- Integration: Automatic quest progression linked to shop purchases and location discoveries.
- UI/UX: New Shop Overlay and updated World Panel with shop/inn action buttons, gold awareness, and feedback banners.
- Persistence: Expanded save/load compatibility to cover new shop-related state and inventory changes.

### Validation
- PR #33 merged real Phaser 2D playability evidence into `main` at `2f1aa46a5c3b06963a8fd118e27104ece0e615a2`.
- Backend tests passed 124/124; frontend tests passed 82/82 with 81.44% branch coverage.
- Ready-to-use E2E and real Phaser 2D playability E2E passed; final audit classification is PASS -- Genuine playable 2D JRPG loop.
- Core runtime health passed; optional cloud AI provider diagnostics may be degraded without credentials, while cached/offline gameplay fallback remains PASS.

## [1.1.0] - 2026-06-18

### Added
- Title Screen: Added "Continue Game" logic with automatic character detection and "New Game" flow.
- JRPG Feel: Authentic JRPG HUD with Kenney RPG UI assets, improved HP/MP bars, and layout.
- Exploration: Added player walk animations (WASD/Arrows) and improved world interaction hints.
- Quest Journal: Redesigned Quest Journal with objective checklists, status cards, and reward previews.
- Combat Polish: Integrated animated damage/healing popups and status effect indicators in the combat scene.
- Content: Expanded world with new NPCs (Blacksmith Hagar, Scout Kael), 3 new quests, 2 new monsters (Giant Wasp, Ancient Sentry), and 3 new items.
- Stability: Refactored frontend test suite into modular flows and reached 85% branch coverage.
- Narrative: Improved quality of AI fallback dialogue and added explicit [OFFLINE] indicators.
- UX: Added save confirmation feedback and improved character-aware continue button.

## [1.0.0] - 2026-06-18

### Added

- Improved 2D JRPG exploration experience in Phaser.
- Tile-based 2D map with keyboard movement (WASD/Arrows) and camera following.
- Interactive NPC, Encounter, and Travel markers in the world scene with proximity hints.
- Enhanced Combat presentation with backgrounds, separate HP bars, damage numbers, and attack animations.
- Bi-directional React ↔ Phaser bridge for location and interaction sync.
- Expanded world content to reach MVP targets: 5 regions, 5 factions, 5 dungeons, and multiple NPCs/Quests.
- World Items: World Stone Fragment, Eternity Bloom, Dragon Scale.
- Comprehensive security audits with `pip-audit` and `npm audit` passing.
- Final documentation and release status for MVP.

### Changed

- Advanced project status to v1.0.0 MVP Release complete.
- Parameterized Dockerfile arguments and `compose.yaml` to allow image overrides (e.g., from AWS ECR public) and prevent Docker Hub 429 rate limit issues during deployment and automated testing.
- Added `release-test.sh` and `release-validation.sh` for non-technical users to validate functionality, featuring a local-only testing fallback mechanism in the event of severe Docker limitations.
- Documented Docker 429 mitigations in the README.md and RELEASE_STATUS.md.

## v0.10.0

### Added

- Phaser 3 integrated into the frontend for World Map and Combat scenes.
- Basic player movement and interaction logic in `WorldScene.ts`.
- Monster sprite rendering (Slime/Goblin) and combat UI in `CombatScene.ts`.
- Kenney RPG UI assets and portraits integrated into character creation and dialogue boxes.
- Explicit "Save Game" and "End Chronicle" functionality in the main HUD.
- Frontend branch coverage increased to 81% through new unit tests and Phaser scene coverage.

### Changed

- UI header and layout updated for the vertical slice experience.
- Migration seeds updated to align with the "Valeria" region and lore.

### Fixed

- `crypto.randomUUID` and `getRandomValues` polyfilled for the Vitest environment.
- Stale combat IDs are now correctly removed if fetching the encounter fails.

## v0.9.0

### Added

- Asset requirements checklist for the v0.10 vertical slice covering UI, characters, monsters, tilesets, items, and backgrounds.
- CC0-licensed asset set from Kenney and OpenGameArt imported into `assets/` and organized in `frontend/src/assets/`.
- Updated `assets/CATALOG.md` with complete provenance, license, and attribution for all selected assets.

### Changed

- Project tasks and release status advanced to reflect v0.9 completion.
- `docs/ASSET_CHECKLIST.md` created to track discovery and selection.

### Known Limitations

- Assets are placeholders for the vertical slice and may be replaced in later stages.
- No audio assets were imported in this release as they are optional for MVP.

## v0.8.0

### Added

- Player-scoped narrative context assembly for character, location, NPC,
  faction, relationship, quest, recent dialogue, and relevant memories.
- Versioned dialogue, lore, quest-framing, and location-description prompts.
- Validated narrative services and APIs with idempotency, canonical context
  hashing, cosmetic record persistence, and context-aware caching.
- Fixed-topic NPC dialogue and JRPG story panels with explicit local-fallback
  and cache presentation.
- Migration `0007_ai_narrative` and unit, integration, regression, API, and
  browser coverage for grounding, safety, fallback, and gameplay isolation.

### Changed

- Backend, frontend, and save engine metadata advanced to `0.8.0`.
- RAG context assembly now merges ranked indexed memories with canonical
  pending memories so Qdrant lag cannot hide relevant history.
- AI validation now rejects prompt-injection reflection, gameplay state
  claims, numeric gain/loss claims, leaked UUIDs, invalid tones, and
  out-of-bound entity references.

### Fixed

- Quest context loading no longer performs one query per active quest step.
- Narrative cache fingerprints now sort entity identifiers and serialize
  canonical JSON for stable reuse across processes.
- Provider and Qdrant outages degrade to approved local narrative while the
  deterministic game remains playable.

### Known Limitations

- Narrative content is deliberately short and bounded to four fixed NPC topics
  plus lore, quest framing, and current-location descriptions.
- Cached idempotent replays preserve text and safety metadata but do not
  reconstruct the original speaker label or memory-count display.
- The seed world remains intentionally small, and production authentication is
  not implemented.

## v0.7.0

### Added

- Pure Quest Engine state transitions, ordered objectives, prerequisite
  validation, and engine-owned XP, gold, and reputation rewards.
- Canonical faction, NPC, quest, relationship, dungeon, journal, and immutable
  world-event persistence through reversible migration `0006`.
- Deterministic NPC profiles, schedules, knowledge, roles, location presence,
  greetings, and explicit help actions without AI.
- Atomic canonical memory candidates and durable Qdrant index jobs for
  significant NPC, quest, faction, and dungeon actions.
- Player-scoped quest, NPC, relationship, faction, dungeon, journal, and world
  APIs with mutation idempotency and transactional outbox records.
- Browser quest journal, NPC action, faction, dungeon, and chronicle panels.
- Unit, integration, regression, deployed API, and browser coverage for quest
  transitions, persistence, authorization, memory creation, and permanent
  world consequences.

### Changed

- Backend, frontend, and save engine metadata advanced to `0.7.0`.
- Save snapshots now capture and restore implemented quest, faction,
  relationship, journal, memory, and dungeon domains.
- The backend image now pins patched `pip 26.1.2`.

### Fixed

- Older saves cannot rewind terminal quests, remove faction membership,
  reduce established relationships, or resurrect a cleared dungeon boss.
- Repeated help actions with new idempotency keys cannot farm relationship
  points, duplicate quest progress, or violate memory deduplication.
- Read-only dungeon views now expose explicit initial boolean state before a
  character enters the dungeon.

### Known Limitations

- NPC schedules are persisted definitions; autonomous time-based movement and
  full world simulation remain excluded.
- NPC interaction is deterministic and menu-driven; AI dialogue and narrative
  presentation belong to v0.8.
- The release contains one bounded quest, NPC, faction, and dungeon path for
  system proof rather than final content breadth.
- `X-Player-ID` remains a development identity boundary.

## v0.6.0

### Added

- Pure deterministic combat engine with seeded initiative, hit, critical,
  damage, elemental, guard, status, escape, enemy-policy, and reward rules.
- Canonical encounter, participant, immutable combat-log, and shared outbox
  persistence through migrations `0004` and `0005`.
- Location encounter discovery and idempotent combat start, action, flee,
  state, and log APIs.
- Browser combat UI with resources, active skills, consumables, guard, wait,
  escape, rewards, status effects, and ordered logs.
- Unit, integration, regression, deployed API, and browser coverage for
  victory, defeat, persistence, retries, ownership, and AI isolation.

### Changed

- Backend, frontend, and save engine metadata advanced to `0.6.0`.
- Character HP/MP/stamina, XP, gold, loot, logs, and outbox events now commit
  through the combat transaction boundary.
- Save creation and loading now fail with `SAVE_ACTIVE_COMBAT` while a
  character has an active encounter.

### Fixed

- Seed definitions now reference the canonical v0.5 item/location UUIDs.
- Healing and barrier skills spend MP and target the acting participant
  without overwriting their updated state.
- Passive skills cannot be submitted as combat actions.
- Failed escape advances deterministic turn/round state before enemy policy.
- Combat outbox storage now uses the canonical shared `outbox_events` contract.

### Known Limitations

- v0.6 supports one player character and one enemy per encounter.
- Party, boss, summon, threat, quest/faction reward, memory-candidate, and
  narrative combat integrations remain future-release work.
- Full combat reconstruction from versioned logs remains post-MVP debt.
- `X-Player-ID` remains a development identity boundary.

## v0.5.0

### Added

- Canonical race, job, skill, character, item, inventory, equipment, location,
  route, and discovery tables with deterministic seed definitions.
- Pure character, progression, inventory, equipment, and navigation engines.
- Atomic and idempotent character creation, XP progression, job unlock/change,
  inventory operations, equipment operations, and route-based travel APIs.
- Canonical character, inventory, equipment, and discovery capture/restore in
  transactional save/load.
- Browser character creation and archive screens for stats, jobs, skills,
  inventory, equipment, and known locations.
- Unit, integration, and regression coverage for deterministic outcomes,
  authorization, persistence, protected items, invalid travel, and AI
  isolation.

### Changed

- Backend and save engine metadata advanced to `0.5.0`.
- Save snapshots now contain and restore implemented canonical character state.
- Development navigation and frontend API proxy now support the v0.5 browser
  flow.

### Fixed

- Re-equipping an item into its current slot is now an idempotent no-op.
- Inventory sorting uses constraint-safe temporary slots before committing its
  deterministic order.
- Invalid route attempts leave the current location unchanged.
- Nginx now re-resolves recreated backend and frontend containers instead of
  retaining stale service addresses.

### Known Limitations

- Combat, quests, NPCs, factions, and narrative integration are not included.
- `X-Player-ID` remains a development identity boundary, not production
  authentication.
- The v0.5 seed catalog is deliberately small and exists to prove systems, not
  final content balance.

## v0.4.0

### Added

- Canonical, player-scoped PostgreSQL memory records with exact logical
  deduplication, typed memory links, soft deletion, and index status tracking.
- Durable memory index jobs processed asynchronously by Celery through Redis.
- Nine Qdrant memory collections, deterministic offline embeddings, retryable
  indexing/deletion, stale-job recovery, and full index rebuild tooling.
- Provider-neutral retrieval contracts with player/entity/tag filtering,
  canonical-row revalidation, weighted ranking, and bounded context packages.
- Redis retrieval caching with per-player generation invalidation.
- RAG worker health, structured logs, and Prometheus metrics.
- Unit, integration, and regression coverage for persistence, retrieval,
  caching, deletion, rebuild, and dependency failure/recovery behavior.

### Changed

- Backend and save engine metadata advanced to `0.4.0`.
- Docker Compose and CI now include the RAG worker and its PostgreSQL, Redis,
  and Qdrant dependencies.
- Memory, observability, and operations contracts now describe the durable
  canonical-to-derived indexing flow.

### Fixed

- Canonical memory commits no longer depend on Redis, Celery, or Qdrant
  availability.
- Retrieval now rechecks PostgreSQL scope and deletion state instead of
  trusting vector payloads.
- Stale or undispatched index jobs are recoverable without losing memory data.
- The corrupted CI workflow was restored as valid YAML with the current
  release gates.

### Known Limitations

- Memory capture uses synthetic infrastructure inputs; gameplay systems do not
  emit memories yet.
- The deterministic feature-hash embedder is suitable for offline development
  and infrastructure tests, not final semantic retrieval quality.
- No NPC dialogue, quest framing, lore generation, relationship mutation, or
  frontend memory UI is included.

## v0.3.0

### Added

- Provider-neutral narrative request, output, adapter, registry, and error
  contracts that cannot encode gameplay state mutations.
- Configured adapters for Gemini, Groq, OpenAI, Anthropic, OpenRouter, Ollama,
  and approved cached narrative templates.
- AI Orchestrator routing with bounded retries, cloud and local timeouts,
  ordered fallback, Redis request budgets, and cached degradation.
- Structured-output validation for schema, entity scope, gameplay authority,
  and secret-like content.
- AI request, provider failure, latency, rejection, fallback, and cached-use
  Prometheus metrics.
- Unit, integration, and regression tests for provider mapping, fallback,
  outages, budgets, validation, isolation, and secret-safe logging.

### Changed

- Backend and save engine metadata advanced to `0.3.0`.
- CI now supplies Redis to backend tests.
- Provider credentials, model IDs, ordering, timeouts, retries, and budgets are
  deployment configuration.

### Fixed

- Provider failures and invalid output now advance through the configured
  chain instead of exposing provider errors to callers.
- Budget service failure and budget exhaustion now fail closed to approved
  cached narrative.
- Provider exception details are excluded from structured failure logs.

### Known Limitations

- The provider layer accepts synthetic narrative requests only and has no
  gameplay, NPC, quest, lore, or frontend integration.
- No cloud provider models or credentials are selected in committed
  configuration.
- Ollama requires an operator-configured local model before it participates in
  fallback.
- Cached templates are intentionally generic and contain no world context.

## v0.2.0

### Added

- SQLAlchemy 2 async persistence, PostgreSQL repositories, and Alembic revision
  `0001_save_system`.
- Complete schema-v1 save snapshots covering character, inventory, equipment,
  world, quest, NPC, faction, relationship, journal, memory, and dungeon state.
- Retry-safe create, list, load, validation, migration, and soft-delete API
  operations.
- SHA-256 integrity checks, monotonic save versions, compatibility migration
  from schema v0, and verified-recovery-point protection.
- Save-specific Prometheus metrics plus unit, integration, and regression
  coverage for restart, concurrency, corruption, rollback, and deletion.

### Changed

- Backend version advanced to `0.2.0`.
- Backend containers now apply migrations before API startup.
- CI now verifies migration downgrade/upgrade and uses Poetry 2.3.4.

### Fixed

- Duplicate retries with the same idempotency key no longer create duplicate
  snapshots.
- Failed final writes roll back the complete save transaction.
- Corrupt and unsupported snapshots now fail closed with stable API errors.
- Updated the Poetry toolchain to remove disclosed dependency
  vulnerabilities.

### Known Limitations

- v0.2 captures empty components until their owning gameplay systems exist.
- Loading returns a validated coherent snapshot; no active gameplay session
  exists yet to consume it.
- `X-Player-ID` is a development identity boundary, not production
  authentication.
- Soft-deleted records are retained for recovery, but no player-facing restore
  endpoint exists yet.

## v0.1.0

### Added

- Mandatory monorepo structure and environment-only baseline configuration.
- Minimal React 18/Vite presentation shell and FastAPI service shell.
- Docker Compose stack for frontend, backend, PostgreSQL, Redis, Qdrant,
  Ollama, and Nginx.
- Dependency-aware health endpoints, request IDs, Prometheus metrics, and
  structured JSON logging.
- Backend unit, integration, and regression tests.
- Frontend component tests and coverage.
- CI jobs for formatting, linting, strict typing, tests, builds, dependency
  audits, container builds, and secret scanning.

### Changed

- Project status advanced from v0.1 planning to v0.1 Foundation complete.

### Fixed

- Corrected IPv4 container health probes for Alpine Nginx.
- Corrected CI setup order so Python environment setup does not require Poetry
  before Poetry is installed.
- Updated frontend and backend dependencies to remove known high and critical
  vulnerabilities.

### Known Limitations

- No gameplay or persistent save functionality exists.
- No database schema or migration exists.
- No AI provider adapters, RAG collections, models, or prompts exist.
- The worker health endpoint reports `degraded` because background workers are
  outside v0.1 scope.
