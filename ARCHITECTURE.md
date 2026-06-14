# ARCHITECTURE.md
# YGGDRASIL CHRONICLES
# System Architecture Document
Version: 2.0 -- Enterprise Edition
Status: Normative
Last reviewed: 2026-06-13

---

## 1. ARCHITECTURE PHILOSOPHY

Yggdrasil Chronicles uses a **layered, event-driven architecture** with strict separation of concerns across eight layers. The architecture is designed to ensure:

- **Gameplay independence from AI** -- all core systems run without AI providers
- **Horizontal scalability** -- each engine can be extracted to a microservice
- **Deterministic game logic** -- identical inputs always produce identical outputs
- **Persistent world state** -- no action is ever silently lost

**The three immutable laws of this architecture:**
```
Game Engine is the authority.
Database is the memory.
AI is the storyteller.
Frontend is the window.
```

Responsibilities must never overlap between layers.

---

## 2. HIGH-LEVEL SYSTEM DIAGRAM

```
+-----------------------------------------------------------------+
|                        Browser Client                           |
|                    React 18 + Phaser 3                          |
|          (Rendering, Input, UI, Game Scene Display)             |
+------------------------+----------------------------------------+
                         | HTTPS / WebSocket
                         v
+-----------------------------------------------------------------+
|                    Nginx Reverse Proxy                          |
|           (TLS Termination, Rate Limiting, Routing)             |
+------------------------+----------------------------------------+
                         |
                         v
+-----------------------------------------------------------------+
|                  FastAPI Application Server                     |
|     API Layer -> Service Layer -> Engine Layer -> Repo Layer      |
+------+--------------+-------------------------------------------+
       |              |
       v              v
+----------+   +--------------------------------------------------+
|  Redis   |   |              PostgreSQL                          |
|  Cache   |   |   (World State, Characters, Quests, Memories)    |
| Sessions |   +--------------------------------------------------+
|   MQ     |
+----------+          v
               +--------------+
               |   Qdrant     |
               |  Vector DB   |
               | (RAG Memory) |
               +--------------+
                         |
                         v
         +-------------------------------+
         |       AI Orchestrator         |
         |   (Provider-Agnostic Layer)   |
         +---+------+------+------+-----+
             |      |      |      |
         Gemini  OpenAI  Groq  Ollama
                         (+ Claude, OpenRouter)
```

---

## 3. SYSTEM LAYERS

### Layer 1 -- Presentation Layer (Frontend)

**Technology:** React 18, TypeScript, Phaser 3, Vite, Zustand

**Responsibilities:**
- Rendering game visuals (Phaser scenes)
- Rendering UI (React components)
- Capturing player input
- Displaying state received from backend
- Managing local UI state only

**Strict prohibitions:**
- May NOT contain gameplay authority
- May NOT calculate damage, XP, or loot
- May NOT call AI providers directly
- May NOT access the database
- May NOT store canonical game state (only display cache)

---

### Layer 2 -- API Layer (FastAPI Routers)

**Technology:** FastAPI, Pydantic v2, JWT

**Responsibilities:**
- HTTP routing and method handling
- Authentication and authorization (JWT)
- Request schema validation (Pydantic)
- Response serialization
- Rate limiting enforcement
- Delegating to Service Layer

**Strict prohibitions:**
- May NOT contain business logic
- May NOT directly query the database (must use repositories)
- May NOT call AI providers
- May NOT modify game state directly

---

### Layer 3 -- Service Layer

**Technology:** Python 3.12+, type-annotated

**Responsibilities:**
- Orchestrating business logic
- Calling Engine Layer for game system operations
- Calling Repository Layer for data access
- Publishing events to the Event Bus
- Coordinating multi-step operations

---

### Layer 4 -- Engine Layer (Game Logic)

**Technology:** Pure Python, fully deterministic

**Sub-engines:**

