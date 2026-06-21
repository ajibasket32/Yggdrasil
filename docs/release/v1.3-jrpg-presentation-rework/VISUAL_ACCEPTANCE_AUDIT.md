# v1.3 JRPG Presentation Rework Visual Acceptance Audit

Date: 2026-06-21
Branch: `feat/v1.3-jrpg-presentation-rework`

## Evidence

Baseline screenshots:

- `screenshots/baseline/01-title.png`
- `screenshots/baseline/02-city.png`
- `screenshots/baseline/03-npc-interaction.png`
- `screenshots/baseline/06-travel-menu.png`
- `screenshots/baseline/07-outskirts-or-route.png`
- `screenshots/baseline/08-encounters.png`
- `screenshots/baseline/09-combat.png`

Final screenshots:

- `screenshots/final/01-title.png`
- `screenshots/final/02-valeris-city.png`
- `screenshots/final/03-blacksmith-interior.png`
- `screenshots/final/03-world-panel.png`
- `screenshots/final/04-shop.png`
- `screenshots/final/05-travel-menu.png`
- `screenshots/final/06-valeris-outskirts.png`
- `screenshots/final/07-forest-or-greenwood.png`
- `screenshots/final/08-innkeeper-or-rest.png`
- `screenshots/final/08-inn-interior.png`
- `screenshots/final/09-encounters.png`
- `screenshots/final/10-combat.png`
- `screenshots/final/11-sylvan-branch.png`
- `screenshots/final/12-save.png`
- `screenshots/final/13-continue-sylvan.png`
- `screenshots/final/audit-state.json`
- `screenshots/final/audio-state.json`
- `screenshots/final/console-errors.txt`
- `screenshots/final/route-console-errors.txt`

Console errors: `NONE`.

## Results

| Area | Result | Evidence |
|---|---|---|
| Map identity | PASS | Valeris City, Blacksmith Interior, Inn Interior, Valeris Outskirts, Greenwood Verge, and Sylvan Branch have authored profiles and screenshot evidence. |
| Visual coherence | PASS | Final screenshots show layered roads, buildings, landmarks, terrain blocks, and compact HUD over a full-screen map. |
| Player visibility | PASS | `audit-state.json` records visible player coordinates after City, travel, and combat states. |
| Transition quality | PASS | Real browser E2E covers City -> Blacksmith -> City -> Outskirts -> Greenwood -> Sylvan Branch -> combat -> world -> save -> Continue. |
| NPC context behavior | PASS | Focused regression test proves active NPC service separation for Hagar and Elena. |
| UI balance | PASS | HUD and action controls are more compact, with modal menus remaining overlays. |
| BGM behavior | PASS | `audio-state.json` records a real browser session with `ready: true`, `muted: false`, `volume: 0.35`, and `paused: false`; E2E asserts area and battle BGM keys. |
| Combat atmosphere | PASS | Combat screenshot and audit state show battle mode returning canonical combat data with no browser console errors. |

## Verification Commands

- `docker compose run --rm -e PYTHONPATH=/repo/backend -v "${repo}:/repo" -w /repo/backend backend poetry run pytest ../tests --tb=short` - 125 passed, 1 warning.
- `npm.cmd run lint` - passed.
- `npm.cmd test` - 84 passed; coverage above 80%.
- `npm.cmd run build` - passed with existing large chunk warning.
- `npm.cmd exec -- playwright test e2e/v1_3_presentation_rework.spec.ts --reporter=line` - 1 passed.
- `docker compose build` - passed for backend, worker, and frontend images.
- Browser screenshot capture at 1366x768 against `http://localhost:5173?audit=1`.

## Verdict

PASS - polished coherent JRPG vertical slice.

Remaining gaps before this feels like a full JRPG:

- This is one polished route, not full world breadth; more locations need the same authored treatment.
