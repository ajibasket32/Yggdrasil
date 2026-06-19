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
    SeedExpectation("npcs", 7),
    SeedExpectation("quests", 7),
    SeedExpectation("quest_steps", 8),
)

EXPECTED_NAMED_ROWS = (
    ("races", "Human"),
    ("jobs", "Warrior"),
    ("items", "Field Potion"),
    ("locations", "Greenwood Verge"),
    ("locations", "Ancient Crossroads"),
    ("locations", "Sylvan Branch"),
    ("npcs", "Warden Elara"),
    ("npcs", "Blacksmith Hagar"),
    ("quests", "The Rootbound Watch"),
    ("quests", "Sylvan Branch Patrol"),
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
    for expectation in EXPECTED_SEEDS:
        count = await _count_rows(expectation.table_name)
        if count < expectation.minimum_count:
            failures.append(
                f"{expectation.table_name}: expected at least "
                f"{expectation.minimum_count}, found {count}"
            )
    for table_name, name in EXPECTED_NAMED_ROWS:
        if not await _has_named_row(table_name, name):
            failures.append(f'{table_name}: missing required row "{name}"')
    await engine.dispose()
    if failures:
        raise SystemExit("Seed verification failed:\n" + "\n".join(failures))
    print("Seed verification passed.")


if __name__ == "__main__":
    asyncio.run(verify())