| Engine | Responsibility |
|---|---|
| `CombatEngine` | Turn management, damage, status effects, victory/defeat |
| `InventoryEngine` | Add/remove/stack/sort items |
| `EquipmentEngine` | Equip/unequip, stat recalculation |
| `QuestEngine` | Quest state machine transitions |
| `ProgressionEngine` | XP, level up, stat growth, skill unlocks |
| `CraftingEngine` | Recipe validation, crafting outcomes |
| `LootEngine` | Loot table resolution |
| `ThreatEngine` | Enemy aggro and targeting |

**Strict prohibition:**
- Engines must **never** call AI
- Engines must be fully deterministic
- Engines must be executable without a network connection

---

### Layer 5 -- World Simulation Layer

**Technology:** Python, event-driven, tick-based

**Responsibilities:**
- Advancing world tick (1 tick = 1 in-game hour)
- Simulating faction behavior
- Simulating kingdom decisions
- Simulating NPC schedules and movement
- Generating world events
- Weather and calendar simulation
- Economy updates

**Design principle:** Runs independently of player actions. Offline advancement must use a persisted tick cursor, deterministic inputs, bounded catch-up batches, idempotent events, and transactional checkpoints. A restart may resume missed ticks; it may never invent elapsed time, replay a tick twice, or silently reset state.

---

### Layer 6 -- Persistence Layer

**Technology:** PostgreSQL 16, SQLAlchemy 2.x (async), Alembic

**Responsibilities:**
- Storing all canonical game state
- Executing all database migrations
- Providing transactional save operations
- Maintaining world history

---

### Layer 7 -- Memory Layer

**Technology:** Qdrant, Redis

**Responsibilities:**
- Vector embedding and storage of world memories
- Semantic similarity search for RAG context retrieval
- Short-term dialogue context (Redis, TTL-based)
- Frequently-accessed memory caching (Redis)

---

### Layer 8 -- Narrative Layer (AI)

**Technology:** AI Orchestrator, Provider Adapters

**Responsibilities:**
- Dialogue generation (NPC speech)
- Lore generation (items, locations, factions)
- Quest text generation
- World narration

**This layer has zero authority over game state.**

### v0.8 Narrative Boundary

`NarrativeContextBuilder` reads player-owned canonical state and combines
PostgreSQL memories with Qdrant-ranked identifiers. `NarrativePromptBuilder`
loads immutable versioned prompt files. `NarrativeService` calls only the AI
Orchestrator, persists validated cosmetic records separately from gameplay
tables, and caches non-dialogue output by prompt version plus canonical context
hash. Fixed frontend topics prevent free-form game-master control. Provider or
retrieval failure falls back to approved local text without blocking gameplay.

---

## 4. FRONTEND ARCHITECTURE

### React Module Structure

```
src/
+-- components/           # Shared reusable UI (Button, Modal, Tooltip...)
|   +-- ui/              # Base design system components
|   +-- game/            # Game-specific UI (HealthBar, ExpBar...)
|   +-- layout/          # Layout components
+-- pages/               # Top-level route pages
|   +-- AuthPage.tsx
|   +-- CharacterPage.tsx
|   +-- GamePage.tsx
|   +-- SavesPage.tsx
+-- scenes/              # Phaser 3 scene classes
|   +-- WorldMapScene.ts
|   +-- CombatScene.ts
|   +-- DungeonScene.ts
|   +-- DialogueScene.ts
+-- systems/             # Frontend game system helpers
|   +-- InputSystem.ts
|   +-- CameraSystem.ts
|   +-- AnimationSystem.ts
+-- hooks/               # Custom React hooks
|   +-- useCharacter.ts
|   +-- useCombat.ts
|   +-- useInventory.ts
+-- services/            # API client (axios wrappers)
|   +-- api.ts           # Axios base client
|   +-- authService.ts
|   +-- characterService.ts
|   +-- combatService.ts
+-- stores/              # Zustand global state
|   +-- useGameStore.ts
|   +-- useCharacterStore.ts
|   +-- useCombatStore.ts
+-- types/               # TypeScript interfaces
|   +-- character.types.ts
|   +-- combat.types.ts
|   +-- world.types.ts
+-- assets/              # Local game assets
```

