# CODING_STANDARDS.md
# YGGDRASIL CHRONICLES
# Coding Standards & Engineering Guidelines
Version: 2.0 -- Enterprise Edition
Status: Normative
Last reviewed: 2026-06-13

---

## 1. PURPOSE & AUTHORITY

This document defines the engineering standards for all code in the Yggdrasil Chronicles codebase.

**These standards apply to:**
- All human-authored code
- All AI-generated code (Claude Code, Cursor, Copilot, etc.)
- All contributions via pull request

**When code conflicts with this document, this document wins.**

Code that violates these standards must be refactored before merging. Deferral is not an exception.

---

## 2. CORE ENGINEERING PRINCIPLES

### 2.1 Readability First
Code is read far more often than it is written. Optimize for the developer who reads this code six months from now -- who may be you.

- Favor explicit over implicit
- Favor clarity over cleverness
- Favor consistency over personal preference

### 2.2 Architectural Sovereignty
The architecture document is law. No "quick hacks" that bypass layer boundaries are permitted, even temporarily.

### 2.3 No Magic
- No magic numbers
- No magic strings
- No undocumented assumptions
- No hidden state

### 2.4 Fail Loudly
Never silently swallow exceptions. Every failure must be logged, classified, and either handled or propagated.

---

## 3. LAYER RESPONSIBILITY MATRIX

| Layer | May Contain | May NOT Contain |
|---|---|---|
| API Controllers | Routing, auth, validation, serialization | Business logic, DB queries |
| Services | Business logic, orchestration | Direct DB access, HTTP logic |
| Repositories | Database queries only | Business logic, HTTP calls |
| Engines | Game system logic | AI calls, direct DB queries |
| AI Layer | Provider adapters | Game logic, DB access |
| UI Components | Rendering, display state | Business logic, API calls (use services/hooks) |

---

## 4. PYTHON STANDARDS

### 4.1 Version & Tooling

| Tool | Requirement |
|---|---|
| Python | 3.12+ |
| Formatter | Black (line length: 100) |
| Linter | Ruff |
| Type checker | MyPy (strict mode) |
| Test runner | Pytest |
| Dependency management | Poetry |

### 4.2 Type Annotations

**Required on all functions, methods, and class attributes.**

```python
# OK Correct
async def calculate_damage(
    attacker: CharacterStats,
    target: CharacterStats,
    skill: Skill,
    rng_seed: int,
) -> DamageResult:
    ...

# FORBIDDEN Forbidden
async def calculate_damage(a, b, skill, seed):
    ...
```

Never use `Any` except:
- When wrapping a third-party library with unknown types
- When the type is genuinely dynamic with justification in a comment

### 4.3 Function Design

**Maximum function length: 50 lines.** Preferred: 20 lines.

If a function exceeds 50 lines, it is doing too much. Split it.

```python
# OK Correct -- one responsibility per function
async def process_combat_action(
    combat_id: UUID,
    action: CombatAction,
) -> CombatResult:
    combat = await self._get_combat_or_raise(combat_id)
    result = self._combat_engine.resolve_action(combat, action)
    await self._persist_combat_result(combat_id, result)
    await self._publish_combat_events(result)
    return result

# FORBIDDEN Forbidden -- doing everything in one function
async def process_combat_action(combat_id, action):
    # 80 lines of mixed DB, logic, AI, and side effects
    ...
```

### 4.4 Class Design

**Maximum class length: 300 lines.** Preferred: 150 lines.

### 4.5 Naming Conventions

```python
# Variables and functions: snake_case
player_character = ...
async def calculate_initiative(...): ...

# Classes: PascalCase
class CombatEngine: ...
class QuestRepository: ...

# Constants: SCREAMING_SNAKE_CASE
MAX_PARTY_SIZE = 4
DAMAGE_MULTIPLIER_CRITICAL = 1.5
DEFAULT_FALLBACK_TIMEOUT_SECONDS = 10

# Private methods: _leading_underscore
def _validate_action_target(self, ...): ...

# Type aliases: PascalCase
CharacterId = UUID
WorldTick = int
```

### 4.6 Magic Numbers -- Prohibited

```python
# FORBIDDEN Forbidden
damage = attack * 1.37
if level >= 100:

# OK Required
DAMAGE_VARIANCE_MULTIPLIER = 1.37
CHARACTER_LEVEL_CAP = 100

damage = attack * DAMAGE_VARIANCE_MULTIPLIER
if level >= CHARACTER_LEVEL_CAP:
```

All constants belong in `app/core/constants.py` or in the relevant engine's constants module.

### 4.7 Error Handling

