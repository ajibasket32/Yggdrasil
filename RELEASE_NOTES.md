# Release Notes - v1.2.0-rc.1

Version: 1.2.0-rc.1
Status: RC (Release Candidate)
Last reviewed: 2026-06-20

## Release Summary
Yggdrasil Chronicles v1.2.0, "Content Expansion," introduces core JRPG systems including a deterministic Shop system and Inn/Rest mechanic. The world continues to grow with expanded quest chains for Hagar and Kael, and deeper integration between world actions and character progression.

## Key Features
- **Shop System**: Merchant Silas is now open for business in Valeris. Players can purchase restorative items and improved equipment using gold.
- **Inn System**: Innkeeper Elena provides rest services in Greenwood, allowing characters to fully restore HP and MP for a fee.
- **Quest Expansion**: "The Blacksmith's Request" and "Scouting the Border" now feature multi-step objectives that require interacting with shops and exploring the forest.
- **UI/UX Refinements**:
    - Full-featured Shop Overlay with price tracking and purchase confirmation.
    - Gold-aware action buttons in the World Panel.
    - Status-based rest buttons that indicate affordability.
- **System Integration**: Shop purchases and location discovery now automatically trigger relevant quest progression.
- **Ready-to-use Startup**: Windows users can run `.\start-game.ps1`, verify with
  `.\verify-ready.ps1`, and stop with `.\stop-game.ps1`.
- **Safe Content Pipeline**: Developers can generate, validate, simulate, and
  dry-run content import offline without cloud AI keys.

## Validation Evidence
- **Backend Tests**: PASS (124/124)
- **Frontend Tests**: PASS (80/80)
- **Frontend Coverage**: 82.03% Branch Coverage.
- **Security Audit**: Zero vulnerabilities (Verified via `pip-audit` and `npm audit`)
- **Docker Build/Startup**: PASS (`docker compose build`, `up -d`, health checks).
- **Critical Journey Validation**: PASS via Playwright ready-to-use smoke path.
- **Content Import Dry-run**: PASS via `tools/content/import_content_pack.py`.
- **RAG Recovery Stability**: PASS, 10/10 repeated focused runs after service restart.
- **GitHub CI / Strict Validation**: PASS on `main` commit `66e39c20294e53063d8f5c7be2a3ff3ebfc2b3fd`.

---

# Release Notes - v1.1.0

Version: 1.1.0
Status: GA (General Availability)
Last reviewed: 2026-06-18

## Release Summary
Yggdrasil Chronicles v1.1.0 focuses on "JRPG Polish," transforming the technical MVP into a more immersive and user-friendly experience. Key improvements include a redesigned title screen, enhanced HUD, player animations, and expanded world content.

## Key Features
- **Redesigned Title Screen**: Clear "New Game" and "Continue" options with automatic character detection.
- **Authentic JRPG HUD**: Integration of Kenney RPG UI assets for a polished look.
- **Exploration Polish**: Added player walk animations and clearer interaction hints in the world map.
- **Improved Quest Journal**: Status-based quest cards with objective checklists and reward previews.
- **Combat Visuals**: Animated damage/healing popups and status effect icons.
- **New Content**:
    - NPCs: Blacksmith Hagar (Valeris), Scout Kael (Greenwood).
    - Quests: "The Master's Iron", "Sylvan Reconnaissance", "A Scout's Tool" (Repeatable).
    - Location: Sylvan Branch route expansion.
    - Monsters: Giant Wasp, Ancient Sentry.
    - Items: High-Grade Iron Ore, Sharpening Stone, Scout's Map.

## Validation Evidence
- **Backend Tests**: PASS (56/56)
- **Frontend Tests**: PASS (59/59)
- **Frontend Coverage**: 80.21% Branch Coverage.
- **Security Audit**: Zero high/critical vulnerabilities (Verified via `pip-audit` and `npm audit`)
- **Visual Verification**: PASS (Screenshots captured)
- **Critical Journey Validation**: PASS via fallback script.
- **Strict Release Validation**: PASS (GitHub Actions)

---

# Release Notes - v1.0.0

Version: 1.0.0
Status: GA (General Availability)
Last reviewed: 2026-06-18

## Release Summary
Yggdrasil Chronicles v1.0.0 is the official MVP Release. This milestone delivers a fully playable 2D JRPG vertical slice with exploration, combat, questing, and persistent state.

## Validation Evidence
- **GitHub Actions CI**: PASS
- **Strict Release Validation**: PASS (Workflow Run ID: [27742245824](https://github.com/ajibasket32/yggdrasil-chronicles/actions/runs/27742245824))
- **Release Readiness Report**: PASS (Verified in `docs/RELEASE_READINESS_REPORT.md`)
- **Security Audit**: Zero high/critical vulnerabilities (Verified via `pip-audit` and `npm audit`)

## Key Features
- **Exploration**: 2D Tile-based world with WASD/Arrow movement and interactive markers.
- **Combat**: Turn-based deterministic combat engine with Kenney assets and monster sprites.
- **Quest System**: Persistent quests, NPC interactions, and faction relationships.
- **Save System**: Transactional Save/Load preserving character, world, and narrative state.
- **AI Narrative**: Integrated AI narration and dialogue with local fallback (Ollama/Cached).
- **Asset Catalog**: 100% locally hosted assets from Kenney and OpenGameArt with full provenance.

## Windows Quickstart
1. Ensure **Docker Desktop** is installed and running.
2. Run `.\start-yggdrasil.ps1` (PowerShell) or `.\start-yggdrasil.cmd` (Command Prompt).
3. Open your browser to **http://localhost:8080**.
4. See `WINDOWS_QUICKSTART.md` for detailed instructions.

## Known Limitations
- **Narrative**: Generation is bounded to specific NPC topics and location atmosphere.
- **Idempotency**: Dialogue replays preserve text but not speaker/memory metadata.
- **Authentication**: `X-Player-ID` is used for development identity; production auth is not implemented.
- **Multiplayer**: This is a single-player MVP; no multiplayer features are included.

## AI Fallback Behavior
The game is "Engine First, AI Second." If AI providers are unavailable, the system automatically degrades to:
1. **Ollama**: Local LLM generation (if configured).
2. **Cached Narrative**: Pre-approved, generic narrative templates.
3. **Menu-Driven Dialogue**: Deterministic interactions remain fully functional.
**No cloud API keys are required for basic gameplay.**

## Access URL
- **Gameplay**: http://localhost:8080
- **Backend Health**: http://localhost:8000/health

## Next Recommended Phase
Maintenance and Content Expansion.
