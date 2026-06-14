# JOB_SYSTEM.md

# YGGDRASIL CHRONICLES

Job, Race, Class & Character Progression System

Version: 2.0 -- Enterprise Edition
Status: Normative
Last reviewed: 2026-06-14

---

# PURPOSE

This document defines:

* Character Progression
* Job Progression
* Race Progression
* Hidden Classes
* World Classes
* Skill Acquisition
* Character Identity

All gameplay systems must follow this document.

---

# CORE PHILOSOPHY

A character is defined by:

Race

*

Jobs

*

Skills

*

Equipment

*

Achievements

*

Player Decisions

Not by level alone.

---

# YGGDRASIL LEVEL SYSTEM

Maximum Character Level:

100

Every level must belong to:

Race Levels

or

Job Levels

---

Formula:

Race Levels + Job Levels = Total Character Level

The total must never exceed the character level cap of 100.

Progression must be deterministic. Given the same character state, experience events, prerequisites, and configured job definitions, the engine must always produce the same level, unlock, and stat results.

---

Examples

Human Warrior

Race Levels: 0

Job Levels: 100

Total: 100

---

Undead Overlord

Race Levels: 40

Job Levels: 60

Total: 100

---

Dragon Emperor

Race Levels: 60

Job Levels: 40

Total: 100

---

# LEVEL CAP

Character Level Cap:

100

No exceptions.

Additional power progression occurs through:

Equipment

World Items

Achievements

Titles

Rare Skills

Reputation

---

# CHARACTER PROGRESSION

Progression Sources

Experience

v

Level Up

v

Stat Growth

v

Skill Unlocks

v

Job Unlocks

v

Advanced Content

For v0.5, character XP required for the next level is:

`100 * current_level^2`

Active-job XP required for the next job level is:

`75 * current_job_level^2`

Each character level grants one skill point and applies the active job's
versioned stat modifiers. Skills unlock from canonical job-level gates. Job
prerequisites are data-driven expressions supporting nested `all` and `any`
branches over character level, karma, race, and existing job levels.

---

# JOB TIERS

Jobs are divided into four tiers.

Basic

High

Rare

World

---

# BASIC JOBS

Entry-level classes.

Easy to obtain.

Level Cap:

15

Examples:

Warrior

Knight Apprentice

Mage

Cleric

Rogue

Archer

Monk

Druid

Bard

Merchant

Blacksmith

Alchemist

Summoner

Priest

---

# HIGH JOBS

Require prerequisites.

Level Cap:

10

Examples:

Sword Master

Paladin

Elementalist

Necromancer

Assassin

Sniper

Battle Monk

High Priest

Rune Smith

Spirit Caller

Beast Tamer

Templar

Warlock

---

# RARE JOBS

Difficult to unlock.

Often hidden.

Level Cap:

5

Examples:

Archmage

Soul Reaper

Chronomancer

Dragon Slayer

Grand Summoner

Death Knight

Void Walker

Demon Hunter

Rune Lord

Ancient Druid

World Scholar

---

# WORLD CLASSES

Extremely rare.

Usually unique.

Level Cap:

1

Examples:

World Champion

World Savior

World Disaster

World Architect

World Conqueror

World Breaker

World Emperor

World Guardian

---

# RACE SYSTEM

Some races possess race levels.

Humans do not.

Heteromorphic races often do.

---

# RACE CATEGORIES

Humanoid

Demi-Human

Heteromorphic

---

# HUMANOID RACES

Humans

Elves

Dwarves

Half-Elves

Half-Dwarves

Usually:

0 Race Levels

---

# DEMI-HUMAN RACES

Orcs

Goblins

Lizardmen

Minotaurs

Gnolls

Can possess:

5-20 Race Levels

---

# HETEROMORPHIC RACES

Undead

Demons

Angels

Dragons

Insectoids

Elementals

Can possess:

20-60 Race Levels

---

# RACIAL EVOLUTION

Certain races evolve.

Example

Skeleton

v

Elder Skeleton

v

Skeleton Warrior

v

Death Knight

v

Lich

v

Elder Lich

v

Overlord

---

Another Example

Young Dragon

v

Adult Dragon

v

Ancient Dragon

v

Dragon Lord

v

World Dragon

---

# RACIAL REQUIREMENTS

Race Evolutions may require:

Level

Items

Achievements

Boss Kills

Quests

Special Locations

World Events

---

# JOB STRUCTURE

Each Job contains:

Name

Tier

Description

Lore

Requirements

Stat Growth

Skill Unlocks

Passive Skills

Hidden Bonuses

Evolution Paths

---

# STAT GROWTH

Every job grants growth.

Example

Warrior

STR +3

VIT +2

AGI +1

---

Mage

INT +4

WIS +2

MP +5

---

Rogue

DEX +3

AGI +3

---

# JOB EXPERIENCE

Every job gains experience independently.

Example

Casting spells

v

Mage Experience

---

Using swords

v

Warrior Experience

---

Healing allies

v

Cleric Experience

---

# MULTI-CLASS SYSTEM

Characters may possess multiple jobs.