```python
# FORBIDDEN Forbidden -- swallowing exceptions
try:
    result = await some_operation()
except Exception:
    pass

# FORBIDDEN Forbidden -- catching too broadly without re-raising
try:
    result = await some_operation()
except Exception:
    logger.error("Something failed")

# OK Required -- classify, log, and raise or handle
try:
    result = await some_operation()
except DatabaseConnectionError as e:
    logger.error(
        "Database connection failed during combat resolution",
        extra={"combat_id": str(combat_id), "error": str(e)},
    )
    raise CombatSystemError("Combat resolution unavailable") from e
except ValueError as e:
    logger.warning("Invalid combat action", extra={"error": str(e)})
    raise InvalidActionError(str(e)) from e
```

### 4.8 Logging

```python
import structlog

logger = structlog.get_logger(__name__)

# OK Correct -- structured, contextual logging
logger.info(
    "Combat action resolved",
    combat_id=str(combat_id),
    action_type=action.type,
    damage=result.damage,
    target_hp_remaining=result.target_state.hp,
)

# FORBIDDEN Forbidden
print("Combat done")
logger.info("Combat action resolved" + str(result))
```

Never use `print()` in any backend code. All logs must be structured JSON compatible.

### 4.9 Comments

**Explain WHY, not WHAT.** Code explains what. Comments explain why.

```python
# FORBIDDEN Useless comment
# increment level by 1
character.level += 1

# OK Useful comment
# Level must be incremented BEFORE passive skill recalculation,
# because passive checks compare against the new level threshold.
character.level += 1
self._recalculate_passive_skills(character)
```

### 4.10 Docstrings

Required on all public services, engines, and repository methods.

```python
async def resolve_combat_action(
    self,
    combat: CombatState,
    action: CombatAction,
) -> CombatResult:
    """
    Resolve a single combat action within the current combat state.

    This is the primary entry point for all combat calculations.
    It is fully deterministic: identical combat and action inputs
    always produce identical results.

    Args:
        combat: The current combat state snapshot.
        action: The action being taken (attack, skill, item, guard, flee).

    Returns:
        CombatResult containing damage, state deltas, and log entries.

    Raises:
        InvalidCombatActionError: If the action is not valid in current state.
        InsufficientResourceError: If MP/stamina requirements are not met.
    """
```

---

## 5. TYPESCRIPT STANDARDS

### 5.1 Configuration

```json
// tsconfig.json -- required settings
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  }
}
```

### 5.2 Type Definitions

```typescript
// OK Correct -- explicit interfaces
interface CharacterData {
  id: string;
  name: string;
  level: number;
  currentHp: number;
  maxHp: number;
  currentMp: number;
  maxMp: number;
}

// FORBIDDEN Forbidden
const data: any = ...
const result: object = ...
```

### 5.3 Null Safety

```typescript
// OK Required -- explicit null handling
function getCharacterName(character: CharacterData | null): string {
  if (character === null) {
    return "Unknown";
  }
  return character.name;
}

// FORBIDDEN Forbidden -- ignoring null
function getCharacterName(character: CharacterData): string {
  return character.name; // crashes if null
}
```

### 5.4 React Component Standards

- Functional components only (no class components)
- Props must be typed via interfaces
- Use `React.FC` only if children are needed; otherwise type props directly

```typescript
// OK Correct
interface HealthBarProps {
  currentHp: number;
  maxHp: number;
  characterName: string;
}

const HealthBar = ({ currentHp, maxHp, characterName }: HealthBarProps) => {
  const percentage = (currentHp / maxHp) * 100;
  return (
    <div aria-label={`${characterName} health: ${currentHp} of ${maxHp}`}>
      <div style={{ width: `${percentage}%` }} />
    </div>
  );
};

export default HealthBar;
```

### 5.5 Component Size

**Maximum component length: 300 lines.** Preferred: 150 lines.

Components longer than 300 lines must be split into sub-components.

### 5.6 State Management Rules

```typescript
// Global game state: Zustand only
// Local UI state: useState
// Derived state: useMemo
// Side effects: useEffect (minimize use)

// OK Correct -- Zustand for shared state
const useGameStore = create<GameStore>((set) => ({
  worldTick: 0,
  currentLocation: null,
  setWorldTick: (tick) => set({ worldTick: tick }),
}));

// FORBIDDEN Forbidden -- prop drilling more than 2 levels
// FORBIDDEN Forbidden -- Redux unless explicitly justified and approved
```

### 5.7 API Service Pattern

```typescript
// OK Correct -- service layer for all API calls
// src/services/combatService.ts
export const combatService = {
  async startCombat(characterId: string, enemyIds: string[]): Promise<CombatState> {
    const { data } = await apiClient.post<ApiResponse<CombatState>>(
      '/combat/start',
      { characterId, enemyIds }
    );
    if (!data.success) {
      throw new ApiError(data.error.code, data.error.message);
    }
    return data.data;
  },
};

// FORBIDDEN Forbidden -- fetch() calls directly in components
```

