"""Verify canonical migration seed data required by local integration tests."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy import text

from app.core.database import engine


@dataclass(frozen=True)
class SeedExpectation:
    table_name: str
    minimum_count: int


EXPECTED_SEEDS = (
    SeedExpectation("races", 4),
    SeedExpectation("jobs", 9),
    SeedExpectation("skills", 9),
    SeedExpectation("items", 9),
    SeedExpectation("equipment_slots", 8),
    SeedExpectation("locations", 6),
    SeedExpectation("factions", 5),
    SeedExpectation("dungeons", 5),
    SeedExpectation("npcs", 8),
    SeedExpectation("quests", 9),
    SeedExpectation("quest_steps", 12),
    SeedExpectation("shops", 1),
)

EXPECTED_NAMED_ROWS = (
    ("races", "Human"),
    ("jobs", "Warrior"),
    ("items", "Field Potion"),
    ("items", "Steel Sword"),
    ("locations", "Greenwood Verge"),
    ("locations", "Ancient Crossroads"),
    ("locations", "Sylvan Branch"),
    ("npcs", "Warden Elara"),
    ("npcs", "Blacksmith Hagar"),
    ("npcs", "Scout Kael"),
    ("npcs", "Innkeeper Elena"),
    ("quests", "The Rootbound Watch"),
    ("quests", "Sylvan Reconnaissance"),
    ("quests", "The Master's Iron"),
    ("quests", "A Scout's Tool"),
    ("quests", "The Blacksmith's Request"),
    ("quests", "Scouting the Border"),
    ("shops", "Silas's Sundries"),
)


async def _count_rows(table_name: str) -> int:
    async with engine.begin() as connection:
        return int(
            await connection.scalar(text(f'SELECT count(*) FROM "{table_name}"')) or 0
        )


async def _has_named_row(table_name: str, name: str) -> bool:
    label_column = "title" if table_name == "quests" else "name"
    async with engine.begin() as connection:
        count = await connection.scalar(
            text(
                f'SELECT count(*) FROM "{table_name}" '
                f'WHERE "{label_column}" = :name'
            ),
            {"name": name},
        )
    return int(count or 0) == 1


async def verify() -> None:
    """Fail loudly if migrated test seed data is incomplete."""
    failures: list[str] = []
    print("Starting seed verification...")
    for expectation in EXPECTED_SEEDS:
        try:
            count = await _count_rows(expectation.table_name)
            if count < expectation.minimum_count:
                failures.append(
                    f"{expectation.table_name}: expected at least "
                    f"{expectation.minimum_count}, found {count}"
                )
            else:
                print(f"  OK: {expectation.table_name} has {count} rows.")
        except Exception as e:
            failures.append(f"{expectation.table_name}: error counting rows: {e}")

    for table_name, name in EXPECTED_NAMED_ROWS:
        try:
            if not await _has_named_row(table_name, name):
                failures.append(f'{table_name}: missing required row "{name}"')
            else:
                print(f'  OK: {table_name} has required row "{name}".')
        except Exception as e:
            failures.append(f'{table_name}: error checking row "{name}": {e}')

    await engine.dispose()
    if failures:
        print("\nSeed verification FAILED:")
        for failure in failures:
            print(f"  - {failure}")
        raise SystemExit(1)
    print("\nSeed verification passed.")


if __name__ == "__main__":
    asyncio.run(verify())
