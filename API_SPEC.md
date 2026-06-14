# API_SPEC.md
# YGGDRASIL CHRONICLES
# Comprehensive API Specification
Version: 2.0 -- Enterprise Edition
Status: Normative
Last reviewed: 2026-06-14

---

## 1. API PHILOSOPHY

The backend is the **single source of authority** for all game state. The frontend is a presentation layer only.

**Immutable rules:**
- All state changes must pass through backend validation
- No AI provider communicates directly with the frontend
- No game state is determined by client-side logic
- All mutations pass through: Validation -> Service -> Engine -> Transactional Persistence + Outbox -> Commit -> Event Publication -> Response

---

## 2. BASE URL & VERSIONING

```
Production:  https://api.yggdrasil.game/api/v1
Development: http://localhost:8000/api/v1
```

Breaking changes require a new API version (`/api/v2`). The previous version is maintained for a minimum of 6 months after a new version is released.

---

## 3. AUTHENTICATION

All endpoints except `/auth/register`, `/auth/login`, and liveness/readiness endpoints require a valid JWT. Metrics and dependency-detail health endpoints are internal-only.

**Header format:**
```
Authorization: Bearer <access_token>
```

**Token lifetimes:**
- Access token: 15 minutes
- Refresh token: 7 days

---

## 4. UNIVERSAL RESPONSE ENVELOPE

All application JSON endpoints return this structure. Prometheus `GET /metrics`, empty `204` responses, file/stream responses, and infrastructure probes are documented exceptions.

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-15T10:30:00Z",
    "api_version": "v1"
  }
}
```

All mutating requests accept an `Idempotency-Key` header. Save, load, combat action, inventory/equipment mutation, quest transition, payment-like future operations, and admin maintenance endpoints must enforce it. The server binds the key to authenticated actor, operation, and request fingerprint; reuse with a different payload returns `409 IDEMPOTENCY_KEY_REUSED`.

**On failure:**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "CHARACTER_NOT_FOUND",
    "message": "No character found with the given ID.",
    "details": {
      "character_id": "550e8400-..."
    }
  },
  "meta": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-15T10:30:00Z",
    "api_version": "v1"
  }
}
```

---

## 5. HTTP STATUS CODES

| Code | Meaning |
|---|---|
| 200 | OK -- successful read or update |
| 201 | Created -- resource created |
| 400 | Bad Request -- invalid input |
| 401 | Unauthorized -- missing or invalid token |
| 403 | Forbidden -- authenticated but lacks permission |
| 404 | Not Found -- resource does not exist |
| 409 | Conflict -- invalid state transition or duplicate |
| 422 | Unprocessable Entity -- schema validation failed |
| 429 | Too Many Requests -- rate limit exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable -- downstream dependency failure |

---

## 6. RATE LIMITING

| Tier | Limit | Scope |
|---|---|---|
| Standard player endpoints | 60 requests / minute | Per user |
| Auth endpoints | 10 requests / minute | Per IP |
| Combat endpoints | 30 requests / minute | Per user |
| AI-backed endpoints | 20 requests / minute | Per user |
| Admin endpoints | Role-restricted | Per admin role |

Rate limit headers included in every response:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705312800
```

---

## 7. AUTH MODULE

### POST /auth/register
Create a new player account.

**Request:**
```json
{
  "username": "string (3-32 chars, alphanumeric + underscore)",
  "email": "string (valid email)",
  "password": "string (min 12 chars; permit long passphrases)"
}
```
**Response:** `201` -- Player account created.

---

### POST /auth/login
Authenticate and receive tokens.

**Request:**
```json
{ "email": "string", "password": "string" }
```
**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 900,
  "player": { "id": "uuid", "username": "string" }
}
```

---

### POST /auth/refresh
Exchange refresh token for new access token.

**Request:**
```json
{ "refresh_token": "string" }
```

---

### POST /auth/logout
Invalidate current session tokens.

---

### GET /auth/me
Return current authenticated player profile.

---

## 8. CHARACTER MODULE

The v0.6 development runtime requires `X-Player-ID` on player-scoped routes
and `Idempotency-Key` on mutations. All paths below are under `/api/v1`.

