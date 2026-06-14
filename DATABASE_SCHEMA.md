# DATABASE_SCHEMA.md

# YGGDRASIL CHRONICLES

Database Design Specification

Version: 2.0 -- Enterprise Edition
Status: Normative
Last reviewed: 2026-06-14

---

# DATABASE ENGINE

Primary Database:

PostgreSQL 16

Extensions:

uuid-ossp

pgvector is not canonical storage for memory. Qdrant is the authoritative vector store. pgvector may be used only for local experiments or one-off developer tooling.

---

# DESIGN PRINCIPLES

Every entity must:

* Have UUID primary key
* Have created_at
* Have updated_at

No game logic should depend on display names.

Names may change.

UUID never changes.

---

# COMMON FIELDS

All major tables include:

id UUID PRIMARY KEY DEFAULT uuid_generate_v4()

created_at TIMESTAMPTZ NOT NULL DEFAULT now()

updated_at TIMESTAMPTZ NOT NULL DEFAULT now()

All tables must maintain `updated_at` through an application-managed timestamp or database trigger. All foreign keys use UUID references. Display names are mutable and must never be used as identifiers.

Production migrations must be reviewed against `RELEASE_CHECKLIST.md`. Any migration that can affect saved state must include a compatibility plan, rollback plan, and regression tests for save/load.

---

# MVP ENTITY COVERAGE

The MVP schema must include the required entities from `AGENTS.md`:

Player, Character, Race, Job, Skill, Item, Equipment, Inventory, NPC, Faction, Location, Dungeon, Quest, QuestStep, Monster, Boss, Guild, CraftRecipe, WorldEvent, JournalEntry, Relationship, DialogueMemory, WorldMemory, SaveGame, and WorldState.

Where implementation uses normalized table names, the mapping is:

| Required Entity | Canonical Table |
|---|---|
| Equipment | `equipment_slots`, `equipped_items`, item records with equipment type |
| CraftRecipe | `crafting_recipes`, `recipe_ingredients` |
| JournalEntry | `journal_entries` |
| Relationship | `relationships`, `character_factions` |
| DialogueMemory | `memories` rows with `memory_type = 'DIALOGUE_MEMORY'` |
| WorldMemory | `memories` rows with `memory_type = 'WORLD_MEMORY'` |

---

# PLAYERS

Represents user accounts.

Table: players

Fields:

id

username

email

password_hash

last_login

account_status

created_at

updated_at

---

# CHARACTERS

Table: characters

Fields:

id

player_id

name

race_id

gender

alignment

level

experience

skill_points

current_hp

current_mp

current_stamina

strength

dexterity

agility

vitality

intelligence

wisdom

charisma

gold

fame

karma

active_job_id

current_location_id

deleted_at

created_at

updated_at

Relationship:

players

1

->

many

characters

---

# RACES

Table: races

Fields:

id

name

description

lore

category

selectable

base_stats

racial_bonuses

racial_penalties

racial_passives

created_at

updated_at

---

# JOBS

Table: jobs

Fields:

id

name

description

lore

tier

max_level

selectable_at_creation

prerequisites

skill_unlocks

passive_unlocks

stat_modifiers

created_at

updated_at

---

# CHARACTER_JOBS

Table: character_jobs

Fields:

id

player_id

character_id

job_id

job_level

experience

created_at

updated_at

---

# SKILLS

Table: skills

Fields:

id

name

description

mana_cost

cooldown

skill_type

target_type

effect_definitions

created_at

updated_at

---

# JOB_SKILLS

Table: job_skills

Fields:

id

job_id

skill_id

required_level

created_at

updated_at

---

# CHARACTER_SKILLS

Table: character_skills

Fields:

id

character_id

skill_id

skill_level

created_at

updated_at

---

# ITEMS

Master item database.

Table: items

Fields:

id

name

description

lore

item_type

rarity

weight

base_value

base_stats

compatible_slots

is_stackable

max_stack

is_quest_item

is_droppable

required_level

created_at

updated_at

---

# ITEM_STATS

Table: item_stats

Fields:

id

item_id

stat_name

stat_value

created_at

updated_at

---

# INVENTORIES

Table: inventories

Fields:

id

character_id

slot_count

max_weight

created_at

updated_at

---

# INVENTORY_ITEMS

Table: inventory_items

Fields:

id

inventory_id

item_id

quantity

slot_index

unique_instance_id

created_at

updated_at

---