---

## 6. DATABASE STANDARDS

### 6.1 Naming

All database objects use `snake_case`.

```sql
-- OK Correct
character_id, quest_progress, world_event_timestamp

-- FORBIDDEN Forbidden
CharacterID, QuestProgress, worldEventTimestamp
```

### 6.2 Required Columns

Every table must have:
```sql
id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
```

PostgreSQL must enable the `uuid-ossp` extension in the initial migration. Use `uuid_generate_v4()` consistently across schema docs, migrations, and seed data.

### 6.3 Migrations

Every schema change requires an Alembic migration. No manual changes to production schema.

```bash
# Creating a migration
alembic revision --autogenerate -m "add_relationship_fear_column"

# Applying migrations
alembic upgrade head

# Rolling back
alembic downgrade -1
```

Migration files must be reviewed before merging. Never squash or reorder existing migrations.

### 6.4 Query Standards

```python
# OK Correct -- repository pattern, async, typed
class CharacterRepository:
    async def get_by_id(self, character_id: UUID) -> Character | None:
        result = await self._session.execute(
            select(Character).where(Character.id == character_id)
        )
        return result.scalar_one_or_none()

# FORBIDDEN Forbidden -- raw SQL strings
await session.execute(
    text(f"SELECT * FROM characters WHERE id = '{character_id}'")
)

# FORBIDDEN Forbidden -- database access in controllers or engines
```

---

## 7. API STANDARDS

### 7.1 Versioning

All endpoints live under `/api/v1/`. Breaking changes require `/api/v2/`.

### 7.2 Response Format

All application JSON endpoints return this envelope. Prometheus metrics, empty `204` responses, file/stream responses, and shallow infrastructure probes are explicit exceptions documented in `API_SPEC.md`.

```json
// Success
{
  "success": true,
  "data": { ... },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}

// Failure
{
  "success": false,
  "error": {
    "code": "COMBAT_NOT_FOUND",
    "message": "No active combat session found for this character.",
    "details": {}
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### 7.3 HTTP Status Codes

| Code | When |
|---|---|
| 200 | Successful read or update |
| 201 | Successful creation |
| 400 | Validation failure (bad request) |
| 401 | Unauthenticated |
| 403 | Authenticated but unauthorized |
| 404 | Resource not found |
| 409 | Conflict (e.g., duplicate, invalid state transition) |
| 422 | Unprocessable entity (Pydantic validation) |
| 429 | Rate limited |
| 500 | Internal server error |
| 503 | Service unavailable (AI providers down, etc.) |

### 7.4 Error Codes

Error codes must be SCREAMING_SNAKE_CASE and descriptive:

```
CHARACTER_NOT_FOUND
COMBAT_ALREADY_ACTIVE
INVENTORY_FULL
INSUFFICIENT_MANA
QUEST_ALREADY_COMPLETED
INVALID_QUEST_STATE_TRANSITION
AI_PROVIDER_UNAVAILABLE
SAVE_TRANSACTION_FAILED
```

---

## 8. TESTING STANDARDS

### 8.1 Coverage Requirements

| Area | Minimum | Target |
|---|---|---|
| Game Engines | 90% | 95% |
| Services | 85% | 90% |
| Repositories | 80% | 90% |
| API Controllers | 80% | 85% |
| AI Adapters | 75% | 85% |

### 8.2 Test Structure

```
tests/
+-- unit/
|   +-- engines/
|   |   +-- test_combat_engine.py
|   |   +-- test_inventory_engine.py
|   |   +-- test_quest_engine.py
|   +-- services/
|   +-- ai/
+-- integration/
|   +-- test_character_flow.py
|   +-- test_combat_flow.py
|   +-- test_save_load.py
+-- e2e/
    +-- test_quest_completion.py
    +-- test_npc_dialogue.py
```

### 8.3 Test Naming

```python
# Pattern: test_{what}_{condition}_{expected}

def test_calculate_damage_with_critical_hit_returns_150_percent():
    ...

def test_equip_item_when_requirements_not_met_raises_error():
    ...

def test_quest_state_machine_completed_to_active_raises_invalid_transition():
    ...
```

### 8.4 Combat Engine Tests Must Verify Determinism

```python
def test_combat_damage_is_deterministic():
    """Identical inputs must always produce identical outputs."""
    attacker = create_test_character(attack=100)
    target = create_test_character(defense=20)
    action = CombatAction(type=ActionType.ATTACK)
    seed = 42

    result_1 = combat_engine.resolve_action(attacker, target, action, seed)
    result_2 = combat_engine.resolve_action(attacker, target, action, seed)

    assert result_1.damage == result_2.damage
    assert result_1.hit == result_2.hit
    assert result_1.crit == result_2.crit
