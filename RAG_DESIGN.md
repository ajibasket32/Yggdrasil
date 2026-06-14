# RAG_DESIGN.md

# YGGDRASIL CHRONICLES

Retrieval Augmented Generation Architecture

Version: 2.0 -- Enterprise Edition
Status: Normative
Last reviewed: 2026-06-13

---

# PURPOSE

The RAG system exists to provide long-term memory for:

* NPCs
* Factions
* Locations
* Quests
* World History
* Player Actions

Without RAG, AI providers will forget information.

Without memory, the world cannot remain consistent.

The purpose of RAG is to make the world remember.

---

# CORE PHILOSOPHY

The AI does not remember.

The database remembers.

The AI only receives memories when needed.

---

# DESIGN GOALS

1. Long-Term Memory

NPCs remember years of history.

---

2. Consistent Lore

Generated content must remain consistent.

---

3. Cheap Token Usage

Never send entire save files to AI.

---

4. Scalable

Must support millions of memories.

---

5. Provider Independent

Works with:

Gemini

OpenAI

Anthropic

Groq

OpenRouter

Ollama

---

# MEMORY HIERARCHY

Not all memories are equal.

Memories are stored in layers.

---

LAYER 1

SHORT TERM MEMORY

Purpose:

Recent conversation context.

Lifetime:

Current session.

Examples:

Last 20 dialogue exchanges.

Storage:

Redis

---

LAYER 2

ACTIVE MEMORY

Purpose:

Recently important events.

Lifetime:

Several game days.

Examples:

Recent quest completion.

Recent faction changes.

Storage:

PostgreSQL + Qdrant

---

LAYER 3

LONG TERM MEMORY

Purpose:

Permanent world memory.

Lifetime:

Forever.

Examples:

Defeated Dragon King.

Founded Guild.

Destroyed City.

Storage:

PostgreSQL + Qdrant

---

LAYER 4

WORLD HISTORY

Purpose:

Major historical records.

Lifetime:

Forever.

Examples:

Wars.

Kingdom collapse.

Legendary heroes.

Storage:

PostgreSQL

Qdrant

World Chronicle

---

# MEMORY TYPES

PLAYER_MEMORY

NPC_MEMORY

FACTION_MEMORY

QUEST_MEMORY

LOCATION_MEMORY

WORLD_MEMORY

DIALOGUE_MEMORY

ITEM_MEMORY

LORE_MEMORY

---

# MEMORY OBJECT

Every memory contains:

{
"id": "",
"memory_type": "",
"summary": "",
"importance": 1,
"participants": [],
"location": "",
"timestamp": "",
"tags": []
}

---

# IMPORTANCE SCALE

1

Trivial

Example:

Bought Bread

---

3

Minor

Example:

Helped Merchant

---

5

Significant

Example:

Completed Quest

---

7

Major

Example:

Joined Guild

---

9

Legendary

Example:

Defeated Ancient Dragon

---

10

World Changing

Example:

Destroyed Kingdom

---

# MEMORY CREATION PIPELINE

Player Action

v

Event Generated

v

Event Stored

v

Memory Candidate Created

v

Canonical Memory Committed to PostgreSQL

v

Durable Index Job Committed

v

Celery Job ID Dispatched Through Redis

v

Importance Scored

v

Embedded

v

Stored in Qdrant

v

Linked to Entities

If dispatch or indexing fails, the canonical memory remains available in
PostgreSQL and the durable job remains retryable. A recovery task re-announces
unqueued, due, and stale jobs. Qdrant is always derived and can be recreated
from active PostgreSQL rows.

---

# MEMORY EXAMPLES

Player kills Goblin.

Importance

1

May be discarded according to the approved memory-retention policy.

---

Player defeats Goblin King.

Importance

8

Stored permanently.

---

Player becomes Guild Master.

Importance

9

Stored permanently.

---

Player destroys kingdom.

Importance

10

Stored permanently.

---

# MEMORY LINKING

Memories are connected.

Example

Memory A

Joined Adventurer Guild

v

Memory B

Promoted to Rank C

v

Memory C

Promoted to Rank B

v

Memory D

Guild Master

Creates narrative continuity.

---

# MEMORY GRAPH

Entities form a graph.

Player

v

Guild

v

Quest

v

NPC

v

Location

v

World Event

Retrieval uses graph relationships.

---

# QDRANT COLLECTIONS

player_memories

npc_memories

world_memories

faction_memories

quest_memories

location_memories

dialogue_memories

item_memories

lore_memories

---

# EMBEDDING STRUCTURE

Text

v

Embedding Model

v

Vector

v

Qdrant Storage

Payload:

memory_id

entity_id

importance

tags

timestamp

location

The v0.4 infrastructure uses a versioned deterministic local feature-hash
embedder so tests, offline development, rebuilds, and provider independence do
not require an external embedding provider. Replacing it with a deployment
embedding model requires a full controlled reindex and compatibility review.

