# TESTING_STRATEGY.md
# YGGDRASIL CHRONICLES
# Comprehensive Testing Strategy
Version: 2.0 -- Enterprise Edition
Status: Normative
Last reviewed: 2026-06-13

---

## 1. TESTING PHILOSOPHY

**A feature without tests is not done. It is a ticking liability.**

The goal of testing in Yggdrasil Chronicles is not to achieve a coverage number. The goal is to **guarantee behavioral correctness** across the following critical properties:

1. **Determinism** -- Combat always produces identical results for identical inputs
2. **Persistence** -- Save/load always preserves complete game state
3. **Isolation** -- AI never influences gameplay outcomes
4. **Consistency** -- World state is never partially updated
5. **Availability** -- Game runs when all cloud AI providers are offline

---

## 2. TESTING PYRAMID

```
          +-----------------+
          |   E2E Tests     |  5% -- Full player workflows
          |  (Playwright)   |  Slowest, highest confidence
          +-----------------+
          |  Integration    |  25% -- Cross-layer behavior
          |    Tests        |  Services + DB + Redis + Qdrant
          +-----------------+
          |   Unit Tests    |  70% -- Logic in isolation
          |   (Pytest)      |  Fast, targeted, deterministic
          +-----------------+
```

---

## 3. COVERAGE REQUIREMENTS

### Backend (Python)

| Module | Minimum | Target |
|---|---|---|
| Combat Engine | 90% | 95% |
| Quest Engine | 90% | 95% |
| Inventory Engine | 85% | 92% |
| Equipment Engine | 85% | 92% |
| Progression Engine | 85% | 92% |
| Loot Engine | 85% | 90% |
| Services (all) | 85% | 90% |
| Repositories (all) | 80% | 90% |
| AI Orchestrator | 80% | 88% |
| API Controllers | 80% | 85% |
| RAG System | 75% | 85% |

### Frontend (TypeScript)

| Module | Minimum | Target |
|---|---|---|
| Game Presentation Systems (client-side, non-authoritative) | 80% | 88% |
| Zustand Stores | 75% | 85% |
| Service Layer | 75% | 85% |
| Custom Hooks | 70% | 80% |
| React Components | 60% | 75% |

---

## 4. UNIT TESTS

### 4.1 What to Unit Test

- Engine logic (combat formulas, quest state transitions, inventory operations)
- Service methods (in isolation, with mocked repositories and engines)
- Repository query construction in isolation; executed repository behavior belongs in integration tests against PostgreSQL.
- AI adapter formatting (input/output structure, not actual AI calls)
- Prompt builder logic
- Memory scoring formulas
- Event creation and serialization

### 4.2 What NOT to Unit Test

- Third-party library internals
- Configuration loading
- Simple data class constructors

### 4.3 Naming Convention

```python
# Pattern: test_{subject}_{scenario}_{expected_outcome}

def test_combat_damage_formula_critical_hit_returns_150_percent_base():
    ...

def test_quest_state_machine_transition_completed_to_active_raises_error():
    ...

def test_inventory_add_item_when_full_raises_inventory_full_error():
    ...
```

### 4.4 Combat Engine Unit Tests (Critical)

```python
# tests/unit/engines/test_combat_engine.py

class TestCombatDeterminism:
    """
    Combat is the most critical deterministic system.
    These tests verify that identical inputs ALWAYS produce identical outputs.
    """

    def test_physical_attack_is_deterministic(self, combat_engine):
        attacker = build_character(attack=100, dex=30)
        target = build_character(defense=20, evasion=10)
        action = CombatAction(type=ActionType.ATTACK)
        seed = 42

        result_a = combat_engine.resolve_action(attacker, target, action, seed)
        result_b = combat_engine.resolve_action(attacker, target, action, seed)

        assert result_a == result_b

    def test_skill_damage_scales_with_modifier(self, combat_engine):
        attacker = build_character(attack=100)
        target = build_character(defense=0)
        skill = build_skill(modifier=2.0, type=SkillType.PHYSICAL)
        action = CombatAction(type=ActionType.SKILL, skill=skill)

        result = combat_engine.resolve_action(attacker, target, action, seed=1)

        assert result.damage == pytest.approx(200, rel=0.01)

    def test_elemental_fire_vs_ice_applies_1_5x_multiplier(self, combat_engine):
        attacker = build_character(magic_attack=100, element=Element.FIRE)
        target = build_character(magic_defense=0, element=Element.ICE)

        base_result = combat_engine.resolve_magic(attacker, target, Element.NONE, seed=1)
        fire_result = combat_engine.resolve_magic(attacker, target, Element.FIRE, seed=1)

        assert fire_result.damage == pytest.approx(base_result.damage * 1.5, rel=0.01)

    def test_combat_does_not_call_ai_provider(self, combat_engine, mock_ai_orchestrator):
        attacker = build_character()
        target = build_character()
        action = CombatAction(type=ActionType.ATTACK)

        combat_engine.resolve_action(attacker, target, action, seed=1)

        mock_ai_orchestrator.generate_dialogue.assert_not_called()
        mock_ai_orchestrator.generate_narration.assert_not_called()
        mock_ai_orchestrator.generate_lore.assert_not_called()
```