### GET /character-definitions
Return selectable races, Basic starting jobs, and the canonical starting
location used by character creation.

---

### GET /characters
List all characters for the authenticated player.

**Response:**
```json
{
  "characters": [
    {
      "id": "uuid",
      "name": "string",
      "race": { "id": "uuid", "name": "string" },
      "level": 12,
      "current_job": { "id": "uuid", "name": "string" },
      "current_location": { "id": "uuid", "name": "string" },
      "created_at": "datetime"
    }
  ]
}
```

---

### POST /characters
Create a new character.

**Request:**
```json
{
  "name": "string (2-32 chars)",
  "race_id": "uuid",
  "gender": "string",
  "alignment": "string",
  "starting_job_id": "uuid"
}
```

**Rules:**
- Name must be unique per player
- Race must exist and be available for selection
- Starting job must be a Basic tier job

---

### GET /characters/{characterId}
Get full character sheet.

**Response:**
```json
{
  "id": "uuid",
  "name": "string",
  "level": 12,
  "experience": 45200,
  "experience_to_next": 60000,
  "race": { ... },
  "jobs": [ { "job": {...}, "level": 10, "experience": 8400 } ],
  "stats": {
    "strength": 42,
    "dexterity": 28,
    "agility": 31,
    "vitality": 35,
    "intelligence": 18,
    "wisdom": 22,
    "charisma": 15
  },
  "derived_stats": {
    "max_hp": 520,
    "current_hp": 520,
    "max_mp": 180,
    "current_mp": 180,
    "max_stamina": 100,
    "current_stamina": 100,
    "physical_attack": 87,
    "physical_defense": 45,
    "magic_attack": 32,
    "magic_defense": 38,
    "accuracy": 91,
    "evasion": 23,
    "critical_chance": 8.5,
    "initiative": 31
  },
  "gold": 4200,
  "karma": 120,
  "fame": 880,
  "current_location": { "id": "uuid", "name": "string" }
}
```

---

### PATCH /characters/{characterId}
Update character cosmetic data (name, appearance settings only).

Status: planned; not implemented in v0.6.

---

### DELETE /characters/{characterId}
Request character deletion. Requires recent re-authentication and explicit confirmation.

The character is soft-deleted and inaccessible immediately, then retained for a configurable recovery window of up to 30 days. Final purge must remove derived cache/vector data and preserve only anonymized world-history records where continuity requires it. This endpoint is distinct from account deletion under `DATA_GOVERNANCE.md`.

Status: planned; not implemented in v0.6.

---

### GET /characters/{characterId}/skills
List all skills the character has unlocked.

---

### POST /characters/{characterId}/skills/upgrade
Spend skill points to upgrade a skill.

Status: planned; not implemented in v0.6.

**Request:**
```json
{ "skill_id": "uuid", "target_level": 3 }
```

---

### GET /characters/{characterId}/jobs
List all jobs the character has unlocked with their levels.

---

### POST /characters/{characterId}/jobs/unlock
Unlock a new job (validates prerequisites server-side).

**Request:**
```json
{ "job_id": "uuid" }
```

---

### POST /characters/{characterId}/jobs/change
Change the character's active primary job.

**Request:**
```json
{ "job_id": "uuid" }
```

---

### POST /characters/{characterId}/progression/experience
Apply an engine-authorized deterministic XP event. This endpoint is an
internal gameplay boundary; clients may not invent rewards.

**Request:**
```json
{ "amount": 100 }
```

---

## 9. INVENTORY MODULE

### GET /characters/{characterId}/inventory
Get full inventory contents.

**Response:**
```json
{
  "inventory_id": "uuid",
  "slot_count": 40,
  "used_slots": 14,
  "total_weight": 24.5,
  "max_weight": 100.0,
  "items": [
    {
      "slot_index": 0,
      "item": {
        "id": "uuid",
        "name": "Iron Sword",
        "type": "weapon",
        "rarity": "common",
        "weight": 3.5,
        "value": 150
      },
      "quantity": 1,
      "is_equipped": false
    }
  ]
}
```

