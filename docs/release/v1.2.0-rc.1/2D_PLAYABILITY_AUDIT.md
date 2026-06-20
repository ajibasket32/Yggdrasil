# v1.2.0-rc.1 2D Playability Audit

Status: PASS -- Genuine playable 2D JRPG loop
Audit branch: `audit/v1.2-2d-playability`
RC target audited: `3240bbb58c76537cd7651b9c11884f3a2f60b4d9`
Merged via PR #33 into `main`: `2f1aa46a5c3b06963a8fd118e27104ece0e615a2`
Date: 2026-06-20

## Ponytail Availability

BLOCKED: Ponytail unavailable for visual/browser automation.

The Ponytail plugin skill instructions were available and used for the audit posture: keep fixes minimal, prove the player-facing path, and avoid speculative redesign. No Codex-integrated Ponytail browser/UI verification command was exposed in this session after tool discovery, so browser verification used the Codex/Playwright fallback.

## Visual Evidence

Evidence directory: `docs/release/v1.2.0-rc.1/2d-playability-audit/`

Retained artifacts:

- `audit-summary-initial.json`
- `audit-summary-post-fix.json`
- `post-01-title.png`
- `post-02-character-creation.png`
- `post-04-arrow-walk.png`
- `post-05-wasd-walk.png`
- `post-07-npc-e-panel.png`
- `post-09-shop-buy.png`
- `post-10-inn.png`
- `post-11-quest-journal.png`
- `post-13-combat-start.png`
- `post-14-combat-victory.png`
- `post-16-save.png`
- `post-18-continue-loaded.png`
- `post-23-frame-world.png`
- `post-24-frame-combat.png`

## Checkpoint Results

| Checkpoint | Result | Evidence |
|---|---|---|
| Title screen | PASS | Game title and New Game visible; Continue appears after save. |
| Character creation | PASS | Name and job choices are usable; create proceeds to world. |
| 2D world render | PASS | Phaser canvas renders a tiled 2D world with visible player and markers. |
| Arrow movement | PASS | Real keyboard input changes Phaser player position. |
| WASD movement | PASS | Real keyboard input changes Phaser player position. |
| Walk animation | PASS | Movement starts `player-walk`; idle resets to the idle frame. |
| Boundaries | PASS | Arcade world bounds clamp player movement. |
| NPC interaction | PASS | Player can move to an NPC marker and press E through the Phaser proximity path. |
| Quest journal | PASS | Active quest/objective text is readable and can be closed safely. |
| Shop | PASS | Shop shows item, price, gold; buying updates state visibly. |
| Inn | PASS | Inn/rest flow shows cost/result and returns to world safely. |
| Combat | PASS | Combat scene is visually distinct; player/enemy HP, actions, log, damage, and victory are visible. |
| Victory return | PASS | Continue from victory returns to exploration. |
| Save/Continue | PASS | Save confirmation appears; reload Continue restores the saved character. |
| Cloud-AI-free play | PASS | Compose used `AI_PROVIDER_ORDER=cached`; gameplay remained usable with cloud providers absent. |

## Bugs Found

1. Phaser assets were referenced with runtime string paths, causing production Docker/CSP asset failures and missing textures.
2. The player sprite used an invisible/poor source frame and the atlas cyan key was opaque.
3. Movement changed position but did not visibly animate.
4. NPC interaction from the Phaser world only generated dialogue and did not expose the world interaction panel for shop/inn flow.
5. The bottom narrative panel duplicated UI while a modal/panel was open.
6. Production CSP blocked Google font downloads and Phaser blob-backed images.
7. Combat and world scenes reused the same `player` texture key, producing browser console errors on scene transitions.
8. Existing Playwright smoke coverage mostly clicked React UI and did not prove real Phaser keyboard movement.
9. `compose.test.yaml` did not mount `/content` or `/assets`, so the explicit full backend test command could not run content-pipeline unit tests inside the test container.