### 4.5 Quest State Machine Tests

```python
class TestQuestStateMachine:

    @pytest.mark.parametrize("from_state,to_state,should_succeed", [
        (QuestStatus.NOT_STARTED, QuestStatus.ACTIVE,    True),
        (QuestStatus.ACTIVE,      QuestStatus.COMPLETED,  True),
        (QuestStatus.ACTIVE,      QuestStatus.FAILED,     True),
        (QuestStatus.FAILED,      QuestStatus.ARCHIVED,   True),
        (QuestStatus.COMPLETED,   QuestStatus.ACTIVE,     False),
        (QuestStatus.COMPLETED,   QuestStatus.FAILED,     False),
        (QuestStatus.ARCHIVED,    QuestStatus.ACTIVE,     False),
        (QuestStatus.NOT_STARTED, QuestStatus.COMPLETED,  False),
    ])
    def test_state_transitions(self, quest_engine, from_state, to_state, should_succeed):
        quest = build_character_quest(status=from_state)
        if should_succeed:
            quest_engine.transition(quest, to_state)
            assert quest.status == to_state
        else:
            with pytest.raises(InvalidQuestTransitionError):
                quest_engine.transition(quest, to_state)
```

---

## 5. INTEGRATION TESTS

### 5.1 Purpose

Integration tests verify that multiple layers work correctly together. They use a **real test database** (PostgreSQL), **real Redis**, and **real Qdrant**, but mock external AI providers.

SQLite is prohibited for persistence-contract tests because it does not reproduce PostgreSQL types, constraints, locking, indexes, or transaction behavior.

### 5.2 Test Database Setup

```python
# conftest.py (integration)
@pytest.fixture(scope="session")
async def test_db():
    """
    Spin up isolated test database.
    Each test session gets a clean schema.
    """
    engine = create_async_engine(settings.TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(autouse=True)
async def rollback_after_test(test_db):
    """Each test runs in a transaction that is rolled back afterward."""
    async with test_db.begin() as conn:
        yield conn
        await conn.rollback()
```

### 5.3 Required Integration Test Scenarios

```python
# tests/integration/test_combat_flow.py

async def test_full_combat_encounter_resolves_correctly(client, test_character, test_enemy):
    """A full combat from start to victory produces correct XP and loot."""
    # Start combat
    start_resp = await client.post("/api/v1/combat/start", json={...})
    combat_id = start_resp.json()["data"]["combat_id"]

    # Simulate turns until victory
    while True:
        action_resp = await client.post(f"/api/v1/combat/action", json={
            "combat_id": combat_id,
            "action_type": "attack",
            "target_id": test_enemy.id,
        })
        status = action_resp.json()["data"]["combat_status"]
        if status != "ongoing":
            break

    assert status == "victory"
    assert action_resp.json()["data"]["rewards"]["experience"] > 0

    # Verify character XP was saved
    char_resp = await client.get(f"/api/v1/characters/{test_character.id}")
    assert char_resp.json()["data"]["experience"] > 0
```

### 5.4 Save/Load Integration Test

```python
async def test_save_preserves_complete_game_state(client, test_character):
    """
    Game state before save must be identical to game state after load.
    This is the most critical integration test in the project.
    """
    # Modify state in multiple systems
    await client.post("/inventory/use", json={...})     # use item
    await client.post("/equipment/equip", json={...})  # equip weapon
    await client.post(f"/quests/{quest_id}/accept", json={...})  # accept quest

    # Capture state before save
    state_before = await capture_full_character_state(client, test_character.id)

    # Save
    save_resp = await client.post("/api/v1/save", json={"character_id": test_character.id})
    save_id = save_resp.json()["data"]["save_id"]

    # Modify state after save (to prove load actually restores)
    await client.post("/inventory/drop", json={...})

    # Load saved state
    await client.post("/api/v1/load", json={"save_id": save_id})

    # Capture state after load
    state_after = await capture_full_character_state(client, test_character.id)

    assert state_before == state_after
```