---

### POST /inventory/use
Use a consumable item from inventory.

Status: planned; not implemented in v0.6.

**Request:**
```json
{
  "character_id": "uuid",
  "inventory_item_id": "uuid",
  "target_character_id": "uuid"
}
```

---

### POST /inventory/drop
Drop item from inventory into the world.

**Request:**
```json
{
  "character_id": "uuid",
  "inventory_item_id": "uuid",
  "quantity": 1
}
```

Quest items cannot be dropped -- this rule is enforced server-side.

---

### POST /inventory/split-stack
Split a stacked item into two separate stacks.

---

### POST /inventory/merge-stack
Merge two compatible stacks.

---

### POST /inventory/sort
Trigger server-side inventory auto-sort.

---

## 10. EQUIPMENT MODULE

### GET /characters/{characterId}/equipment
Get all equipped items by slot.

**Response:**
```json
{
  "slots": {
    "main_hand": { "item": { ... }, "slot_bonuses": { ... } },
    "off_hand": null,
    "helmet": { "item": { ... }, "slot_bonuses": { ... } },
    "chest": null,
    "boots": null,
    "ring_1": null,
    "ring_2": null,
    "artifact": null
  },
  "total_equipment_bonuses": {
    "strength": 12,
    "physical_attack": 35
  }
}
```

---

### POST /equipment/equip

**Request:**
```json
{
  "character_id": "uuid",
  "inventory_item_id": "uuid",
  "slot_id": "uuid"
}
```

Server validates:
- Item type matches slot type
- Character meets level and stat requirements
- Slot is valid for this item

---

### POST /equipment/unequip

**Request:**
```json
{ "character_id": "uuid", "slot_id": "uuid" }
```

---

### POST /equipment/swap
Swap an equipped item with an inventory item.

Status: planned; not implemented in v0.6.

---

## 11. COMBAT MODULE

Status: implemented in v0.6. Combat mutations require `X-Player-ID` and
`Idempotency-Key`. The game engine resolves all turns, rewards, and status
effects; the API only validates identity/input and returns canonical state.

### GET /characters/{characterId}/encounters

List enabled deterministic encounter definitions at the character's current
location.

### POST /combat/start
Initiate one seeded canonical combat encounter. A character may have only one
active encounter.

**Request:**
```json
{
  "character_id": "uuid",
  "encounter_definition_id": "uuid",
  "seed": 17
}
```

**Response:**
```json
{
  "combat_id": "uuid",
  "encounter_name": "Slime on the Verge",
  "seed": 17,
  "status": "ACTIVE",
  "round_number": 1,
  "action_sequence": 0,
  "turn_order": ["participant-uuid"],
  "participants": [{ "id": "uuid", "side": "PLAYER", "current_hp": 190 }],
  "rewards": { "experience": 0, "gold": 0, "items": [] },
  "recent_log": []
}
```

---

### POST /combat/action
Submit one player action. Deterministic enemy-policy turns are resolved before
the response whenever the enemy is next.

**Request:**
```json
{
  "combat_id": "uuid",
  "action_type": "ATTACK|SKILL|ITEM|GUARD|WAIT",
  "target_id": "uuid | null",
  "skill_id": "uuid | null",
  "inventory_item_id": "uuid | null"
}
```

The response uses the same combat-state contract as `/combat/start`. Completed
states are `VICTORY`, `DEFEAT`, or `FLED`. Victory XP, gold, loot, character
progression, immutable log rows, and outbox events commit atomically.

---

### POST /combat/flee
Attempt seeded escape using the current player and enemy initiative.

**Request:**
```json
{ "combat_id": "uuid" }
```

---

### GET /combat/{combatId}
Get player-owned canonical combat state. Active state survives API/container
restart because encounters and participants are stored in PostgreSQL.

---

### GET /combat/{combatId}/log
Get the full immutable battle log ordered by zero-based `sequence`.

Save creation and save loading return `409 SAVE_ACTIVE_COMBAT` while the
character has an active encounter. This prevents snapshot restoration from
rewinding character state underneath canonical combat participants.