---

# RETRIEVAL PROCESS

User Talks To NPC

v

Retrieve NPC

v

Retrieve Relationship

v

Retrieve Relevant Memories

v

Retrieve Active Quest

v

Retrieve Location History

v

Build Context

v

Send To AI

---

# RETRIEVAL PRIORITY

Priority 1

Current Conversation

---

Priority 2

NPC Memories

---

Priority 3

Player Relationship

---

Priority 4

Active Quest

---

Priority 5

Location Events

---

Priority 6

Faction History

---

Priority 7

World History

---

# MEMORY SCORING

score = (relevance_score * 0.4)
      + (importance * 0.3)
      + (recency_bonus * 0.2)
      + (relationship_weight * 0.1)

This formula must match `ARCHITECTURE.md`. Relevance comes from vector similarity, importance comes from the canonical memory row, recency is calculated from world time, and relationship weight is read from deterministic relationship values.

---

# RECENCY DECAY

Recent memories gain bonus.

Old memories lose bonus.

Important memories never disappear.

Recency bonus decays by 10% per in-game week. Memories with importance >= 8 never decay and must remain retrievable through direct entity links even when they no longer rank highly by semantic similarity.

Example

Defeated Rat

v

Eventually ignored.

Example

Killed Dragon King

v

Never ignored.

---

# MEMORY SUMMARIZATION

Long histories become summaries.

Example

500 conversations

v

Summary

"Aji regularly helps merchants and is respected by traders."

This saves tokens.

---

# NPC MEMORY MODEL

Each NPC remembers:

Personal Events

Player Interactions

Faction Events

Local History

Rumors

Knowledge

Not all NPCs know everything.

---

# KNOWLEDGE LIMITATION

Village Farmer

Should not know:

Ancient Dragon Politics

World Secrets

Distant Kingdom Affairs

Unless informed.

Knowledge is restricted.

---

# KNOWLEDGE SPREAD SYSTEM

Event Occurs

v

Rumor Created

v

Rumor Travels

v

NPC Learns

World information spreads naturally.

---

# WORLD CHRONICLE

Major events enter Chronicle.

Examples:

King Died

World Item Found

Ancient Dragon Defeated

Kingdom Conquered

Chronicle acts as permanent history.

---

# DIALOGUE CONTEXT ASSEMBLER

Before AI call:

Build Context Package

Includes:

NPC Profile

Relationship Values

Recent Dialogue

Relevant Memories

Location State

Quest State

World State

Then send to AI.

## v0.8 Implemented Context Path

Narrative requests retrieve up to 20 player-scoped memories through Qdrant,
revalidate every identifier against PostgreSQL, and merge relevant canonical
memories that are still pending indexing. Context also includes current
location, NPC profile and knowledge, faction standing, numeric relationship
values, quest state/objective, and recent validated dialogue. The package is
bounded, canonically hashed, and never contains writable gameplay state.

---

# CONTEXT SIZE LIMITS

Target

2,000-6,000 tokens

Never send:

Entire save file

Entire world history

Entire conversation history

Only relevant context.

Context packages must exclude secrets, authentication tokens, raw provider credentials, and unrelated player data. RAG is allowed to retrieve narrative context, not private operational state.

---

# MEMORY CACHE

Frequently used memories cached.

Redis

TTL configurable.

Reduces retrieval latency.

Cache keys are player-scoped and include a per-player generation. Memory
creation or deletion advances that generation. Redis failure degrades to a
cache miss and never changes canonical memory state.

---

# MEMORY DEDUPLICATION

Prevent duplicates.

Example

Killed Goblin King

must not appear 500 times.

Duplicate memories merged.

Active duplicates are identified by player, memory type, entity type, entity
identity, and normalized content hash. Concurrent creation is serialized and
enforced by a PostgreSQL partial unique index.

---

# AI PROVIDER SWITCHING

RAG output must be provider agnostic.

Same memory package works for:

Gemini

OpenAI

Anthropic

Groq

OpenRouter

Ollama

Switching providers should not change world consistency.

---

# FALLBACK MODE

If all AI providers fail:

Use Prebuilt Narrative Templates.

NPCs remain functional.

Game remains playable.

Fallback responses must be clearly generated from approved local templates and must not invent gameplay state.

---

# COST CONTROL

Maximum memories retrieved:

20

Maximum dialogue history:

10 exchanges

Maximum context size:

6,000 tokens

Anything larger gets summarized.

---

# FUTURE IMPROVEMENTS

Hierarchical Memory Trees

Temporal Memory Graphs

Faction Knowledge Networks

Agentic NPC Planning

Autonomous World Historians

Dynamic Rumor Systems

Future AI-assisted planning or historian features remain narrative proposals only. Deterministic engines must validate and own every schedule, action, relationship change, event, and world-state mutation.

---

# FINAL PRINCIPLE

The AI is not the memory.

The database is the memory.

The AI simply reads the memories that matter most at the moment.