Example

Warrior 15

Knight 10

Paladin 10

Dragon Slayer 5

World Champion 1

Total Job Levels

41

---

# ACTIVE CLASS

One class is designated as Primary Class.

Primary Class determines:

Character Title

Profile Display

NPC Recognition

Visual Identity

Class Reputation

---

# CLASS SYNERGY

Certain combinations unlock bonuses.

Examples

Warrior

*

Knight

v

Veteran Soldier

---

Knight

*

Cleric

v

Paladin

---

Mage

*

Necromancer

v

Dark Scholar

---

Summoner

*

Druid

v

Nature Shepherd

---

# HIDDEN CLASSES

Hidden Classes are never shown.

Players discover them naturally.

Examples

Void Walker

Soul Weaver

Dream Sage

Dragon Apostle

Rune Emperor

Eclipse Mage

Blood Monarch

Ancient Prophet

---

# DISCOVERY METHODS

Hidden Jobs may require:

Specific Quests

Specific Items

Specific NPCs

Rare Achievements

Rare Locations

Unique World Events

Secret Dialogues

Reputation Thresholds

---

# ALIGNMENT SYSTEM

Characters possess Karma.

Range:

-500

to

+500

---

# POSITIVE CLASSES

Require positive karma.

Examples

Paladin

Saint

Holy Champion

Divine Apostle

---

# NEGATIVE CLASSES

Require negative karma.

Examples

Necromancer

Soul Reaper

Demon Lord

World Disaster

---

# NEUTRAL CLASSES

Ignore karma.

Examples

Chronomancer

Rune Lord

World Architect

Merchant King

---

# REPUTATION REQUIREMENTS

Certain jobs require faction standing.

Examples

Royal Knight

Requires:

Kingdom Reputation

50+

---

Archmage

Requires:

Arcane Council Reputation

75+

---

Shadow Assassin

Requires:

Shadow Syndicate Reputation

60+

---

# SKILL ACQUISITION

Skills can be obtained through:

Job Levels

Quest Rewards

Books

NPC Teachers

Artifacts

World Events

Rare Drops

Hidden Discoveries

---

# SKILL TYPES

Active

Passive

Ultimate

World Skill

Racial Skill

Support Skill

Crafting Skill

---

# PASSIVE SKILLS

Always active.

Examples

Heavy Armor Mastery

Mana Efficiency

Critical Mastery

Poison Resistance

Rune Affinity

---

# ULTIMATE SKILLS

High cooldown.

High impact.

Examples

Meteor Fall

Army Commander

Divine Judgment

Soul Harvest

Dragon's Wrath

---

# WORLD SKILLS

Exceptionally powerful.

Very rare.

Examples

Reality Slash

World Break

Heaven's Fall

Eternal Command

Absolute Dominion

---

# WORLD CLASS REQUIREMENTS

Extremely difficult.

May require:

World Boss Defeat

World Item Ownership

Faction Leadership

Legendary Reputation

Major Historical Impact

Special Achievements

Developer-Controlled Events

---

# JOB TRAINERS

NPCs can teach jobs.

Requirements may include:

Gold

Items

Reputation

Quests

Friendship

Special Events

---

# CRAFTING CLASSES

Supported Paths

Blacksmith

v

Master Smith

v

Rune Smith

v

Artifact Creator

---

Alchemist

v

Master Alchemist

v

Philosopher

v

Grand Creator

---

# SUMMONING PATH

Summoner

v

Spirit Caller

v

Grand Summoner

v

Celestial Shepherd

v

World Shepherd

---

# MAGIC PATH

Mage

v

Elementalist

v

Archmage

v

Arcane Sage

v

World Scholar

---

# NECROMANCY PATH

Mage

v

Necromancer

v

Death Lord

v

Elder Lich

v

Overlord

---

# MARTIAL PATH

Warrior

v

Knight

v

Sword Master

v

Blademaster

v

World Champion

---

# JOB RESET POLICY

No free respec.

Character decisions matter.

Rare methods may allow:

Class Reset

Soul Rebirth

Memory Rewrite

These methods are intentionally difficult.

---

# NPC CLASS SYSTEM

NPCs use the same progression rules.

NPCs can:

Level Up

Gain Classes

Change Classes

Unlock Rare Jobs

Acquire Skills

No special privileges.

---

# AI USAGE RULES

AI may:

Generate job descriptions

Generate lore

Generate dialogue and lore for existing engine-defined class trainers

Generate class history

Generate flavor text

AI may NOT:

Create new jobs

Change balance

Modify requirements

Change progression rules

without explicit developer approval and a deterministic engine implementation.

AI-generated job lore is cosmetic. It must never create a new unlock path, stat modifier, prerequisite bypass, skill effect, or hidden bonus.

---

# FUTURE EXPANSION

The system must support:

Additional Jobs

Additional Races

Additional Evolutions

Additional World Classes

Additional Skill Trees

Without architectural redesign.

---

# FINAL RULE

A class is not merely a collection of numbers.

A class is a record of a character's journey, identity, achievements, and choices.
