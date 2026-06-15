import type {
  CharacterDefinitions,
  CharacterSheet,
  CharacterSummary,
  CombatActionType,
  CombatState,
  CreateCharacterInput,
  Equipment,
  EncounterDefinition,
  Inventory,
  Location,
  Dungeon,
  Faction,
  JournalEntry,
  Narrative,
  Npc,
  DialogueTopic,
  NpcInteraction,
  Quest,
} from "../types/gameplay";

interface ApiEnvelope<T> {
  success: true;
  data: T;
}

interface ApiErrorEnvelope {
  error?: {
    message?: string;
  };
}

const PLAYER_ID_KEY = "yggdrasil-player-id";
const FALLBACK_PLAYER_ID = "9d463696-4daf-4f3c-bb8c-f21389acb991";

export const getPlayerId = (): string => {
  const stored = window.localStorage.getItem(PLAYER_ID_KEY);
  if (stored !== null) {
    return stored;
  }
  const generated =
    typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : FALLBACK_PLAYER_ID;
  window.localStorage.setItem(PLAYER_ID_KEY, generated);
  return generated;
};

const request = async <T>(
  path: string,
  playerId?: string,
  init?: RequestInit,
): Promise<T> => {
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  if (init?.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  if (playerId !== undefined) {
    headers.set("X-Player-ID", playerId);
  }

  const response = await fetch(`/api/v1${path}`, { ...init, headers });
  const payload = (await response.json()) as ApiEnvelope<T> | ApiErrorEnvelope;
  if (!response.ok || !("data" in payload)) {
    const message =
      "error" in payload ? payload.error?.message : "Request failed";
    throw new Error(message ?? "Request failed");
  }
  return payload.data;
};

export const gameApi = {
  definitions: () => request<CharacterDefinitions>("/character-definitions"),
  characters: (playerId: string) =>
    request<CharacterSummary[]>("/characters", playerId),
  character: (playerId: string, characterId: string) =>
    request<CharacterSheet>(`/characters/${characterId}`, playerId),
  createCharacter: (
    playerId: string,
    input: CreateCharacterInput,
    idempotencyKey: string,
  ) =>
    request<CharacterSheet>("/characters", playerId, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify(input),
    }),
  inventory: (playerId: string, characterId: string) =>
    request<Inventory>(`/characters/${characterId}/inventory`, playerId),
  equipment: (playerId: string, characterId: string) =>
    request<Equipment>(`/characters/${characterId}/equipment`, playerId),
  locations: (playerId: string, characterId: string) =>
    request<Location[]>(`/characters/${characterId}/locations`, playerId),
  travel: (
    playerId: string,
    characterId: string,
    destinationId: string,
    idempotencyKey: string,
  ) =>
    request<{
      character_id: string;
      origin: Location;
      destination: Location;
      newly_discovered: boolean;
    }>(`/characters/${characterId}/travel`, playerId, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({ destination_id: destinationId }),
    }),
  encounters: (playerId: string, characterId: string) =>
    request<EncounterDefinition[]>(
      `/characters/${characterId}/encounters`,
      playerId,
    ),
  startCombat: (
    playerId: string,
    characterId: string,
    encounterDefinitionId: string,
    seed: number,
    idempotencyKey: string,
  ) =>
    request<CombatState>("/combat/start", playerId, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({
        character_id: characterId,
        encounter_definition_id: encounterDefinitionId,
        seed,
      }),
    }),
  combat: (playerId: string, combatId: string) =>
    request<CombatState>(`/combat/${combatId}`, playerId),
  combatAction: (
    playerId: string,
    combatId: string,
    actionType: CombatActionType,
    idempotencyKey: string,
    skillId?: string,
    inventoryItemId?: string,
  ) =>
    request<CombatState>("/combat/action", playerId, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({
        combat_id: combatId,
        action_type: actionType,
        skill_id: skillId,
        inventory_item_id: inventoryItemId,
      }),
    }),
  fleeCombat: (playerId: string, combatId: string, idempotencyKey: string) =>
    request<CombatState>("/combat/flee", playerId, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({ combat_id: combatId }),
    }),
  quests: (playerId: string, characterId: string) =>
    request<Quest[]>(`/characters/${characterId}/quests`, playerId),
  questMutation: (
    playerId: string,
    characterId: string,
    questId: string,
    action: "accept" | "submit" | "fail" | "archive",
    idempotencyKey: string,
  ) =>
    request<Quest>(`/quests/${questId}/${action}`, playerId, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({ character_id: characterId }),
    }),
  npcs: (playerId: string, characterId: string) =>
    request<Npc[]>(`/characters/${characterId}/npcs`, playerId),
  interact: (
    playerId: string,
    characterId: string,
    npcId: string,
    actionId: "GREET" | "OFFER_HELP",
    idempotencyKey: string,
  ) =>
    request<NpcInteraction>(`/npcs/${npcId}/interact`, playerId, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({ character_id: characterId, action_id: actionId }),
    }),
  factions: (playerId: string, characterId: string) =>
    request<Faction[]>(`/characters/${characterId}/factions`, playerId),
  joinFaction: (
    playerId: string,
    characterId: string,
    factionId: string,
    idempotencyKey: string,
  ) =>
    request<Faction>(`/factions/${factionId}/join`, playerId, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({ character_id: characterId }),
    }),
  dungeons: (playerId: string, characterId: string) =>
    request<Dungeon[]>(`/characters/${characterId}/dungeons`, playerId),
  dungeonMutation: (
    playerId: string,
    characterId: string,
    dungeonId: string,
    action: "enter" | "clear",
    idempotencyKey: string,
  ) =>
    request<Dungeon>(`/dungeons/${dungeonId}/${action}`, playerId, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({ character_id: characterId }),
    }),
  journal: (playerId: string, characterId: string) =>
    request<JournalEntry[]>(`/characters/${characterId}/journal`, playerId),
  dialogue: (
    playerId: string,
    characterId: string,
    npcId: string,
    topicId: DialogueTopic,
    idempotencyKey: string,
  ) =>
    request<Narrative>(`/npcs/${npcId}/dialogue`, playerId, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({
        character_id: characterId,
        topic_id: topicId,
      }),
    }),
  questFraming: (
    playerId: string,
    characterId: string,
    questId: string,
    idempotencyKey: string,
  ) =>
    request<Narrative>(`/quests/${questId}/framing`, playerId, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({ character_id: characterId }),
    }),
  lore: (
    playerId: string,
    characterId: string,
    entityId: string,
    entityType: "quest" | "location",
    idempotencyKey: string,
  ) =>
    request<Narrative>("/narrative/lore", playerId, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({
        character_id: characterId,
        entity_id: entityId,
        entity_type: entityType,
      }),
    }),
  locationDescription: (
    playerId: string,
    characterId: string,
    locationId: string,
    idempotencyKey: string,
  ) =>
    request<Narrative>(`/locations/${locationId}/description`, playerId, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({ character_id: characterId }),
    }),
  createSave: (playerId: string, characterId: string, idempotencyKey: string) =>
    request<{
      save_id: string;
      character_id: string;
      save_name: string;
    }>("/save", playerId, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({
        character_id: characterId,
        save_name: "Manual Save",
      }),
    }),
  deleteSave: (playerId: string, saveId: string, idempotencyKey: string) =>
    request<unknown>(`/save/${saveId}`, playerId, {
      method: "DELETE",
      headers: { "Idempotency-Key": idempotencyKey },
    }),
};
