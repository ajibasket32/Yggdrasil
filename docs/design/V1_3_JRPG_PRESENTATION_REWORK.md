# v1.3 JRPG Presentation Rework

Status: In progress
Date: 2026-06-21

## Baseline Audit

Screenshots were captured at 1366x768 before implementation:

- `docs/release/v1.3-jrpg-presentation-rework/screenshots/baseline/01-title.png`
- `docs/release/v1.3-jrpg-presentation-rework/screenshots/baseline/02-city.png`
- `docs/release/v1.3-jrpg-presentation-rework/screenshots/baseline/03-npc-interaction.png`
- `docs/release/v1.3-jrpg-presentation-rework/screenshots/baseline/06-travel-menu.png`
- `docs/release/v1.3-jrpg-presentation-rework/screenshots/baseline/07-outskirts-or-route.png`
- `docs/release/v1.3-jrpg-presentation-rework/screenshots/baseline/08-encounters.png`
- `docs/release/v1.3-jrpg-presentation-rework/screenshots/baseline/09-combat.png`

Current strengths worth keeping:

- Full-screen Phaser presentation already exists.
- Player movement, animation, combat return, shop, inn, save, and Continue flows already work.
- Approved local character, UI, monster, and tileset assets are already cataloged.
- Backend owns travel, combat, shop, inn, quest, and save outcomes.

Current visual issues:

- World maps read as repeated texture fields rather than authored places.
- NPC, travel, and encounter markers are evenly spaced instead of placed in-world.
- Valeris landmarks are not visually distinct enough.
- Shop and inn interactions are reachable from a broad global panel rather than a focused nearby NPC.
- Area music is not connected to map identity.
- UI panels are useful, but they compete with the map more than they should.

## Art Direction

Use the approved local pixel assets as a kit and compose original maps with Phaser primitives and tiled textures. The target is readable, warm, classic 2D JRPG staging: clear roads, entrances, landmarks, terrain changes, and compact UI over a world-first canvas.

## Map Transition Graph

Title Screen -> Valeris City -> Blacksmith Interior -> Valeris City -> Inn Interior -> Valeris City -> Valeris Outskirts -> Greenwood Verge -> Sylvan Branch -> Combat -> Current Area -> Save -> Continue

Canonical backend locations remain authoritative. Blacksmith and Inn interiors are frontend presentation focus states attached to active NPC interactions; they do not create canonical travel state.

## Tileset and Style Rules

- Ground, decoration, obstacle, and foreground layers must be visually separated.
- Buildings need doors, signs, and entry-facing paths.
- Every map needs a landmark visible without opening a menu.
- Use no runtime asset downloads.
- Audio keys must map to local files and fall back silently if unavailable.
- UI overlays should be compact and dismissible.

## Location Identities

Valeris City:

- Warm hub with plaza, stone roads, blacksmith landmark, inn landmark, gate, market edges, and NPC gathering points.

Blacksmith Interior:

- Forge, counter, workbench, shelves, tools, and warm lighting. Hagar is the center.

Inn Interior:

- Beds, tables, reception counter, and hearth. Rest is visually tied to Elena and the room.

Valeris Outskirts:

- City gate gives way to fences, dirt road, grass, rocks, and route signage toward the forest.

Greenwood Verge:

- Transitional woodland road with clear pathing and rising foliage density.

Sylvan Branch:

- Enclosed forest with roots, stones, darker foliage, and dangerous encounter staging.

Forest Battle Backdrop:

- Dense green battlefield with tree silhouettes, ground strip, and readable combatants.

## Interaction Rules

- Show only one nearest prompt.
- `E Talk: Name`, `E Fight: Name`, and `E Travel: Place` are the only map prompts.
- Opening an NPC interaction focuses that NPC only.
- Hagar cannot show inn services.
- Elena cannot show shop services.
- Closing interaction returns control to exploration.
- Travel, combat, save/load, and moving away clear presentation-only interaction focus.

## Audio Plan

Local generated WAV loops provide lightweight BGM keys:

- `title`
- `city`
- `interior`
- `outskirts`
- `forest`
- `battle`

Playback starts only after a user click or key press. Mute and volume persist in local storage. Failed audio loads leave gameplay unchanged.

## Screenshot Acceptance Checklist

- Title screen is readable and atmosphere-forward.
- Valeris City has roads, landmarks, gate, and no accidental black voids.
- Blacksmith and Inn interiors are visually distinct from outdoor maps.
- Outskirts and Sylvan Branch read as different biomes.
- Player is visible after travel, interaction, combat return, save, and Continue.
- NPC panels are scoped to the active NPC.
- Shop and inn services do not appear on the wrong NPC.
- Combat backdrop matches the current forest route.
- BGM key changes with title, map, interior, battle, and return.