### React <-> Phaser Communication

```
React Component
    |
    v
GameEventBus (typed EventEmitter)
    |
    v
Phaser Scene
    |
    v (game events back to React via same bus)
Zustand Store
    |
    v
React UI Update
```

Never pass Phaser scene references into React components. Use the event bus only.

---

## 5. BACKEND ARCHITECTURE

### Application Structure

```
backend/app/
+-- api/
|   +-- v1/
|   |   +-- auth.py
|   |   +-- characters.py
|   |   +-- combat.py
|   |   +-- inventory.py
|   |   +-- quests.py
|   |   +-- npcs.py
|   |   +-- world.py
|   |   +-- saves.py
|   +-- dependencies.py   # FastAPI dependency injection
+-- core/
|   +-- config.py         # Pydantic settings (env-based)
|   +-- logging.py        # Structured JSON logging setup
|   +-- security.py       # JWT utilities
|   +-- middleware.py     # Request ID, timing, error handling
|   +-- exceptions.py    # Custom exception classes
+-- models/               # SQLAlchemy ORM models
+-- schemas/              # Pydantic request/response schemas
+-- services/             # Business logic
+-- repositories/         # Database access (SQLAlchemy queries)
+-- engines/              # Game system engines
|   +-- combat/
|   +-- inventory/
|   +-- equipment/
|   +-- quest/
|   +-- progression/
|   +-- world/
+-- rag/
|   +-- embedder.py
|   +-- retriever.py
|   +-- summarizer.py
|   +-- context_builder.py
+-- ai/
|   +-- orchestrator.py
|   +-- adapters/
|   |   +-- base.py       # Abstract provider interface
|   |   +-- openai.py
|   |   +-- gemini.py
|   |   +-- anthropic.py
|   |   +-- groq.py
|   |   +-- openrouter.py
|   |   +-- ollama.py
|   +-- validators/
|       +-- output_validator.py
+-- events/
|   +-- bus.py            # Event bus implementation
|   +-- handlers/         # Event handler functions
|   +-- types.py          # Event type definitions
+-- tasks/                # Celery background tasks
    +-- world_tick.py
    +-- memory_embed.py
    +-- memory_summarize.py
```

---

## 6. COMBAT ENGINE -- DETAILED DESIGN

Combat must be fully deterministic. Given identical inputs, results must be identical.

### Input Contract
```python
@dataclass
class CombatInput:
    combat_id: UUID
    attacker: CombatantState
    target: CombatantState
    action: CombatAction
    skill_id: Optional[UUID]
    item_id: Optional[UUID]
    rng_seed: int  # Seeded RNG for determinism
```

### Output Contract
```python
@dataclass
class CombatResult:
    hit: bool
    damage: int
    crit: bool
    status_effects_applied: list[StatusEffect]
    status_effects_removed: list[StatusEffect]
    attacker_state_delta: StatDelta
    target_state_delta: StatDelta
    events: list[CombatEvent]
    log_entries: list[CombatLogEntry]
```

### Damage Formula
```
Physical Damage:
  base = (attacker.attack * skill.modifier) - target.defense
  crit_multiplier = 1.5 if crit_roll < crit_chance else 1.0
  final = max(1, base * crit_multiplier * elemental_modifier)

Magical Damage:
  base = (attacker.magic_attack * spell.modifier) - target.magic_defense
  final = max(1, base * elemental_modifier * resistance_modifier)
```

### Elemental Interaction Matrix
```
Fire    > Ice        (1.5x)
Ice     > Water      (1.5x)
Lightning > Water   (1.5x)
Holy    > Undead     (2.0x)
Dark    > Holy users (1.5x)
Nature  > Earth      (1.5x)
Arcane  > Barriers   (1.5x)
```

### v0.6 Persistence Boundary

The pure `CombatEngine` accepts immutable participant state, action, seed, and
sequence inputs and performs no database, network, or AI calls.
`CombatService` owns transaction orchestration around:

