import json
from uuid import UUID

HUMAN_ID = UUID("51000000-0000-0000-0000-000000000001")
GREENWOOD_ID = UUID("56000000-0000-0000-0000-000000000002")

npc_data = {
    "id": UUID("74000000-0000-0000-0000-000000000008"),
    "name": "Innkeeper Elena",
    "race_id": HUMAN_ID,
    "home_location_id": GREENWOOD_ID,
    "occupation": "Innkeeper",
    "role": "INNKEEPER",
    "personality_profile": {"archetype": "hospitable_host"},
    "schedule": [{"start_hour": 0, "end_hour": 24, "location_id": str(GREENWOOD_ID)}],
    "knowledge": {"topics": ["resting", "local_rumors"]},
    "is_alive": True,
}

# The fields that are JSONB in the database:
json_fields = ["personality_profile", "schedule", "knowledge"]

for field in json_fields:
    try:
        json.dumps(npc_data[field])
        print(f"Field {field} is serializable")
    except TypeError as e:
        print(f"Field {field} failed: {e}")