# EQUIPMENT_SLOTS

Table: equipment_slots

Fields:

id

code

name

created_at

updated_at

Examples:

Main Hand

Off Hand

Helmet

Chest

Boots

Ring 1

Ring 2

Artifact

---

# EQUIPPED_ITEMS

Table: equipped_items

Fields:

id

character_id

slot_id

inventory_item_id

created_at

updated_at

---

# NPCS

Table: npcs

Fields:

id

name

race_id

occupation

role

faction_id

home_location_id

personality_profile JSONB

schedule JSONB

knowledge JSONB

is_alive

created_at

updated_at

---

# RELATIONSHIPS

Table: relationships

Fields:

id

player_id

npc_id

character_id

trust

friendship

respect

fear

hatred

loyalty

created_at

updated_at

---

# FACTIONS

Table: factions

Fields:

id

name

description

created_at

updated_at

---

# FACTION_RELATIONSHIPS

Table: faction_relationships

Fields:

id

faction_a_id

faction_b_id

relationship_value

created_at

updated_at

---

# CHARACTER_FACTIONS

Table: character_factions

Fields:

id

player_id

character_id

faction_id

reputation

rank

joined

created_at

updated_at

---

# LOCATIONS

Table: locations

Fields:

id

name

location_type

danger_level

description

is_starting_location

created_at

updated_at

---

# LOCATION_ROUTES

Table: location_routes

Fields:

id

origin_location_id

destination_location_id

travel_cost

requirements

created_at

updated_at

Routes are directed canonical graph edges. Travel succeeds only when the
current location matches `origin_location_id`, the destination matches
`destination_location_id`, and engine-owned requirements pass.

---

# CHARACTER_LOCATION_DISCOVERIES

Table: character_location_discoveries

Fields:

id

character_id

location_id

created_at

updated_at

Discovery is permanent per character and belongs in transactional save/load.
It is not stored as a global flag on a location definition.

---

# MAP_REGIONS

Table: map_regions

Fields:

id

name

description

region_type

created_at

updated_at

---

# DUNGEONS

Table: dungeons

Fields:

id

name

description

location_id

recommended_level

created_at

updated_at

---

# CHARACTER_DUNGEON_STATES

Table: character_dungeon_states

Fields:

id

player_id

character_id

dungeon_id

entered

cleared

boss_alive

cleared_at

created_at

updated_at

An existing `cleared = true` or `boss_alive = false` outcome cannot be
reversed by loading an older save.

---

# MONSTERS

Table: monsters

Fields:

id

name

level

family

max_hp

max_mp

max_stamina

combat_stats JSONB

resistances JSONB

behavior JSONB

reward_experience

reward_gold

loot_item_id

loot_chance_percent

escape_blocked

created_at

updated_at

---

# BOSSES

Persistent named bosses and world bosses. Boss defeat state is permanent and save-compatible.

Table: bosses

Fields:

id

monster_id

name

boss_type

location_id

world_event_id

is_world_boss

is_alive

defeated_at

defeated_by_character_id

created_at

updated_at

---

# MONSTER_SKILLS

Table: monster_skills

Fields:

id

monster_id

skill_id

created_at

updated_at

---

# QUESTS

Table: quests

Fields:

id

title

description

location_id

giver_npc_id

faction_id

minimum_level

prerequisites JSONB

rewards JSONB

repeatable

created_at

updated_at

---

# QUEST_STEPS

Table: quest_steps

Fields:

id

quest_id

sequence

objective_type

target_id

description

required_count

created_at

updated_at

---

# CHARACTER_QUESTS

Table: character_quests

Fields:

id

player_id

character_id

quest_id

status

current_step

step_progress

objectives_complete

rewards_claimed

accepted_at

completed_at

archived_at

created_at

updated_at

---

# WORLD_EVENTS

Immutable significant world outcomes.

Table: world_events

Fields:

id

player_id

character_id

event_type

location_id

faction_id

quest_id

payload JSONB

deduplication_key

created_at

updated_at

# JOURNAL_ENTRIES

Table: journal_entries

Fields:

id

player_id

character_id

quest_id

category

title

body

created_at

updated_at

---

# MEMORIES

Canonical memory table.

Table: memories

Fields:

id

player_id

memory_type

source_entity_type

source_entity_id

summary

importance

world_event_id

entity_id

entity_type

participants

location_id

tags

occurred_at

content_hash

version

status

index_status

deleted_at

