# v1.3 World Map and Audio Direction

Status: Active
Last reviewed: 2026-06-20

## Purpose

v1.3 turns the playable slice from marker-driven rooms into authored 2D JRPG
places. The game engine still owns travel, combat, quests, shops, inns, saves,
and progression. Map art direction and BGM only present canonical state.

## Location Map Contract

Every map or generated location must declare:

| Field | Requirement |
|---|---|
| `map_id` | Stable map identifier. |
| `region_type` | One of `safe_hub`, `route`, `town_interior`, `shop_interior`, `inn_interior`, `quest_area`, `combat_region`, `dungeon_route`, or `forest_route`. |
| `theme` | Short readable theme such as `capital_city`, `countryside_gate`, or `deep_forest`. |
| `palette` | Named colors used by ground, path, structures, props, and lighting. |
| `tileset` | Local tileset or authored-shape set. |
| `background_layers` | Ordered ground and distance layers. |
| `foreground_layers` | Ordered canopy, roof, prop, and label layers. |
| `collision_layer` | Impassable walls, furniture, water, trees, buildings, cliffs, and fences. |
| `camera_bounds` | Exact bounds matching authored playable content. |
| `spawn_points` | Named entry points for player placement. |
| `transition_points` | Named exits connected to canonical location routes. |
| `npc_zones` | Believable placement zones for NPCs. |
| `interaction_zones` | Shop, inn, quest, save, and inspect interaction zones. |
| `landmarks` | Distinct visible features that identify the place. |
| `music_key` | Local BGM key from the audio manifest. |
| `ambient_sound_key` | Local ambience key or `none`. |
| `combat_background_key` | Local combat backdrop key for encounters started here. |
| `lighting_profile` | Day, dusk, interior_warm, forest_canopy, or dungeon_dark. |
| `layout_seed` | Required for generated maps. Use `null` for authored maps. |
| `layout_hash` | Stable hash of navigation shape and landmark placement. |
| `asset_manifest_reference` | Asset manifest IDs needed by the map. |

## Gameplay Purpose

Every future map must have one explicit purpose:

- safe hub
- route
- town interior
- shop interior
- inn interior
- quest area
- combat/exploration region
- dungeon/forest route

## Coherence Rules

- No outdoor city map may contain unrelated indoor bed or room props.
- No map may default to a large black unused void unless darkness is an intentional gameplay feature.
- Each location must have distinct landmarks, palette, navigation shape, and gameplay purpose.
- Generated maps must not reuse the same `layout_hash` as another active map.
- Generated content packs must declare a theme, map template, landmarks, music profile, and asset requirements.
- Validators must reject missing map theme, audio, landmark, layout, or asset metadata.
- Shops and inns must be assigned to coherent shop or inn zones before approval.
- Quest objectives that target a map zone must reference a declared interaction or NPC zone.

## v1.3 First Corridor

| Location | Purpose | Visual Identity | Audio |
|---|---|---|---|
| Valeris City | Safe hub | Cobblestone plaza, gate road, forge, inn, market square. | `valeris_city` |
| Valeris Outskirts | Transition route | Dirt road, grass, fences, rocks, city gate edge. | `valeris_outskirts` |
| Greenwood Verge | Forest route | Woodland threshold linking the outskirts to deeper forest. | `sylvan_branch` |
| Sylvan Branch | Forest quest area | Dense canopy, creek crossing, roots, encounter clearings. | `sylvan_branch` |
| Blacksmith zone | Shop interaction zone | Forge, counter, tools in Valeris City. | `valeris_city` |
| Inn zone | Rest interaction zone | Warm hearth, beds, tables at the forest road inn. | `sylvan_branch` |

