# v1.4 JRPG Experience Overhaul Baseline Audit

Date: 2026-06-21
Branch: `feat/v1.4-jrpg-experience-overhaul`
Viewport: 1366x768, browser zoom 100%, Docker stack via `http://localhost:8080/?audit=1`

## Evidence

Screenshots are in `docs/release/v1.4-jrpg-experience-overhaul/screenshots/baseline/`.

| File | State |
|---|---|
| `01-title.png` | Title screen |
| `02-city.png` | Valeris City |
| `03-global-npc-panel.png` | Global quest/NPC panel |
| `04-shop.png` | Current shop |
| `05-outskirts.png` | Valeris Outskirts |
| `06-greenwood-verge.png` | Greenwood Verge |
| `07-innkeeper-panel.png` | Innkeeper panel |
| `08-inn-rest.png` | Inn rest |
| `09-inn-interior.png` | Inn Interior |
| `10-sylvan-branch.png` | Sylvan Branch |
| `11-combat.png` | Combat |
| `12-save.png` | Save feedback |
| `13-continue.png` | Continue screen |
| `baseline-state.json` | Audit state and console/page errors |

## Findings

1. Map composition and visual identity: Current maps are colored geometric blocks with pale overlays. Valeris City has labels and rectangular building shapes, but it still reads as a diagram rather than an authored town. Forest maps are greener, but the route language is still mostly rectangles.

2. Empty/black/unused camera areas: No giant black void appeared in the captured journey, but the active space often feels sparse. The camera shows large low-detail bands and weak landmarks, especially in Valeris City and forest routes.

3. Player movement speed: Keyboard movement felt sluggish. `baseline-state.json` shows the player moved only about 10 px after 600 ms of ArrowLeft input, so responsiveness needs tuning and verification.

4. Player sprite disappearance or flicker: No full disappearance was reproduced in this capture. Risk remains in transitions because `WorldScene` recreates backgrounds and resets player position on registry changes while UI state can also switch presentation maps.

5. NPC interaction behavior: The `Quests` button opens broad quest, NPC, faction, dungeon, and chronicle content. This exposes unrelated context instead of the nearest NPC. The current shop belongs to Merchant Silas, while the v1.4 target requires Hagar's blacksmith service. Innkeeper Elena can be reached through the global panel even though she is physically a Greenwood NPC.

6. HUD/menu obstruction: The HUD and action bar occupy large permanent areas. Modal panels darken and cover most of the map. The world is visible but secondary.

7. BGM/audio quality: Local audio files play and map keys change, but tracks are short placeholder WAV loops. This is technical playback, not polished JRPG atmosphere.

8. Combat presentation: Combat is readable and functional. The battle background is still generic and does not clearly inherit Sylvan Branch's forest identity.

9. What works and should be preserved: Docker startup, save/Continue, combat loop, local audio plumbing, Phaser audit hooks, keyboard input, deterministic backend systems, and basic map transition data are already useful and should be extended rather than replaced.

## Root Causes

- `WorldScene.ts` draws maps procedurally with rectangles and labels instead of reusable authored layers.
- `PLAYER_SPEED` is hardcoded in `WorldScene.ts`, and movement lacks a central tuning file.
- The React action bar exposes global Travel/Encounters/Quests at all times.
- `WorldPanel` mixes quests, all nearby NPCs, factions, dungeons, journal, shop, and inn service in one overlay.
- Shop seed ownership is Silas-centered, while the target journey expects Hagar to own the blacksmith shop.
- Audio assets are local and cataloged, but the current loops are generated placeholders.
