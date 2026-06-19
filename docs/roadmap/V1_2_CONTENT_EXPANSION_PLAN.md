# v1.2.0 Content Expansion Plan

Theme: **Content Expansion and JRPG Systems Depth**

## Goal
Expand the world of Yggdrasil with meaningful new locations, NPCs, and quests while deepening the JRPG mechanics with deterministic shop and rest systems.

## New Systems
1. **Shop System**:
   - Merchant Silas added to Valeris.
   - Deterministic item listing and purchasing.
   - Gold deduction and inventory addition.
2. **Inn System**:
   - Innkeeper Elena added to Greenwood.
   - Rest mechanic to restore HP/MP for a gold fee.
3. **Save/Load UX**:
   - Improved messaging for continue/recovery.

## New Content
1. **Playable Region Expansion**:
   - Sylvan Deep (Requires Sylvan Reconnaissance completion).
2. **NPCs**:
   - Merchant Silas (Valeris).
   - Innkeeper Elena (Greenwood).
   - Elder Torin (Sylvan Deep).
3. **Quests**:
   - "The Blacksmith's Request": Gather ore for Hagar.
   - "Scouting the Border": Explore the edge of Sylvan Deep for Kael.
   - "Deepwood Distress": Help Elder Torin with a monster problem.
4. **Monsters**:
   - Forest Stalker (Level 5).
   - Corrupted Ent (Level 6 Boss).

## Validation Targets
- Merchant buying flow integration tests.
- Inn rest recovery unit tests.
- Quest progression for the new chain.
- Save/load compatibility with the new shop/inn states.

## Ready-to-use Hardening Addendum
- Beginner Windows startup scripts are available as `start-game.ps1`,
  `verify-ready.ps1`, and `stop-game.ps1`.
- Generated content has a one-command offline pipeline and a dry-run import
  boundary.
- Generated content does not enter gameplay automatically and cannot bypass
  validation, asset resolution, and simulation reports.