- `combat_encounters` lifecycle and seeded turn position;
- `combat_participants` snapshot/resources/statuses;
- immutable `combat_log_entries`;
- character HP/MP/stamina, progression, gold, and inventory rewards;
- shared `outbox_events` records for `combat.started`,
  `combat.action_taken`, and `combat.ended`.

Victory state, rewards, logs, and outbox events commit together. Defeat stores
the encounter result and restores canonical character HP to 1. Save creation
and loading are rejected while an encounter is active because active combat is
canonical independent state, not a save-snapshot component.

### v0.7 World Persistence Boundary

The pure `QuestEngine` and `RelationshipEngine` validate state transitions,
ordered objective progress, rewards, and bounded relationship deltas without
database, network, or AI calls. `WorldService` orchestrates one transaction
across:

- quest, faction, relationship, dungeon, journal, and immutable world state;
- character progression and gold rewards;
- canonical PostgreSQL memories and durable Qdrant index jobs;
- shared outbox events for quest, relationship, faction, and dungeon actions;
- idempotency records bound to player, operation, key, and request fingerprint.

NPC interaction is limited to server-issued menu action IDs. NPC profile,
schedule, knowledge, faction, and location data are canonical definitions; AI
is neither called nor consulted in v0.7.

Save capture includes implemented quest, faction, relationship, journal,
memory-reference, and dungeon domains. Restore may fill missing state but must
not rewind terminal quests, remove established faction/relationship outcomes,
or resurrect a permanently cleared dungeon boss.

---

## 7. EVENT BUS ARCHITECTURE

All significant actions must emit events. Events are immutable once created. State changes and outbox records commit atomically. Delivery occurs after commit and is at-least-once, so every consumer must be idempotent.

### Event Flow
```
Player Action Received
         |
         v
   API Layer Validates
         |
         v
   Service Orchestrates
         |
         v
   Engine Executes
         |
         v
   Persist State + Outbox Event
         |
         v
   Commit Transaction
         |
         v
   Publish Event from Outbox
    +----+-----------------------------+
    v        v           v            v
Memory    Journal    Relationship   Analytics
Engine    Engine       Engine        Engine
    |
    v
 PostgreSQL + Qdrant
```

### Required Event Types
```python
class GameEventType(Enum):
    # Character
    CHARACTER_LEVEL_UP = "character.level_up"
    CHARACTER_JOB_CHANGED = "character.job_changed"
    CHARACTER_SKILL_LEARNED = "character.skill_learned"
    # Combat
    COMBAT_STARTED = "combat.started"
    COMBAT_ACTION_TAKEN = "combat.action_taken"
    COMBAT_ENDED = "combat.ended"
    BOSS_DEFEATED = "combat.boss_defeated"
    # Inventory
    ITEM_OBTAINED = "inventory.item_obtained"
    ITEM_DROPPED = "inventory.item_dropped"
    ITEM_USED = "inventory.item_used"
    # Quest
    QUEST_ACCEPTED = "quest.accepted"
    QUEST_STEP_COMPLETED = "quest.step_completed"
    QUEST_COMPLETED = "quest.completed"
    QUEST_FAILED = "quest.failed"
    # NPC
    NPC_DIALOGUE_COMPLETED = "npc.dialogue_completed"
    NPC_RELATIONSHIP_CHANGED = "npc.relationship_changed"
    # World
    WORLD_EVENT_CREATED = "world.event_created"
    FACTION_JOINED = "world.faction_joined"
    DUNGEON_CLEARED = "world.dungeon_cleared"
    MEMORY_CREATED = "memory.created"
```

---

## 8. NPC ARCHITECTURE