```

---

## 9. GIT & VERSION CONTROL STANDARDS

### 9.1 Branch Naming

```
feature/combat-engine-phase-system
feature/rag-memory-summarization
fix/save-transaction-rollback
refactor/npc-service-decompose
docs/update-api-spec-v2
test/combat-engine-coverage
chore/upgrade-sqlalchemy-2
```

### 9.2 Commit Message Format (Conventional Commits)

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `security`

Examples:
```
feat(combat): add boss phase transition system
fix(save): prevent partial saves on transaction failure
refactor(npc): decompose NPC service into sub-services
docs(api): update combat endpoint response schemas
test(combat): add determinism verification for all damage types
perf(rag): add Redis cache layer for frequent memory queries
security(auth): enforce token refresh on password change
```

### 9.3 Pull Request Requirements

Before a PR can be merged:
- [ ] All CI checks pass (lint, type check, tests)
- [ ] Coverage did not decrease
- [ ] No secrets or API keys in diff
- [ ] Architecture boundaries not violated
- [ ] `TECH_DEBT.md` updated if debt is being added
- [ ] Relevant Markdown contracts updated
- [ ] Release checklist impact reviewed for gameplay, security, persistence, and operations changes
- [ ] At least one reviewer approved
- [ ] No unresolved review comments

---

## 10. SECURITY STANDARDS

### 10.1 Secrets Management

```bash
# OK Correct -- environment variables only
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/yggdrasil
OPENAI_API_KEY=sk-...

# FORBIDDEN Forbidden -- hardcoded in code
DATABASE_URL = "postgresql://..."
OPENAI_API_KEY = "sk-..."
```

Never commit `.env` files. Commit `.env.example` with non-secret sample values only.

### 10.2 Input Validation

Every API endpoint validates input via Pydantic schema before any processing occurs. No raw user input reaches the service or engine layer without validation.

### 10.3 SQL Injection Prevention

Use SQLAlchemy ORM or parameterized queries exclusively. Never interpolate user input into SQL strings.

---

## 11. PERFORMANCE STANDARDS

### 11.1 Profile Before Optimizing

Never optimize code without a measured performance problem. Premature optimization creates maintenance debt.

Optimization order:
1. Measure and identify bottleneck
2. Propose fix with expected improvement
3. Implement
4. Measure again to confirm improvement

### 11.2 Database Query Rules

- All queries on foreign keys and frequently-filtered columns must have indexes
- Never load more rows than needed (use `LIMIT`, pagination)
- Use `select()` with specific columns when loading large datasets
- N+1 query patterns are prohibited -- use `joinedload` or `selectinload`

### 11.3 Async Requirements

All I/O-bound operations must be async:
- Database queries: `await session.execute(...)`
- AI provider calls: `await provider.generate(...)`
- Redis operations: `await redis.get(...)`
- HTTP client calls: `await httpx_client.post(...)`

---

## 12. PROMPT ENGINEERING STANDARDS

### 12.1 Prompt Storage

All AI prompts stored as files -- never as inline strings in code.

```
backend/app/ai/prompts/
+-- dialogue/
|   +-- npc_greeting.txt
|   +-- npc_quest_offer.txt
|   +-- npc_merchant.txt
+-- lore/
|   +-- item_lore.txt
|   +-- location_description.txt
|   +-- dungeon_atmosphere.txt
+-- narration/
    +-- combat_victory.txt
    +-- boss_introduction.txt
    +-- world_event.txt
```

### 12.2 Prompt Design Requirements

Every prompt must include:
- Clear instruction section
- World context section (populated from RAG)
- Output format specification
- Constraint list (what AI must not do or mention)

### 12.3 Prompt Versioning

Prompt files are versioned. Never edit a prompt file in-place for a breaking change -- create a new version:
```
npc_greeting_v1.txt
npc_greeting_v2.txt
```

---

## 13. DEFINITION OF FEATURE COMPLETE

A feature or system is complete when:

| Criterion | Standard |
|---|---|
| Implemented | Follows architecture, passes code review |
| Tested | Unit + integration + regression, meets coverage target |
| Documented | Public interfaces have docstrings, complex logic explained |
| Observable | Logs, metrics, traces, and alerts exist for release-critical paths |
| Secure | No secrets, input validated, dependencies audited |
| Save-compatible | State is serializable, backward-compatible |
| Docker-compatible | Starts correctly via `docker compose up` |
| Recoverable | Failure modes are defined and handled |

Release-critical paths include save/load, combat completion, quest transition, inventory mutation, equipment mutation, authentication, AI fallback, RAG retrieval, and database migration.

---

## 14. FINAL PRINCIPLE

```
Readable today > Clever tomorrow.
Consistent always > Personal preference sometimes.
Tested always > Assumed correct sometimes.
```