created_at

updated_at

`player_id` is mandatory for privacy isolation. `content_hash` supports
deduplication within player, memory type, entity type, and entity identity.
`status` is `ACTIVE` or `DELETED`; `index_status` is `PENDING`, `INDEXED`,
`FAILED`, or `DELETED`. Deletion is canonical in PostgreSQL before derived
cache and Qdrant data are removed.

Partial unique index for active rows:

player_id, memory_type, entity_type, entity_id, content_hash

---

# MEMORY_LINKS

Links memories together.

Table: memory_links

Fields:

id

memory_a_id

memory_b_id

relationship_type

created_at

updated_at

Unique constraint:

memory_a_id, memory_b_id, relationship_type

---

# MEMORY_INDEX_JOBS

Durable, retryable synchronization requests for the rebuildable Qdrant index.
A memory row commits before its job is dispatched to the worker.

Table: memory_index_jobs

Fields:

id

memory_id

operation

status

attempts

max_attempts

next_attempt_at

last_error_code

created_at

updated_at

`operation` is `UPSERT` or `DELETE`. `status` is `PENDING`, `PROCESSING`,
`RETRY`, `COMPLETED`, or `FAILED`. Worker messages contain only the job UUID;
PostgreSQL remains the source of truth if Redis, Celery, or Qdrant is
unavailable.

---

# GUILDS

Guilds are MVP entities because factions, quests, and future multiplayer systems depend on stable guild identity.

Table: guilds

Fields:

id

name

description

guild_type

faction_id

headquarters_location_id

reputation

created_at

updated_at

---

# GUILD_MEMBERS

Table: guild_members

Fields:

id

guild_id

character_id

npc_id

rank

joined_at

created_at

updated_at

---

# DIALOGUE HISTORY

The earlier planned `dialogue_history` table is superseded in v0.8 by
`narrative_records`. Fixed topic identifiers replace free-form `player_text`,
and validated NPC responses use the same cosmetic persistence contract as
lore, narration, and location descriptions.

---

# SAVE_GAMES

Table: save_games

Fields:

id

character_id

save_name

save_version

world_tick

snapshot_reference

snapshot_checksum

schema_version

engine_version

status

deleted_at

created_at

updated_at

---

# GAME_SETTINGS

Table: game_settings

Fields:

id

character_id

setting_name

setting_value

created_at

updated_at

---

# CRAFTING_RECIPES

Table: crafting_recipes

Fields:

id

name

description

crafting_type

created_at

updated_at

---

# RECIPE_INGREDIENTS

Table: recipe_ingredients

Fields:

id

recipe_id

item_id

quantity

created_at

updated_at

---

# WORLD_STATE

Stores global simulation state.

Table: world_state

Fields:

id

world_tick

current_day

current_month

current_year

active_weather

active_season

created_at

updated_at

`snapshot_reference` is a JSONB value containing one complete logical save
snapshot. Schema version 1 contains `character`, `inventory`, `equipment`,
`world_state`, `quest_state`, `npc_state`, `faction_state`, `relationships`,
`journal`, `memories`, and `dungeon_state`. Components may be empty before
their owning gameplay release exists, but none may be omitted from the
versioned contract.

`snapshot_checksum` is the SHA-256 checksum of canonical JSON. `save_version`
is monotonic per player and character. `schema_version` records compatibility
format, `engine_version` records the writer release, and `deleted_at` provides
recoverable soft deletion.

Unique constraint:

player_id, character_id, save_version

---

# IDEMPOTENCY_RECORDS

Stores server-side outcomes for retry-safe critical mutations.

Table: idempotency_records

Fields:

id

player_id

idempotency_key

request_fingerprint

operation

response_status

response_body

expires_at

created_at

updated_at

Unique constraint:

player_id, idempotency_key, operation

---

# AUDIT_LOGS

Append-only security and administrative audit records. Application roles may insert but may not update or delete.

Table: audit_logs

Fields:

id

event_type

actor_id

actor_type

request_id

source_ip_hash

target_type

target_id

details

occurred_at

created_at

updated_at

---

# ENCOUNTER_DEFINITIONS

Location-bound deterministic encounter catalog.

Table: encounter_definitions

Fields:

id

name

location_id

monster_id

difficulty

enabled

created_at

updated_at

---

# COMBAT_ENCOUNTERS

Player-owned canonical combat lifecycle. Only one `ACTIVE` row may exist per
character.