### NPC Data Model
```python
@dataclass
class NPCState:
    id: UUID
    name: str
    race_id: UUID
    occupation: str
    faction_id: Optional[UUID]
    location_id: UUID
    personality: PersonalityProfile
    knowledge: KnowledgeSet         # What this NPC knows
    schedule: DailySchedule
    is_alive: bool

@dataclass
class PersonalityProfile:
    archetype: str                  # e.g., "gruff_merchant"
    traits: list[str]               # e.g., ["distrustful", "loyal_to_guild"]
    speech_style: str               # e.g., "formal", "casual", "archaic"
    values: list[str]               # e.g., ["honor", "profit", "family"]

@dataclass
class KnowledgeSet:
    known_locations: list[UUID]
    known_factions: list[UUID]
    known_world_events: list[UUID]
    rumors: list[str]               # Textual rumors NPC can share
```

### NPC Memory Categories
```
SHORT_TERM     -- Current session interactions (Redis, TTL 24h)
LONG_TERM      -- Significant past events (PostgreSQL + Qdrant)
WORLD_EVENTS   -- Major world events NPC learned about
PLAYER_EVENTS  -- History of interactions with this player
FACTION_EVENTS -- Events relevant to NPC's faction
```

### Knowledge Propagation
```
World Event Occurs
       |
       v
Rumor Created
       |
  +----+----------------------+
  v                           v
Nearby NPCs learn         Distant NPCs
immediately              learn after
                         N world ticks
                         (simulating travel time)
```

---

## 9. RAG PIPELINE ARCHITECTURE

```
Dialogue Request Received
          |
          v
   Retrieve NPC Profile
          |
          v
   Retrieve Relationship Values
          |
          v
   Retrieve NPC Long-Term Memories
   (Qdrant semantic search, top 10)
          |
          v
   Retrieve Recent Dialogue
   (Redis, last 10 exchanges)
          |
          v
   Retrieve Active Quest Context
          |
          v
   Retrieve Location Recent Events
          |
          v
   Build Context Package
   (target: 2,000-6,000 tokens)
          |
          v
   Prompt Builder
   (NPC persona + context + player message)
          |
          v
   AI Orchestrator
          |
          v
   Output Validator
   (reject if contradicts world state)
          |
          v
   Store Dialogue in PostgreSQL
          |
          v
   Async: Embed & Store in Qdrant
          |
          v
   Return Response to Frontend
```

### Memory Scoring Formula
```
score = (relevance_score * 0.4)
      + (importance * 0.3)
      + (recency_bonus * 0.2)
      + (relationship_weight * 0.1)

Recency bonus decays by 10% per in-game week.
Memories with importance >= 8 never decay.
```

---

## 10. AI ORCHESTRATOR ARCHITECTURE

```python
class AIOrchestrator:
    """
    Routes AI generation requests through the fallback chain.
    Never called directly -- always through service methods.
    """

    async def generate_dialogue(
        self,
        npc: NPCState,
        context: DialogueContext,
        player_message: str
    ) -> DialogueResponse:
        ...

    async def generate_lore(
        self,
        entity_type: str,
        entity_id: UUID,
        context: LoreContext
    ) -> LoreResponse:
        ...

    async def generate_narration(
        self,
        event: WorldEvent,
        context: NarrationContext
    ) -> NarrationResponse:
        ...
```

### Fallback Chain
```
Default provider order:
Gemini -> Groq -> OpenAI -> Anthropic -> OpenRouter -> Ollama

Each cloud provider:
  configured timeout (maximum 10s), invalid output, or error
     |
     v
  next configured provider

Ollama:
  local timeout (maximum 30s), invalid output, or error
     |
     v
Cached narrative template:
  approved local content; game remains playable
```

Deployment configuration may reorder or disable cloud providers after
compatibility, safety, cost, latency, and validation review. It may not remove
the Ollama and cached-template degradation path.

### Output Validation Rules

AI output is **rejected** and regenerated if it:
- References entities not in the database (hallucinated names)
- Contradicts established world state
- Attempts to modify numeric game values
- Attempts to create or transition gameplay state
- Attempts to grant XP, gold, loot, quest completion, faction reputation, or relationship changes
- Contains out-of-character content (anachronisms, modern references)
- Fails structure schema validation

