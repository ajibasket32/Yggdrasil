# v1.3 Visual World Audit

Status: PASS
Audit date: 2026-06-20
Branch: `feat/v1.3-map-audio-overhaul`

## Root Cause

The old world presentation used one repeated tileset image as a universal
Phaser background, hard-coded the player spawn at the center of an 800x800
world, and placed NPC/encounter/travel markers at generic coordinates. Location
changes mostly swapped React/backend state while the visible map stayed the
same. That is why Valeris City, Valeris Outskirts, and forest routes read like
the same room repeated, with indoor-looking props and black/empty regions
showing through.

## Changes Verified

| Area | Result | Evidence |
|---|---|---|
| Title | PASS | `screenshots/01-title.png` |
| Valeris Outskirts | PASS | `screenshots/02-valeris-outskirts-start.png`, `screenshots/05-valeris-outskirts.png` |
| Valeris City | PASS | `screenshots/03-valeris-city.png` |
| Shop zone | PASS | `screenshots/04-shop-zone.png` |
| Greenwood Verge / inn zone | PASS | `screenshots/06-greenwood-verge-inn.png`, `screenshots/07-inn-zone.png` |
| Sylvan Branch | PASS | `screenshots/08-sylvan-branch.png` |
| Battle | PASS | `screenshots/09-battle.png` |

## BGM Verification

`frontend/e2e/real-phaser-playability.spec.ts` toggles audio off/on after a user
gesture, then asserts the browser-side BGM audit state reports `status:
playing`. The same test verifies:

- `valeris_outskirts` after New Game and outskirts travel
- `valeris_city` in Valeris City
- `sylvan_branch` in Sylvan Branch
- `battle_theme` during combat
- return to `sylvan_branch` after victory

The tracks are local WAV files under `frontend/src/assets/audio/` and are
catalogued in `assets/CATALOG.md`.

## Known Limitations

- Maps are authored Phaser shape layers, not full Tiled JSON maps yet.
- BGM files are compact self-authored placeholder loops, not final composed music.
- Shop and inn remain interaction zones tied to existing NPC/menu flows, not
  separate walkable interior scenes.
- Combat background selection is represented by current battle presentation and
  BGM; biome-specific battle backdrops can be expanded later.

## Decision

The first corridor now reads as a coherent 2D JRPG slice rather than one
repeated marker room. City, outskirts, Greenwood/inn route, Sylvan forest, shop,
and battle have distinct visual identities, local BGM keys, and E2E evidence.