---

## 6. END-TO-END TESTS

### 6.1 Tool: Playwright

E2E tests use Playwright to drive a real browser against the full running application.

```typescript
// tests/e2e/character_creation.spec.ts

test('player can create character and enter world', async ({ page }) => {
    await page.goto('/');
    await page.fill('[data-testid="email"]', 'test@example.com');
    await page.fill('[data-testid="password"]', 'testpassword123');
    await page.click('[data-testid="login-button"]');

    await expect(page).toHaveURL('/characters');
    await page.click('[data-testid="create-character"]');
    await page.fill('[data-testid="character-name"]', 'Aji');
    await page.click('[data-testid="race-human"]');
    await page.click('[data-testid="job-warrior"]');
    await page.click('[data-testid="confirm-creation"]');

    await expect(page.locator('[data-testid="world-map"]')).toBeVisible();
    await expect(page.locator('[data-testid="character-name"]')).toContainText('Aji');
});
```

### 6.2 Required E2E Scenarios

| Scenario | Priority |
|---|---|
| Register, login, logout | Critical |
| Create character, enter world | Critical |
| Move between locations | Critical |
| Talk to NPC, receive response | Critical |
| Accept, progress, complete quest | Critical |
| Fight combat encounter, win | Critical |
| Fight combat encounter, lose | High |
| Save game, reload, verify state | Critical |
| Equip/unequip items | High |
| Use consumable item | High |
| Attempt combat with all AI providers offline | Critical |

---

## 7. AI ISOLATION TESTS

These tests verify the absolute boundary between AI and gameplay systems.

```python
# tests/unit/test_ai_isolation.py

class TestAIIsolation:
    """
    Verify that AI providers cannot influence gameplay outcomes.
    These tests are non-negotiable -- failure here is a critical bug.
    """

    async def test_combat_result_unchanged_when_ai_offline(
        self, combat_engine, mock_ai_orchestrator
    ):
        """Combat must resolve identically whether AI is online or offline."""
        mock_ai_orchestrator.side_effect = AIProviderError("All providers offline")

        attacker = build_character(attack=100)
        target = build_character(defense=20)
        action = CombatAction(type=ActionType.ATTACK)

        # Must not raise -- must complete without AI
        result = combat_engine.resolve_action(attacker, target, action, seed=42)

        assert result.damage > 0
        assert result is not None

    async def test_quest_reward_unchanged_when_ai_offline(
        self, quest_engine, mock_ai_orchestrator
    ):
        mock_ai_orchestrator.side_effect = AIProviderError("Offline")
        quest = build_quest(reward_gold=500, reward_experience=1000)

        rewards = quest_engine.calculate_rewards(quest)

        assert rewards.gold == 500
        assert rewards.experience == 1000

    async def test_loot_table_unchanged_when_ai_offline(
        self, loot_engine, mock_ai_orchestrator
    ):
        mock_ai_orchestrator.side_effect = AIProviderError("Offline")
        monster = build_monster(loot_table_id=test_loot_table.id)

        loot = loot_engine.resolve_loot(monster, seed=42)

        assert loot is not None
        # Loot is determined by engine, never by AI
```

---

## 8. PERFORMANCE TESTS

### 8.1 Load Testing Tool: Locust

```python
# tests/performance/locustfile.py

class PlayerBehavior(TaskSet):

    @task(3)
    def check_character(self):
        self.client.get(f"/api/v1/characters/{self.character_id}")

    @task(2)
    def combat_action(self):
        self.client.post("/api/v1/combat/action", json={...})

    @task(1)
    def npc_dialogue(self):
        self.client.post(f"/api/v1/npcs/{self.npc_id}/talk", json={
            "character_id": self.character_id,
            "message": "Hello"
        })
```

### 8.2 Performance Assertions

| Endpoint | p50 | p95 | p99 |
|---|---|---|---|
| GET /characters/{id} | < 50ms | < 100ms | < 200ms |
| POST /combat/action | < 100ms | < 200ms | < 500ms |
| POST /npcs/{id}/talk | < 500ms | < 2000ms | < 5000ms |
| POST /save | < 200ms | < 500ms | < 1000ms |
| POST /load | < 300ms | < 700ms | < 1500ms |

---

## 9. REGRESSION TESTS

### 9.1 Regression Test Policy