---

## 11. SAVE SYSTEM ARCHITECTURE

### Save Operation Flow
```
Player Initiates Save
         |
         v
   Acquire Consistent Snapshot Boundary
         |
         v
   Validate Current State
         |
         v
   Begin PostgreSQL Transaction
         |
         +-- Serialize Character State
         +-- Serialize Inventory State
         +-- Serialize Equipment State
         +-- Serialize Quest State
         +-- Serialize World State
         +-- Serialize NPC State
         +-- Serialize Faction State
         +-- Serialize Relationships
         +-- Serialize Journal
         +-- Serialize Memory Index
         +-- Serialize Dungeon State
         |
         v
   Write Snapshot Reference
         |
         v
   Commit Transaction
         |
         v
   Release Snapshot Boundary
```

If any step fails, the transaction rolls back completely. No partial save is ever committed.

A global world pause is not required. Implementations may use transaction isolation, version checks, or a short scoped lock, but the snapshot must represent one coherent world version.

---

## 12. DEPLOYMENT ARCHITECTURE

### Docker Compose Services

```yaml
services:
  nginx:       # Reverse proxy, port 80/443
  frontend:    # React/Vite build, port 3000
  backend:     # FastAPI, port 8000
  postgres:    # PostgreSQL 16, port 5432
  redis:       # Redis 7, port 6379
  qdrant:      # Qdrant, port 6333/6334
  ollama:      # Local LLM, port 11434
  worker:      # Celery worker (world tick, embeddings)
  flower:      # Celery monitoring UI (dev only)
```

### Startup Command
```bash
docker compose up --build
```

All services must start successfully from this single command.

### Health Check Endpoints
```
GET /health              -> System health summary
GET /health/db           -> PostgreSQL connectivity
GET /health/redis        -> Redis connectivity
GET /health/qdrant       -> Qdrant connectivity
GET /health/ai           -> AI provider status
```

---

## 13. SECURITY ARCHITECTURE

- All API keys stored in environment variables only
- No secrets in source code or Docker images
- JWT tokens: 15-minute access, 7-day refresh
- HTTPS enforced via Nginx in production
- Rate limiting: 60 req/min per player, 10 req/min on auth endpoints
- Input validation on all endpoints (Pydantic schemas)
- SQL injection risk controlled through SQLAlchemy ORM/parameterized queries, review, and tests
- Frontend never receives AI provider credentials

---

## 14. SCALABILITY DESIGN

The current monolithic backend is designed to be **extractable** into microservices without requiring a redesign of the game logic.

**Future extraction targets:**
```
World Engine -> Dedicated world simulation service
Combat Engine -> Dedicated stateless combat service
Memory Engine -> Dedicated RAG microservice
AI Orchestrator -> Dedicated AI gateway service
```

The event bus contract remains stable across all extraction paths.

---

## 15. FUTURE SCALABILITY TARGETS

The architecture must support the following without complete redesign:

- 100,000+ NPCs in a single world
- Millions of memory records
- Multiple continents and playable regions
- Multiplayer support (co-op and guild features)
- Real-time world events visible across sessions

---

## 16. LOGGING & OBSERVABILITY

See `OBSERVABILITY.md` for full specification.

Log categories required in all backend code:
```
SYSTEM    DATABASE    COMBAT    QUEST
NPC       AI          RAG       SAVE
ERROR     SECURITY    PERF
```

All logs must be structured JSON. No `print()` statements in production code.

---

## 17. RELEASE READINESS ARCHITECTURE

Every production release must satisfy the gates in `RELEASE_CHECKLIST.md`.

Architecture approval requires:

- Verified layer boundaries
- Deterministic engine behavior
- Transactional save/load compatibility
- Database migration review
- AI provider isolation
- Security review
- Observability for critical workflows
- Backup, restore, and rollback procedures from `OPERATIONS_RUNBOOK.md`

Any architecture exception must be recorded in `TECH_DEBT.md` with priority, risk, mitigation, owner, and target resolution.
