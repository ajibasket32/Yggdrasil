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
- `screenshots/final/audit-state.json`
- `screenshots/final/console-errors.txt`

Console errors: `NONE`.

## Results

| Area | Result | Evidence |
|---|---|---|
| Map identity | PARTIAL | Valeris City, Valeris Outskirts, Greenwood/forest, Blacksmith Interior, and Inn Interior now have authored profiles, but the automated visual capture did not prove the full Sylvan Branch route. |
| Visual coherence | PASS | Final screenshots show layered roads, buildings, landmarks, terrain blocks, and compact HUD over a full-screen map. |
| Player visibility | PASS | `audit-state.json` records visible player coordinates after City, travel, and combat states. |
| Transition quality | PARTIAL | City start, Outskirts, Greenwood, blacksmith focus, inn focus, and combat route were captured. Full Sylvan Branch traversal still needs stronger proof. |
| NPC context behavior | PASS | Focused regression test proves active NPC service separation for Hagar and Elena. |
| UI balance | PASS | HUD and action controls are more compact, with modal menus remaining overlays. |
| BGM behavior | PARTIAL | Local BGM keys are selected and visible in HUD/audit state. Manual browser run did not audibly validate every track transition. |
| Combat atmosphere | PASS | Combat screenshot and audit state show battle mode returning canonical combat data with no browser console errors. |

## Verification Commands

- `npm.cmd run typecheck`
- `npm.cmd exec -- vitest run src/scenes/WorldScene.test.ts src/test/ShopInnFlow.test.tsx`
- Inline content-pipeline self-check using bundled Python because local pytest/Poetry were unavailable.
- Browser screenshot capture at 1366x768 against `http://localhost:5173?audit=1`.

## Verdict

PARTIAL - strong improvement but remaining visual gaps.

Remaining gaps before this feels like a full JRPG:

- Capture the complete Valeris City -> Outskirts -> Greenwood Verge -> Sylvan Branch route.
- Add audible/manual BGM verification notes for every track transition.
- Run the full frontend/backend/Docker validation suite before PR handoff.