## Fixes Made

- Converted Phaser asset loading to Vite-imported local asset URLs.
- Made the player sprite visible by using a valid idle frame and transparent atlas background.
- Added deterministic walk animation on real movement and idle frame reset.
- Added a read-only `?audit=1` observability bridge exposing actual Phaser world/combat state after scene updates.
- Routed Phaser NPC interaction to the existing world panel while preserving dialogue.
- Hid the bottom narrative panel while another gameplay panel is open.
- Removed runtime Google font dependency and relaxed CSP only for existing inline styles and Phaser blob images.
- Gave combat its own player texture key and guarded repeated texture loads.
- Added real Phaser E2E coverage for keyboard movement, animation, NPC proximity interaction, combat, victory return, save, Continue, and browser console/page errors.
- Mounted `assets/` and `content/` read-only in `backend-test` so the full backend test suite can run in the test container.

## E2E Assessment

The old ready-to-use E2E was useful as a smoke test, but it did not independently prove that keyboard input reached the Phaser movement implementation or that the visible sprite moved in the canvas. The new `frontend/e2e/real-phaser-playability.spec.ts` drives real keys, reads only real scene state exposed after Phaser updates, asserts movement and animation, checks proximity interaction, verifies combat and save/continue, and fails on browser console/page errors.

## Validation Results

- `cd frontend && npm ci`: PASS, 0 vulnerabilities.
- `cd frontend && npm run format:check`: PASS.
- `cd frontend && npm run lint`: PASS.
- `cd frontend && npm run typecheck`: PASS.
- `cd frontend && npm run test`: PASS, 82 passed; branch coverage 81.44%.
- `cd frontend && npm run build`: PASS.
- `cd frontend && npx playwright test e2e/real-phaser-playability.spec.ts e2e/ready-to-use.spec.ts --reporter=line`: PASS, 2 passed.
- `cd backend && poetry check`: PASS with existing deprecated-field warnings.
- `cd backend && poetry run pip-audit`: PASS, no known vulnerabilities.
- `cd backend && poetry run black --check app ../tests`: PASS.
- `cd backend && poetry run ruff check app ../tests`: PASS.
- `cd backend && poetry run mypy app ../tests`: PASS.
- `docker compose --env-file .env.test -f compose.test.yaml ... poetry run pytest -c pyproject.toml ../tests`: PASS, 124 passed.
- `.\test-local.ps1 -Suite all`: PASS, 68 integration/regression tests passed.
- `docker compose config`: PASS.
- `docker compose build`: PASS.
- `docker compose up -d`: PASS; main containers healthy.
- `/health`: DEGRADED only for unavailable cloud AI provider checks; core runtime health passed for database, Redis, Qdrant, worker, frontend, and backend. Cached/offline narrative fallback supported gameplay because cloud AI is optional and not gameplay authority.

## Classification

PASS -- Genuine playable 2D JRPG loop.

The RC was not passable as a visual 2D JRPG before fixes because sprites/textures were broken and movement lacked visible animation. After fixes, the audited branch supports a complete visible loop: title, character creation, 2D world, real keyboard movement, animation, NPC interaction, quest UI, shop, inn, combat, victory return, save, Continue, and cloud-AI-free play.

## Remaining Limits

This is still an MVP/prototype JRPG loop, not a full-feeling JRPG. The world map is small and marker-driven, collisions are boundary-only rather than rich tile collisions, shop/inn are reached through the existing world panel after NPC proximity rather than bespoke in-world interiors, combat visuals are clear but simple, and content depth is limited. None of those block the v1.2.0-rc.1 classification as a genuine playable 2D loop.

## Tag/Release Notes

No final `v1.2.0` tag was created.
The existing `v1.2.0-rc.1` tag was not modified.

## Recommended Next Prompt

After the GA evidence PR is merged, run strict post-merge validation on the exact final `main` SHA, then create and publish final `v1.2.0` only if every gate passes.
