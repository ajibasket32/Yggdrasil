# Automatic Content Generation Pipeline Design

## 1. Goals
The goal of this pipeline is to enable the generation of new content packs (NPCs, quests, items, etc.) after launch while maintaining the core "Engine First, AI Second" philosophy.

- **Deterministic**: Content generation should be reproducible from a seed.
- **AI-Light**: AI is used as an orchestrator or repair assistant, not as the primary source of gameplay truth.
- **Validated**: All generated content must pass strict schema and referential integrity checks.
- **Offline-First**: The system must work without cloud API keys using deterministic fallback templates.
- **Safe Assets**: Assets are resolved from allowlisted sources or local packs with clear license metadata.

## 2. Content Types
The pipeline supports the following schemas:
- **NPC**: Identity, role, personality archetype, and home location.
- **Quest**: Title, description, giver, requirements, and ordered objectives.
- **Quest Objective**: Type (Fetch, Scout, Defeat, NPC_Help), target, and count.
- **Location**: Name, description, and region.
- **Monster**: Stats, archetypes, and loot tables.
- **Item**: Stats, type, rarity, and price.
- **Shop Inventory**: Items available at specific NPCs.
- **Inn**: Locations where resting is available.
- **Dialogue Seed**: Templates for AI or fallback dialogue.
- **Asset Requirement**: Sprite/Icon needs with license tracking.

## 3. Content Pack Format
Content is organized into "packs" located in `content/packs/<pack_id>/`.

### `pack.json`
Contains all gameplay definitions.
```json
{
  "pack_id": "sylvan_supply_001",
  "version": "1.0.0",
  "generated_by": "seeded_generator",
  "seed": 42,
  "theme": "sylvan",
  "npcs": [...],
  "locations": [...],
  "quests": [...],
  "enemies": [...],
  "items": [...],
  "shops": [...],
  "inns": [...],
  "validation_status": "pending"
}
```

### `assets.json`
Contains asset requirements and resolution status.
```json
{
  "pack_id": "sylvan_supply_001",
  "assets": [
    {
      "asset_id": "sprite_sylvan_scout",
      "type": "sprite",
      "preferred_fallback": "assets/sprites/placeholder_npc.png",
      "remote_url": "https://opengameart.org/.../scout.png",
      "license": "CC0",
      "status": "local"
    }
  ]
}
```

## 4. AI-Light Orchestration Model
AI is strictly optional and performs only the following roles:
1. **Thematic Suggestions**: Suggesting content themes from compact templates.
2. **Content Repair**: Fixing validation errors in a `pack.json` using only the error diff.
3. **Asset Candidate Suggestion**: Recommending assets from allowlisted sources based on content descriptions.
4. **Dialogue QA**: Reviewing generated dialogue for tone and consistency.

**AI Constraints:**
- Never writes directly to the database.
- Never decides rewards, combat stats, or gold.
- Operates on compact JSON schemas.
- Fails gracefully to deterministic templates if unavailable.

## 5. Token-Saving Policy
- Use deterministic templates for the bulk of the content.
- Cache AI outputs by input hash.
- Send only minimal context (schema name, validation errors, specific objects) to the AI.

## 6. Validation Gates
Every pack must pass:
- **Schema Validation**: JSON schema compliance.
- **Referential Integrity**: All IDs (NPCs, items, etc.) referenced in quests/shops must exist within the pack or the base game.
- **Logic Validation**: Quest objectives must be supported by the engine.
- **Asset Validation**: All required assets must have valid license metadata and a local fallback.
- **Deterministic Simulation**: A smoke test to ensure the content doesn't break save/load or core loops.

## 7. Asset Pipeline
- **Resolver**: Matches requirements to local assets or allowlisted URLs.
- **License Guard**: Rejects assets without clear "CC0", "Public Domain", or "Kenney" licenses.
- **Runtime**: Only uses already-approved local assets. Runtime downloads are for dev/build steps only.

## 8. Workflow
1. **Generate**: `generate_content_pack.py --seed <N> --theme <T>` creates a draft.
2. **Validate**: `validate_content_pack.py` checks for errors.
3. **Repair (Optional AI)**: `content_ai_orchestrator.py --repair` fixes errors if enabled.
4. **Resolve Assets**: `resolve_asset_manifest.py` ensures all sprites/icons are available.
5. **Finalize**: The pack is marked as `validated` and can be loaded by the game.
