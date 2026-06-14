# COMBAT_DESIGN.md

# YGGDRASIL CHRONICLES

Combat System Design Document

Version: 2.0 -- Enterprise Edition
Status: Normative
Last reviewed: 2026-06-13

---

# COMBAT PHILOSOPHY

Combat must be:

* Easy to understand
* Difficult to master
* Deterministic
* Tactical
* Expandable

Combat must never depend on AI.

Combat must always produce the same result when given the same inputs.

Combat determinism is release-blocking. Any combat formula, status effect, initiative rule, reward table, or seeded RNG change must include regression tests that prove identical inputs produce identical outputs.

---

# DESIGN GOALS

The player should win because:

* Better planning
* Better equipment
* Better team composition
* Better skill usage

Not because of hidden randomness.

Randomness is allowed only through seeded engine RNG. Identical combat inputs, including the same RNG seed, must always produce identical outputs.

---

# INSPIRATIONS

Primary

* Final Fantasy X
* Persona 5
* Dragon Quest XI
* Suikoden II

Secondary

* Yggdrasil (Overlord)
* Dungeons & Dragons
* Pathfinder

---

# COMBAT TYPE

Turn Based

Party Based

Gridless

Single Screen Battle

---

# COMBAT FLOW

Encounter

v

Determine Initiative

v

Turn Order Created

v

Player Action

v

Enemy Action

v

Resolve Effects

v

Update Turn Order

v

Victory or Defeat

---

# CORE ATTRIBUTES

STR

Physical Damage

---

DEX

Accuracy

Critical Chance

---

AGI

Turn Speed

Evasion

---

VIT

Defense

HP Scaling

---

INT

Magic Damage

Magic Accuracy

---

WIS

Magic Resistance

Healing Power

---

CHA

Summons

Leadership

NPC Recruitment

---

# RESOURCES

HP

Health Points

---

MP

Magic Points

---

STAMINA

Physical Skill Resource

---

# DERIVED STATS

Physical Attack

Physical Defense

Magic Attack

Magic Defense

Accuracy

Evasion

Critical Chance

Critical Damage

Initiative

Threat

Resistance

---

# TURN ORDER

Formula

Initiative =

AGI

*

Equipment Bonus

*

Buffs

Higher initiative acts first.

Turn order recalculated every round.

---

# DAMAGE PHILOSOPHY

Damage must be predictable.

No hidden calculations.

---

# PHYSICAL DAMAGE

Base Damage

=

Attack

x

Skill Modifier

Defense Reduction

Applied Afterward

---

# MAGICAL DAMAGE

Base Damage

=

Magic Attack

x

Spell Modifier

Magic Defense Reduction

Applied Afterward

---

# CRITICAL HITS

Critical Chance

Based On

DEX

Skills

Equipment

Critical Damage

Default

150%

---

# HIT CALCULATION

Accuracy

vs

Evasion

Every attack must resolve hit chance through seeded RNG.

Certain skills never miss.

---

# COMBAT ACTIONS

Attack

Skill

Magic

Item

Guard

Escape

Wait

---

# GUARD

Reduces incoming damage.

Cannot stack.

Ends after next turn.

---

# ESCAPE

Success based on:

Party AGI

vs

Enemy AGI

Bosses may block escape.

---

# STATUS EFFECT SYSTEM

Positive

Buffs

Negative

Debuffs

Crowd Control

---

# BUFF TYPES

Attack Up

Defense Up

Magic Up

Speed Up

Critical Up

Regeneration

Barrier

---

# DEBUFF TYPES

Attack Down

Defense Down

Magic Down

Speed Down

Poison

Burn

Bleed

Weakness

Curse

---

# CROWD CONTROL

Sleep

Stun

Freeze

Paralysis

Silence

Fear

Charm

---

# RESISTANCE SYSTEM

Every entity contains:

Fire Resistance

Ice Resistance

Lightning Resistance

Holy Resistance

Dark Resistance

Poison Resistance

Mental Resistance

---

# ELEMENTAL SYSTEM

Elements

Fire

Water

Ice

Earth

Wind

Lightning

Holy

Dark

Arcane

Nature

---

# ELEMENTAL INTERACTIONS

Fire > Ice

Ice > Water

Lightning > Water

Holy > Undead

Dark > Holy Users

Nature > Earth

Arcane > Magical Barriers

---

# PARTY SYSTEM

Default

4 Active Members

Reserve Members Supported

Swap Allowed During Battle

Depending on Skills

---

# JOB SYSTEM INTEGRATION

Combat abilities come from:

Race

Job

Equipment

Skills

Buffs

Consumables

---

# RACIAL ABILITIES

Example

Elf

Mana Regeneration

---

Dwarf

Physical Resistance

---

Undead

Poison Immunity

---

Demon

Dark Resistance

---

# SKILL CATEGORIES

Physical

Magic

Support

Healing

Utility

Ultimate

Passive

---

# PASSIVE SKILLS