---

## 12. QUEST MODULE

### v0.7 Implemented Profile

- `GET /characters/{characterId}/quests`
- `POST /quests/{questId}/accept`
- `POST /quests/{questId}/submit`
- `POST /quests/{questId}/fail`
- `POST /quests/{questId}/archive`

Every mutation requires `X-Player-ID`, `Idempotency-Key`, and
`{"character_id":"uuid"}`. The Quest Engine is the only component allowed to
transition state. Submit applies database-defined XP, gold, and faction
reputation in the same transaction as quest completion, journal, memory,
world-event, and outbox records.

### GET /quests
List all available quests in the current location.

Status: superseded in v0.7 by the player-scoped character quest listing.

---

### GET /characters/{characterId}/quests
Get all quests for a character with status.

**Response includes quests in all states:** `NOT_STARTED`, `ACTIVE`, `COMPLETED`, `FAILED`, `ARCHIVED`

---

### POST /quests/{questId}/accept

**Request:**
```json
{ "character_id": "uuid" }
```

Validates: character meets level requirement, quest prerequisites satisfied.

---

### POST /quests/{questId}/submit
Submit completed quest for rewards.

Quest rewards are calculated by the Quest Engine from database-defined rewards and deterministic loot tables. AI may generate quest text, but it may never determine reward amounts, completion conditions, or item drops.

**Response:**
```json
{
  "quest": { ... },
  "rewards": {
    "experience": 1200,
    "gold": 500,
    "items": [ { ... } ],
    "faction_reputation": [
      { "faction_id": "uuid", "faction_name": "Adventurer Guild", "delta": 50 }
    ]
  }
}
```

---

## 13. NPC MODULE

### v0.7 Implemented Profile

- `GET /characters/{characterId}/npcs` lists living NPCs at the character's
  current location.
- `GET /npcs/{npcId}/relationship?character_id={characterId}` returns the six
  engine-owned numeric dimensions.
- `POST /npcs/{npcId}/interact` accepts a server-approved `GREET` or
  `OFFER_HELP` action plus `character_id`.

NPC interaction in v0.7 is deterministic and menu-driven. Repeating the same
significant help action cannot farm relationship values, duplicate quest
progress, or create duplicate canonical memories.

### GET /npcs/{npcId}
Get NPC public profile.

Status: planned aggregate profile; v0.7 exposes location-scoped NPC lists.

---

### GET /npcs/{npcId}/relationship
Get relationship values between NPC and current character.

**Response:**
```json
{
  "npc_id": "uuid",
  "character_id": "uuid",
  "trust": 45,
  "friendship": 30,
  "respect": 60,
  "fear": 0,
  "hatred": 0,
  "loyalty": 10
}
```

---

### POST /npcs/{npcId}/dialogue
Generate one validated response to a fixed, server-approved dialogue topic.

Status: implemented in v0.8. Free-form player messages are not accepted.

**Request:**
```json
{
  "character_id": "uuid",
  "topic_id": "GREETING|QUEST|LOCAL_NEWS|FAREWELL"
}
```

**Backend process:**
```
1. Retrieve NPC profile and personality
2. Retrieve relationship values
3. Retrieve NPC long-term memories (Qdrant)
4. Retrieve recent validated dialogue history
5. Retrieve active quest context
6. Build context package
7. Route through AI Orchestrator
8. Validate AI output
9. Store the validated cosmetic narrative record
10. Return response without modifying canonical gameplay state
```

**Response:**
```json
{
  "speaker_name": "string|null",
  "text": "string",
  "tone": "neutral|warm|wary|cautious|solemn|mysterious|quiet|tense|urgent",
  "tags": ["string"],
  "fallback_used": false,
  "cached": false,
  "prompt_version": "npc-dialogue-v1",
  "context_memory_count": 3,
  "available_topics": ["GREETING", "QUEST", "LOCAL_NEWS", "FAREWELL"]
}
```

Related v0.8 cosmetic endpoints:

- `POST /narrative/lore`
- `POST /quests/{questId}/framing`
- `POST /locations/{locationId}/description`