Table: combat_encounters

Fields:

id

player_id

character_id

encounter_definition_id

seed

status (`ACTIVE`, `VICTORY`, `DEFEAT`, `FLED`)

round_number

action_sequence

turn_order JSONB

rewards JSONB

rewards_applied

completed_at

created_at

updated_at

---

# COMBAT_PARTICIPANTS

Immutable identity/stat snapshot plus canonical mutable combat resources.

Table: combat_participants

Fields:

id

encounter_id

source_type

source_id

name

side (`PLAYER`, `ENEMY`)

level

current_hp, max_hp

current_mp, max_mp

current_stamina, max_stamina

combat_stats JSONB

statuses JSONB

guarding

created_at

updated_at

Unique constraint: encounter_id, source_type, source_id

---

# COMBAT_LOG_ENTRIES

Immutable ordered engine results used by the UI and audit path.

Table: combat_log_entries

Fields:

id

encounter_id

sequence

round_number

actor_participant_id

target_participant_id

action_type

outcome JSONB

text

created_at

updated_at

Unique constraint: encounter_id, sequence

---

# OUTBOX_EVENTS

Stores immutable events in the same transaction as canonical state changes. A background publisher delivers them at least once.

Table: outbox_events

Fields:

id

event_type

aggregate_type

aggregate_id

player_id

payload

deduplication_key

occurred_at

published_at

attempt_count

last_error

created_at

updated_at

Consumers must deduplicate by event ID or `deduplication_key`. Application
code must not delete unpublished events.

---

# DATA_DELETION_REQUESTS

Tracks authenticated privacy deletion workflows and restore tombstones.

Table: data_deletion_requests

Fields:

id

player_id

status

requested_at

verified_at

completed_at

tombstone_version

created_at

updated_at

---

# INDEXING STRATEGY

Must Create Indexes On:

characters.player_id

inventory_items.inventory_id

inventory_items.item_id

character_quests.character_id

character_quests.quest_id

relationships.character_id

relationships.npc_id

world_events.location_id

world_events.character_id

world_events.event_type

character_dungeon_states.character_id

character_dungeon_states.dungeon_id

memories.world_event_id

memories.player_id

memories.memory_type

memories.entity_id

memories.location_id

memories.occurred_at

memory_index_jobs.memory_id

memory_index_jobs.status, memory_index_jobs.next_attempt_at

narrative_records.player_id

narrative_records.character_id

narrative_records.npc_id

narrative_records.entity_id

narrative_records.context_hash

idempotency_records.expires_at

audit_logs.event_type

audit_logs.occurred_at

outbox_events.published_at

outbox_events.aggregate_id

combat_encounters.player_id

combat_encounters.character_id

combat_participants.encounter_id

combat_log_entries.encounter_id

encounter_definitions.location_id

encounter_definitions.monster_id

data_deletion_requests.status

All foreign keys and frequently filtered status fields must be indexed before release. Any query expected to run during gameplay must be explainable under the performance targets in `AGENTS.md`.

---

# VALIDATED NARRATIVE RECORDS

`narrative_records` stores cosmetic output separately from canonical gameplay
state. Each row is player- and character-scoped and records:

- optional NPC and required entity identifiers
- narrative kind and fixed topic
- idempotency key and request fingerprint
- prompt version and canonical context hash
- provider/model metadata
- validated text, tone, tags, and referenced entity identifiers
- fallback and cache flags

The table has a unique player/kind/request-key boundary and a context-cache
index. It contains no damage, reward, progression, quest-transition,
relationship-delta, or other writable gameplay fields.

---

# QDRANT COLLECTIONS

npc_memories

player_memories

world_memories

faction_memories

quest_memories

location_memories

dialogue_memories

item_memories

lore_memories

---

# MEMORY EMBEDDING PAYLOAD

{
"memory_id": "...",
"player_id": "...",
"memory_type": "WORLD_MEMORY",
"entity_type": "...",
"entity_id": "...",
"importance": 10,
"tags": [],
"timestamp": "..."
}

---

# FUTURE TABLES (POST-1.0)

guild_wars

auction_house

mail_system

player_housing

mounts

companions

marriage_system

kingdom_simulation

multiplayer_sessions

---

# FINAL DATABASE RULE

If a piece of information can affect future gameplay,
it must be stored.

If it is not stored,
the world cannot remember it.

If it can corrupt or reset saved progress,
the migration is release-blocking until proven safe.