Always Active

Examples

Mana Efficiency

Critical Mastery

Poison Immunity

Heavy Armor Training

---

# ULTIMATE SKILLS

Powerful

Long Cooldown

Class Defining

Examples

Meteor Fall

Divine Judgment

Army Commander

Soul Harvest

---

# SUPER TIER MAGIC

Inspired by Yggdrasil

Extremely Rare

Very High MP Cost

World-Changing Effects

Limited Usage

Examples

Fallen Down

Reality Slash

Mass Resurrection

World Break

---

# SUMMON SYSTEM

Summons act independently.

Summons consume:

MP

Items

Special Resources

Summons have:

Level

Stats

Skills

Deterministic Behavior Policy

The term "AI" must not be used for authoritative enemy or summon decision-making. Combat behavior is an engine-owned policy evaluated from canonical state and seeded inputs.

---

# THREAT SYSTEM

Enemies track threat.

Threat Sources

Damage

Healing

Taunts

Special Skills

---

# BOSS DESIGN

Bosses must be mechanics-driven.

Not stat walls.

Every boss should have:

Phase System

Unique Mechanic

Weakness

Counterplay

---

# BOSS PHASES

Example

Phase 1

Physical Combat

v

Phase 2

Summons Adds

v

Phase 3

Ultimate Ability

---

# ELITE ENEMIES

Mini-Boss Tier

Unique Skills

Improved AI

Rare Loot

---

# WORLD BOSSES

Rare

Powerful

Persistent

May Affect World State

Defeating them creates:

World Event

Memory Entry

Journal Entry

---

# COMBAT REWARDS

Experience

Gold

Loot

Faction Reputation

Quest Progress

Memory Creation

All rewards are resolved by the engine from database-defined reward tables. AI may narrate the outcome after resolution, but may not determine XP, gold, loot, faction reputation, or quest progress.

Reward output must be persisted through the same transaction boundary as combat completion events. A victory without persisted rewards, journal entries, and relevant memory candidates is an invalid partial result.

---

# EXPERIENCE SYSTEM

Reward based on:

Enemy Level

Difficulty

Party Size

Modifiers

No AI involvement.

---

# LOOT SYSTEM

Loot Tables

Generated by Engine

Never Generated By AI

---

# COMBAT LOG

Every action stored.

Example

Turn 5

Aji casts Fireball.

Goblin takes 52 damage.

Goblin defeated.

Combat logs can be inspected and exported. Full deterministic reconstruction from logs is post-MVP technical debt tracked in `TECH_DEBT.md`.

---

# V0.6 IMPLEMENTED RULE PROFILE

The v0.6 foundation implements one player character against one enemy while
preserving participant identities and turn arrays for future party expansion.

Deterministic rules:

* Initiative sorts descending, then by participant UUID as a stable tie break.
* Seeded rolls are SHA-256 derived from encounter seed, action sequence, and
  purpose (`hit`, `critical`, `escape`, or `loot`).
* Hit chance is clamped to 5-95 percent:
  `75 + attacker accuracy - target evasion`.
* Physical and magical damage use integer arithmetic:
  `max(1, attack * modifier / 100 - defense)`.
* Critical damage is 150 percent.
* Guard halves incoming damage and expires at the actor's next turn start.
* Fire skills apply two-turn burn only when the target survives the hit.
* Burn, poison, and bleed deal deterministic turn-start damage. Stun, sleep,
  and freeze consume the affected turn.
* Escape chance is clamped to 10-90 percent:
  `50 + (player initiative - enemy initiative) * 3`.
* Enemy behavior is a deterministic policy: guard at low HP on even rounds,
  use the configured skill every third round when resources permit, otherwise
  attack.
* XP, gold, and seeded loot are read from monster definitions and applied by
  the engine/service transaction with no AI input.

Canonical encounter, participant, log, reward, and outbox rows persist through
process restart. Save creation and load are blocked while combat is active;
completed outcomes are captured by the normal character/inventory save
boundary.

Party combat, swapping, threat, bosses, summons, quest progress, faction
reputation, memory candidates, and narrative combat text remain excluded until
their owning releases.

---

# DIFFICULTY LEVELS

Story

Normal

Hard

Nightmare

Yggdrasil

---

# AI NARRATIVE INTEGRATION

Allowed

Combat Descriptions

Skill Flavor Text

Victory Narration

Boss Introductions

Lore

Not Allowed

Damage Calculation

Hit Chance

Loot

XP

Combat Results

---

# MULTIPLAYER COMPATIBILITY

Combat architecture must support:

Future Co-op

Future Guild Battles

Future Raid Bosses

Without redesign.

---

# BALANCE PRINCIPLE

No build should dominate all content.

Every build should have:

Strengths

Weaknesses

Counters

Tradeoffs

---

# FINAL RULE

Combat is a game system.

Not a storytelling system.

If there is ever a conflict between:

Narrative

and

Gameplay

Gameplay wins.
