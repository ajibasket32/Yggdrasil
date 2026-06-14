"""Run deployed v0.6 victory, persistence, retry, and defeat smoke journeys."""

import asyncio
import json
from uuid import UUID, uuid4

import httpx
from sqlalchemy import select

from app.core.database import session_factory
from app.engines.combat import SeededRolls
from app.models.combat import CombatParticipant

API_ROOT = "http://backend:8000/api/v1"


async def request(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    player_id: UUID,
    *,
    payload: dict[str, object] | None = None,
    key: str | None = None,
) -> object:
    headers = {"X-Player-ID": str(player_id)}
    if key is not None:
        headers["Idempotency-Key"] = key
    response = await client.request(method, path, headers=headers, json=payload)
    response.raise_for_status()
    body = response.json()
    if not body.get("success"):
        raise RuntimeError(f"API returned an unsuccessful envelope: {body}")
    return body["data"]


async def create_ready_character(
    client: httpx.AsyncClient,
    player_id: UUID,
    name: str,
) -> dict[str, object]:
    definitions_response = await client.get("/character-definitions")
    definitions_response.raise_for_status()
    definitions = definitions_response.json()["data"]
    warrior = next(
        value for value in definitions["starting_jobs"] if value["name"] == "Warrior"
    )
    character = await request(
        client,
        "POST",
        "/characters",
        player_id,
        payload={
            "name": name,
            "race_id": definitions["races"][0]["id"],
            "gender": "Unspecified",
            "alignment": "NEUTRAL",
            "starting_job_id": warrior["id"],
        },
        key=f"create-{player_id}",
    )
    if not isinstance(character, dict):
        raise RuntimeError("Character response was not an object")
    locations = await request(
        client,
        "GET",
        f"/characters/{character['id']}/locations",
        player_id,
    )
    if not isinstance(locations, list):
        raise RuntimeError("Location response was not a list")
    greenwood = next(value for value in locations if value["name"] == "Greenwood Verge")
    await request(
        client,
        "POST",
        f"/characters/{character['id']}/travel",
        player_id,
        payload={"destination_id": greenwood["id"]},
        key=f"travel-{player_id}",
    )
    return character


async def start_combat(
    client: httpx.AsyncClient,
    player_id: UUID,
    character_id: str,
    seed: int,
) -> dict[str, object]:
    encounters = await request(
        client,
        "GET",
        f"/characters/{character_id}/encounters",
        player_id,
    )
    if not isinstance(encounters, list) or not encounters:
        raise RuntimeError("No deployed combat encounter was available")
    state = await request(
        client,
        "POST",
        "/combat/start",
        player_id,
        payload={
            "character_id": character_id,
            "encounter_definition_id": encounters[0]["id"],
            "seed": seed,
        },
        key=f"start-{player_id}",
    )
    if not isinstance(state, dict):
        raise RuntimeError("Combat response was not an object")
    return state


async def victory_journey(client: httpx.AsyncClient) -> dict[str, object]:
    player_id = uuid4()
    character = await create_ready_character(client, player_id, "Release Victor")
    state = await start_combat(client, player_id, str(character["id"]), 17)
    final_key = ""
    index = 0
    while state["status"] == "ACTIVE":
        final_key = f"attack-{player_id}-{index}"
        resolved = await request(
            client,
            "POST",
            "/combat/action",
            player_id,
            payload={"combat_id": state["combat_id"], "action_type": "ATTACK"},
            key=final_key,
        )
        if not isinstance(resolved, dict):
            raise RuntimeError("Combat action response was not an object")
        state = resolved
        index += 1
        if index > 20:
            raise RuntimeError("Victory smoke exceeded the deterministic turn limit")
    if state["status"] != "VICTORY":
        raise RuntimeError(f"Expected victory, received {state['status']}")

    replay = await request(
        client,
        "POST",
        "/combat/action",
        player_id,
        payload={"combat_id": state["combat_id"], "action_type": "ATTACK"},
        key=final_key,
    )
    if replay != state:
        raise RuntimeError("Final action retry returned a different result")
    sheet = await request(
        client,
        "GET",
        f"/characters/{character['id']}",
        player_id,
    )
    if not isinstance(sheet, dict):
        raise RuntimeError("Character sheet response was not an object")
    if sheet["experience"] != 45 or sheet["gold"] != 118:
        raise RuntimeError(f"Rewards were not persisted exactly once: {sheet}")

    save = await request(
        client,
        "POST",
        "/save",
        player_id,
        payload={"character_id": character["id"], "save_name": "v0.6 smoke"},
        key=f"save-{player_id}",
    )
    if not isinstance(save, dict):
        raise RuntimeError("Save response was not an object")
    loaded = await request(
        client,
        "POST",
        "/load",
        player_id,
        payload={"save_id": save["save_id"]},
        key=f"load-{player_id}",
    )
    if not isinstance(loaded, dict):
        raise RuntimeError("Load response was not an object")
    snapshot = loaded["snapshot"]["character"]
    if snapshot["experience"] != 45 or snapshot["gold"] != 118:
        raise RuntimeError("Combat rewards were absent from the loaded save")

    logs = await request(
        client,
        "GET",
        f"/combat/{state['combat_id']}/log",
        player_id,
    )
    if not isinstance(logs, list):
        raise RuntimeError("Combat log response was not a list")
    if [entry["sequence"] for entry in logs] != list(range(len(logs))):
        raise RuntimeError("Combat log sequence was not contiguous")
    return {
        "status": state["status"],
        "combat_id": state["combat_id"],
        "actions": index,
        "experience": sheet["experience"],
        "gold": sheet["gold"],
        "save_id": save["save_id"],
        "log_entries": len(logs),
    }


async def defeat_journey(client: httpx.AsyncClient) -> dict[str, object]:
    seed = next(
        value for value in range(1000) if SeededRolls.percent(value, 1, "hit") <= 90
    )
    player_id = uuid4()
    character = await create_ready_character(client, player_id, "Release Defeat")
    state = await start_combat(client, player_id, str(character["id"]), seed)
    async with session_factory() as session, session.begin():
        participant = (
            await session.execute(
                select(CombatParticipant).where(
                    CombatParticipant.encounter_id == UUID(str(state["combat_id"])),
                    CombatParticipant.side == "PLAYER",
                )
            )
        ).scalar_one()
        participant.current_hp = 1
    resolved = await request(
        client,
        "POST",
        "/combat/action",
        player_id,
        payload={"combat_id": state["combat_id"], "action_type": "WAIT"},
        key=f"defeat-{player_id}",
    )
    if not isinstance(resolved, dict) or resolved["status"] != "DEFEAT":
        raise RuntimeError(f"Expected defeat, received {resolved}")
    sheet = await request(
        client,
        "GET",
        f"/characters/{character['id']}",
        player_id,
    )
    if not isinstance(sheet, dict) or sheet["current_hp"] != 1:
        raise RuntimeError("Defeat recovery did not persist exactly 1 HP")
    return {
        "status": resolved["status"],
        "combat_id": resolved["combat_id"],
        "recovery_hp": sheet["current_hp"],
    }


async def main() -> None:
    async with httpx.AsyncClient(base_url=API_ROOT, timeout=20) as client:
        victory = await victory_journey(client)
        defeat = await defeat_journey(client)
    print(json.dumps({"victory": victory, "defeat": defeat}, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