All require `X-Player-ID` and `Idempotency-Key`. AI output and topic selection
never change relationship, quest, faction, reward, combat, inventory, or world
state.

---

### POST /npcs/{npcId}/gift
Give an item to an NPC.

---

### POST /npcs/{npcId}/trade
Open trading interface with NPC merchant.

---

## 14. WORLD MODULE

### v0.7 Implemented Profile

- `GET /characters/{characterId}/world`
- `GET /characters/{characterId}/journal`

The bounded world response includes deterministic nearby NPCs, faction
standing, dungeon state, and immutable world events. `world_tick` remains `0`
until a later release owns autonomous simulation.

### GET /world/map
Get the world map data including discovered regions and locations.

---

### GET /world/state
Get current world simulation state.

**Response:**
```json
{
  "world_tick": 15240,
  "current_day": 120,
  "current_month": 4,
  "current_year": 3,
  "season": "summer",
  "weather": "clear",
  "active_world_events": [ { ... } ],
  "faction_states": [ { ... } ]
}
```

---

### GET /characters/{characterId}/locations
Return canonical locations with per-character `discovered` and current-route
`reachable` flags.

---

### POST /characters/{characterId}/travel
Move the character across one valid directed route and permanently record a
new discovery.

**Request:**
```json
{
  "destination_id": "uuid"
}
```

---

### POST /world/fast-travel
Fast-travel to a previously discovered location.

Status: planned; not implemented in v0.6.

---

## 15. SAVE MODULE

### POST /save
Create a new save game snapshot.

In the pre-authentication v0.2 development runtime, the player boundary is
supplied through the required `X-Player-ID` UUID header. This header is not a
production authentication mechanism and must be replaced by authenticated
identity before a public release.

**Request:**
```json
{
  "character_id": "uuid",
  "save_name": "string (optional)"
}
```

Save operation is transactional. If any component fails, the entire save is rolled back and an error is returned.

`POST /save` must require idempotency handling. Repeating the same request with the same `Idempotency-Key` must return the original save result, not create a duplicate or partial snapshot.

**Response:**
```json
{
  "save_id": "uuid",
  "character_id": "uuid",
  "save_name": "string",
  "world_tick": 15240,
  "save_version": 1,
  "schema_version": 1,
  "engine_version": "0.5.0",
  "status": "VERIFIED",
  "created_at": "datetime"
}
```

---

### GET /saves
List all saves for authenticated player.

---

### POST /load
Load and validate one coherent save snapshot. In v0.6, implemented character,
inventory, equipment, active location, discovery state, and completed combat
outcomes are restored transactionally from the server-owned snapshot. Save
creation and loading are rejected with `SAVE_ACTIVE_COMBAT` while a character
has an active encounter.

**Request:**
```json
{ "save_id": "uuid" }
```

---

### DELETE /save/{saveId}
Soft-delete a save slot. Deletion must be recoverable during the configured recovery window and may not delete the only known-good recovery point while a newer save is unverified.

---

## 16. MEMORY MODULE

### GET /memories/player/{characterId}
Retrieve paginated memory records for a character.

---

### GET /memories/npc/{npcId}
Retrieve NPC memory records relevant to the current character.

---

### GET /memories/world
Retrieve major world memory records (world chronicle).

---

## 17. FACTION MODULE

### v0.7 Implemented Profile

- `GET /characters/{characterId}/factions`
- `POST /factions/{factionId}/join`

Join requires `X-Player-ID`, `Idempotency-Key`, and
`{"character_id":"uuid"}`. Membership is permanent canonical state; quest
reputation is calculated by the engine.

### GET /factions
List all factions and their public standing.

---

### GET /characters/{characterId}/factions
Get character's reputation and rank within each known faction.

---

### POST /factions/{factionId}/join
Join a faction (validates eligibility server-side).

---

## 18. DUNGEON MODULE

### v0.7 Implemented Profile

- `GET /characters/{characterId}/dungeons`
- `POST /dungeons/{dungeonId}/enter`
- `POST /dungeons/{dungeonId}/clear`