When a bug is fixed:
1. Write a test that **reproduces the bug** first
2. Verify the test fails before the fix
3. Apply the fix
4. Verify the test passes
5. The test stays in the suite permanently

### 9.2 Critical Regression Guard List

These bugs, once fixed, must never return:

| ID | Bug Description | Test Location |
|---|---|---|
| REG-001 | Partial save on transaction failure | test_save_atomicity |
| REG-002 | AI narration overwriting HP values | test_ai_isolation |
| REG-003 | Quest completing on wrong condition | test_quest_completion |
| REG-004 | Inventory item duplication on stack merge | test_inventory_stack_merge |
| REG-005 | Dead boss respawning after reload | test_boss_permanent_death |
| REG-006 | Event published for a rolled-back mutation | test_outbox_atomicity |
| REG-007 | Duplicate outbox delivery applies side effects twice | test_event_consumer_idempotency |

---

## 10. CI/CD PIPELINE

### 10.1 Required CI Checks (all must pass to merge)

```yaml
# .github/workflows/ci.yml

jobs:
  lint:
    - ruff check backend/
    - black --check backend/
    - mypy backend/ --strict

  test-unit:
    - pytest tests/unit/ --cov=app --cov-fail-under=80

  test-integration:
    services: [postgres, redis, qdrant]
    - pytest tests/integration/

  test-frontend:
    - tsc --noEmit
    - eslint src/
    - vitest run --coverage

  security:
    - pip-audit
    - npm audit --audit-level=high
    - gitleaks detect --no-git
```

Release candidates must also run:

- backup and restore drill from `OPERATIONS_RUNBOOK.md`
- migration dry run against staging data
- AI-provider-offline smoke test
- save/load compatibility regression suite
- observability smoke test for logs, metrics, traces, and alerts
- account export/deletion and deletion-tombstone restore tests
- SBOM, license, container, and build-provenance verification
- accessibility checks for keyboard navigation, focus, contrast, and critical screen-reader flows
- chaos/failure tests for database failover, Redis loss, Qdrant loss, worker restart, and AI-provider outage

Release evidence must be retained as immutable CI artifacts and linked from `RELEASE_CHECKLIST.md`.

### 10.2 Coverage Gate

Coverage must never decrease on main branch. A PR that lowers coverage below the current baseline is automatically blocked.

---

## 11. TESTING ENVIRONMENTS

| Environment | Purpose | Data | AI Providers |
|---|---|---|---|
| `local` | Developer machines | Synthetic seed data | Mocked or Ollama |
| `test` | CI pipeline | Isolated per run | Always mocked |
| `staging` | Pre-release verification | Snapshot of prod data | Real providers (rate-limited) |
| `production` | Live game | Real player data | Real providers |

### 11.1 Windows Local Integration and Regression Path

The repository root provides a Docker Compose-backed Windows test entrypoint:

```powershell
.\test-local.ps1
```

This command uses `compose.test.yaml` and `.env.test` rather than the normal
development stack. The test stack exposes PostgreSQL, Redis, and Qdrant only on
localhost test ports, applies Alembic migrations, verifies canonical seed data
created by migrations, and runs backend integration and regression tests inside
a backend test runner container with Poetry dev dependencies installed.

The default command is equivalent to:

```bash
pytest -c pyproject.toml ../tests/integration ../tests/regression
```

Use `.\test-local.ps1 -Suite integration` or
`.\test-local.ps1 -Suite regression` for focused runs. Tests must keep using
fixtures in `tests/conftest.py` or local stubs/mocks for external AI behavior;
cloud provider credentials are intentionally empty in `.env.test`.

---

## 12. MOCK PATTERNS

### AI Provider Mock

```python
@pytest.fixture
def mock_ai_orchestrator(mocker):
    """
    Default mock returns pre-written NPC dialogue.
    Tests that need to verify AI failure use .side_effect.
    """
    mock = mocker.patch("app.ai.orchestrator.AIOrchestrator")
    mock.return_value.generate_dialogue.return_value = DialogueResponse(
        text="Greetings, adventurer.",
        emotion="neutral",
    )
    return mock
```

### Database Mock (Unit Tests)

```python
@pytest.fixture
def mock_character_repo(mocker):
    mock = mocker.MagicMock(spec=CharacterRepository)
    mock.get_by_id.return_value = build_character(level=10, hp=200)
    return mock
```

---

## 13. FINAL RULE

```
A bug found by a test is fixed in minutes.
A bug found in production is fixed in days -- and may affect player data.

Test everything that matters.
Everything in this game matters.
```