Mutations require `X-Player-ID`, `Idempotency-Key`, and
`{"character_id":"uuid"}`. Clear validates location and level, permanently
sets the dungeon cleared and boss dead, progresses matching quest objectives,
and creates world-event, memory, index-job, and outbox records atomically.
Loading an older save cannot resurrect the boss.

### GET /dungeons/{dungeonId}
Get dungeon information including difficulty and boss status.

**Response includes:**
- `boss_alive: bool` -- boss defeat is permanent
- `is_cleared: bool` -- character has cleared this dungeon
- `recommended_level: int`

---

### POST /dungeons/{dungeonId}/enter
Enter a dungeon instance.

---

## 19. AI ORCHESTRATION MODULE

**Internal use only. Not accessible to frontend clients.**

### GET /ai/providers/status
Get health status of all configured AI providers.

**Response:**
```json
{
  "providers": [
    {
      "name": "gemini",
      "healthy": true,
      "latency_ms": 420,
      "success_rate": 99.2,
      "last_checked": "datetime"
    },
    {
      "name": "ollama",
      "healthy": true,
      "latency_ms": 1840,
      "success_rate": 100.0,
      "last_checked": "datetime"
    }
  ],
  "active_provider": "gemini",
  "fallback_available": true
}
```

---

### POST /ai/providers/reload
Reload provider configuration without restart.

---

## 20. SYSTEM & HEALTH MODULE

### GET /health
Overall system health check.

**Response:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "qdrant": "healthy",
    "ai_primary": "healthy",
    "ai_fallback": "healthy"
  },
  "request_id": "uuid"
}
```

`GET /health` is a shallow public readiness summary and must not expose versions, topology, provider names, world state, or dependency error details in production. Detailed endpoints under `/health/*` require internal network access or an authenticated internal role.

---

### GET /metrics
Prometheus-compatible metrics endpoint. Protected by internal network access.

---

## 21.1 ACCOUNT DATA MODULE

### GET /account/export

Create an authenticated, rate-limited data export job. The downloadable artifact must be encrypted, expire automatically, and omit secrets and internal security controls.

### POST /account/deletion-requests

Create an account deletion request. Requires recent re-authentication and records an auditable tombstone so deleted data is not resurrected during restore.

### POST /account/deletion-requests/{requestId}/cancel

Cancel a pending deletion during the configured recovery window.

---

## 22. ADMIN MODULE

Admin endpoints require `admin` role claim in JWT.

Admin endpoints are production-risk operations. They must emit audit logs, require request IDs, enforce authorization, and support dry-run mode where practical.

### GET /admin/world
Full world simulation status.

### POST /admin/force-world-tick
Manually advance world simulation by N ticks.

### POST /admin/rebuild-memory
Re-embed all memories into Qdrant (maintenance operation).

### POST /admin/reindex-qdrant
Full reindex of Qdrant collections.

---

## 23. EVENT BUS CONTRACT

Every gameplay action must emit one or more events to the internal event bus. These events are consumed by downstream engines.

### Required Events

| Event | Published By | Consumed By |
|---|---|---|
| `character.level_up` | Progression Engine | Journal, Memory, Achievement |
| `combat.boss_defeated` | Combat Engine | Memory, World, Journal, Achievement |
| `quest.completed` | Quest Engine | Reward, Memory, Journal, World |
| `npc.relationship_changed` | NPC Service | Memory, AI Context Cache |
| `world.event_created` | World Engine | Memory, Journal, NPC Knowledge |
| `inventory.item_obtained` | Inventory Engine | Journal, Achievement |
| `memory.created` | Memory Engine | Qdrant Embedder |

---

## 24. FINAL API CONTRACT

**No API endpoint may directly write to the database without passing through:**

```
Request Validation (Pydantic)
         v
Authorization Check (JWT + permission)
         v
Service Layer (business logic)
         v
Engine Layer (game rules)
         v
Repository + Transactional Outbox
         v
Commit Canonical State
         v
Event Publisher (post-commit delivery)
         v
Response
```

Outbox consumers must be idempotent. Endpoints that skip required layers or publish side effects before canonical state commits are architecturally invalid and must be refactored.
