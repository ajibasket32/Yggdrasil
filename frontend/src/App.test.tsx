import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import App from "./App";

const race = {
  id: "race-1",
  name: "Human",
  description: "Adaptable",
  category: "Humanoid",
};

const job = {
  id: "job-1",
  name: "Fighter",
  description: "Front-line combatant",
  tier: "Basic",
};

const locations = [
  {
    id: "location-1",
    name: "Frontier Gate",
    location_type: "TOWN",
    description: "A guarded settlement.",
    danger_level: 0,
    discovered: true,
    reachable: false,
  },
  {
    id: "location-2",
    name: "Whispering Road",
    location_type: "ROAD",
    description: "A road beneath old trees.",
    danger_level: 1,
    discovered: false,
    reachable: true,
  },
];

const sheet = {
  id: "character-1",
  name: "Aster Vale",
  race,
  level: 1,
  current_job: job,
  current_location: locations[0],
  gender: "Unspecified",
  alignment: "NEUTRAL",
  experience: 0,
  experience_to_next: 100,
  skill_points: 0,
  stats: {
    strength: 12,
    dexterity: 10,
    agility: 10,
    vitality: 12,
    intelligence: 8,
    wisdom: 9,
    charisma: 8,
  },
  derived_stats: {
    max_hp: 120,
    max_mp: 40,
    max_stamina: 80,
    physical_attack: 24,
    physical_defense: 18,
    magic_attack: 12,
    magic_defense: 14,
    accuracy: 80,
    evasion: 5,
    critical_chance: 0.05,
    initiative: 10,
  },
  current_hp: 120,
  current_mp: 40,
  current_stamina: 80,
  gold: 0,
  fame: 0,
  karma: 0,
  jobs: [
    {
      job,
      job_level: 1,
      experience: 0,
      experience_to_next: 100,
      active: true,
    },
  ],
  skills: [
    {
      id: "skill-1",
      name: "Power Strike",
      description: "A precise blow.",
      skill_type: "ACTIVE",
      skill_level: 1,
      mana_cost: 3,
      cooldown: 0,
      target_type: "ENEMY",
      effect_definitions: [{ effect: "physical", magnitude: 1 }],
    },
  ],
};

const inventory = {
  slot_count: 30,
  used_slots: 2,
  total_weight: 4,
  max_weight: 100,
  items: [
    {
      inventory_item_id: "item-1",
      name: "Field Potion",
      item_type: "CONSUMABLE",
      rarity: "COMMON",
      quantity: 5,
      is_quest_item: false,
      is_equipped: false,
    },
  ],
};

const equipment = {
  slots: [
    {
      slot_id: "slot-1",
      code: "main_hand",
      name: "Main Hand",
      item: null,
    },
  ],
  total_equipment_bonuses: {},
};

const definitions = {
  races: [race],
  starting_jobs: [job],
  starting_location: locations[0],
};

const encounter = {
  id: "encounter-1",
  name: "Slime on the Verge",
  monster_name: "Greenwood Slime",
  monster_level: 1,
  difficulty: "NORMAL",
  location_id: "location-1",
  reward_experience: 45,
  reward_gold: 18,
};

const quest = {
  id: "quest-1",
  title: "The Rootbound Watch",
  description: "Secure the frontier.",
  minimum_level: 1,
  status: "NOT_STARTED",
  objectives_complete: false,
  rewards_claimed: false,
  current_step: 0,
  steps: [],
  rewards: { experience: 120, gold: 45, reputation: 20 },
};

const npc = {
  id: "npc-1",
  name: "Warden Elian",
  occupation: "Frontier Warden",
  role: "QUEST_GIVER",
  faction_id: "faction-1",
  current_location_id: "location-1",
  personality_profile: {},
  knowledge: {},
  is_alive: true,
  available_actions: ["GREET", "OFFER_HELP"],
};

const faction = {
  id: "faction-1",
  name: "Frontier Wardens",
  description: "Protectors of the roads.",
  reputation: 0,
  rank: "OUTSIDER",
  joined: false,
};

const dungeon = {
  id: "dungeon-1",
  name: "Rootbound Hollow",
  description: "An old sealed hollow.",
  location_id: "location-1",
  recommended_level: 1,
  entered: false,
  cleared: false,
  boss_alive: true,
};

const narrative = {
  speaker_name: "Warden Elian",
  text: "The roots remember who keeps watch.",
  tone: "wary",
  tags: ["greeting"],
  fallback_used: false,
  cached: false,
  prompt_version: "npc-dialogue-v1",
  context_memory_count: 1,
  available_topics: ["GREETING", "QUEST", "LOCAL_NEWS", "FAREWELL"],
};

const combatState = (status: "ACTIVE" | "VICTORY" | "DEFEAT") => ({
  combat_id: "combat-1",
  encounter_name: encounter.name,
  seed: 17,
  status,
  round_number: 2,
  action_sequence: 3,
  turn_order: ["participant-player", "participant-enemy"],
  participants: [
    {
      id: "participant-player",
      source_id: sheet.id,
      name: sheet.name,
      side: "PLAYER",
      level: 1,
      current_hp: status === "DEFEAT" ? 0 : 92,
      max_hp: 120,
      current_mp: 40,
      max_mp: 40,
      current_stamina: 80,
      max_stamina: 80,
      guarding: false,
      defeated: status === "DEFEAT",
      statuses: [],
    },
    {
      id: "participant-enemy",
      source_id: "monster-1",
      name: encounter.monster_name,
      side: "ENEMY",
      level: 1,
      current_hp: status === "VICTORY" ? 0 : 32,
      max_hp: 55,
      current_mp: 0,
      max_mp: 0,
      current_stamina: 40,
      max_stamina: 40,
      guarding: false,
      defeated: status === "VICTORY",
      statuses: [],
    },
  ],
  rewards:
    status === "VICTORY"
      ? { experience: 45, gold: 18, items: ["Field Potion"] }
      : { experience: 0, gold: 0, items: [] },
  recent_log: [
    {
      id: `log-${status}`,
      sequence: 0,
      round_number: 1,
      action_type: status,
      outcome: {},
      text:
        status === "VICTORY"
          ? "Victory. Gained 45 XP and 18 gold."
          : status === "DEFEAT"
            ? "Aster Vale is defeated."
            : "Combat begins.",
      created_at: "2026-06-14T00:00:00Z",
    },
  ],
});

const response = (data: unknown, ok = true) =>
  Promise.resolve({
    ok,
    json: () =>
      Promise.resolve(
        ok ? { success: true, data } : { error: { message: String(data) } },
      ),
  } as Response);

const installFetch = (
  hasCharacter: boolean,
  travelSucceeds = true,
  combatOutcome: "VICTORY" | "DEFEAT" = "VICTORY",
  options: {
    encountersAvailable?: boolean;
    restoreSucceeds?: boolean;
    startSucceeds?: boolean;
    actionSucceeds?: boolean;
    fleeSucceeds?: boolean;
    worldAvailable?: boolean;
    questSucceeds?: boolean;
    npcSucceeds?: boolean;
    narrativeSucceeds?: boolean;
    framingSucceeds?: boolean;
    descriptionSucceeds?: boolean;
    factionSucceeds?: boolean;
    dungeonSucceeds?: boolean;
  } = {},
) => {
  const calls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url =
        typeof input === "string"
          ? input
          : input instanceof URL
            ? input.href
            : input.url;
      calls.push(`${init?.method ?? "GET"} ${url}`);
      if (url.endsWith("/character-definitions")) return response(definitions);
      if (url.endsWith("/characters") && init?.method === "POST") {
        return response(sheet);
      }
      if (url.endsWith("/characters")) {
        return response(hasCharacter ? [sheet] : []);
      }
      if (url.endsWith("/inventory")) return response(inventory);
      if (url.endsWith("/equipment")) return response(equipment);
      if (url.endsWith("/locations")) return response(locations);
      if (url.endsWith("/encounters")) {
        return response(
          options.encountersAvailable === false ? [] : [encounter],
        );
      }
      if (url.endsWith("/quests")) {
        return response(options.worldAvailable ? [quest] : []);
      }
      if (url.endsWith("/npcs")) {
        return response(options.worldAvailable ? [npc] : []);
      }
      if (url.endsWith("/factions")) {
        return response(options.worldAvailable ? [faction] : []);
      }
      if (url.endsWith("/dungeons")) {
        return response(options.worldAvailable ? [dungeon] : []);
      }
      if (url.endsWith("/journal")) return response([]);
      if (url.endsWith("/quests/quest-1/accept")) {
        return options.questSucceeds === false
          ? response("Quest unavailable", false)
          : response({ ...quest, status: "ACTIVE" });
      }
      if (url.endsWith("/npcs/npc-1/interact")) {
        return options.npcSucceeds === false
          ? response("NPC unavailable", false)
          : response({
              npc,
              action_id: "OFFER_HELP",
              result_text: "Aid recorded.",
              quest_progressed: true,
              relationship: {
                npc_id: npc.id,
                character_id: sheet.id,
                trust: 5,
                friendship: 2,
                respect: 3,
                fear: 0,
                hatred: 0,
                loyalty: 0,
              },
            });
      }
      if (url.endsWith("/npcs/npc-1/dialogue")) {
        return options.narrativeSucceeds === false
          ? response("Dialogue unavailable", false)
          : response(narrative);
      }
      if (url.endsWith("/quests/quest-1/framing")) {
        return options.framingSucceeds === false
          ? response("Story unavailable", false)
          : response({
              ...narrative,
              speaker_name: null,
              text: "A watch must be kept beneath the old boughs.",
              prompt_version: "quest-framing-v1",
              available_topics: [],
            });
      }
      if (url.endsWith("/locations/location-1/description")) {
        return options.descriptionSucceeds === false
          ? response("Description unavailable", false)
          : response({
              ...narrative,
              speaker_name: null,
              text: "Lanterns hold back the green dusk.",
              prompt_version: "location-description-v1",
              available_topics: [],
            });
      }
      if (url.endsWith("/factions/faction-1/join")) {
        return options.factionSucceeds === false
          ? response("Faction unavailable", false)
          : response({ ...faction, joined: true, rank: "INITIATE" });
      }
      if (url.endsWith("/dungeons/dungeon-1/enter")) {
        return options.dungeonSucceeds === false
          ? response("Dungeon unavailable", false)
          : response({ ...dungeon, entered: true });
      }
      if (url.endsWith("/travel")) {
        return travelSucceeds
          ? response({ newly_discovered: true })
          : response("Route closed", false);
      }
      if (url.endsWith("/combat/start")) {
        return options.startSucceeds === false
          ? response("Encounter unavailable", false)
          : response(combatState("ACTIVE"));
      }
      if (url.endsWith("/combat/action")) {
        return options.actionSucceeds === false
          ? response("Action rejected", false)
          : response(combatState(combatOutcome));
      }
      if (url.endsWith("/combat/flee")) {
        return options.fleeSucceeds === false
          ? response("Escape blocked", false)
          : response({ ...combatState("ACTIVE"), status: "FLED" });
      }
      if (url.endsWith("/combat/combat-1")) {
        return options.restoreSucceeds === false
          ? response("Combat expired", false)
          : response(combatState("ACTIVE"));
      }
      if (url.endsWith("/characters/character-1")) return response(sheet);
      return response("Unknown route", false);
    }),
  );
  return calls;
};

beforeEach(() => {
  window.localStorage.clear();
  window.localStorage.setItem(
    "yggdrasil-player-id",
    "5f22ba23-eaac-44d4-a232-c27c98b8fbf0",
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("App", () => {
  it("creates and presents an authoritative character sheet", async () => {
    const calls = installFetch(false);
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "Create your character" }),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Character name"), {
      target: { value: "Aster Vale" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create character" }));

    expect(
      await screen.findByRole("heading", { name: "Aster Vale" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Power Strike")).toBeInTheDocument();
    expect(screen.getByText("Field Potion")).toBeInTheDocument();
    expect(calls).toContain("POST /api/v1/characters");
  });

  it("loads an existing character and follows only a valid route", async () => {
    const calls = installFetch(true);
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "Known world" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Travel here" }));

    await waitFor(() => {
      expect(calls).toContain("POST /api/v1/characters/character-1/travel");
    });
  });

  it("shows a stable load failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => response("Service unavailable", false)),
    );
    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Service unavailable",
    );
  });

  it("keeps creation available when the server rejects it", async () => {
    installFetch(false);
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockImplementationOnce(() => response(definitions));
    fetchMock.mockImplementationOnce(() => response([]));
    fetchMock.mockImplementationOnce(() => response("Name unavailable", false));
    render(<App />);

    await screen.findByRole("heading", { name: "Create your character" });
    fireEvent.change(screen.getByLabelText("Character name"), {
      target: { value: "Aster Vale" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create character" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Name unavailable",
    );
    expect(
      screen.getByRole("heading", { name: "Create your character" }),
    ).toBeInTheDocument();
  });

  it("reports a rejected route without losing the character sheet", async () => {
    installFetch(true, false);
    render(<App />);

    await screen.findByRole("heading", { name: "Aster Vale" });
    fireEvent.click(screen.getByRole("button", { name: "Travel here" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Route closed");
    expect(
      screen.getByRole("heading", { name: "Aster Vale" }),
    ).toBeInTheDocument();
  });

  it("completes and presents a canonical victory flow", async () => {
    installFetch(true);
    render(<App />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Begin combat" }),
    );
    expect(
      await screen.findByRole("heading", {
        name: "Slime on the Verge",
        level: 2,
      }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Attack" }));

    expect(await screen.findByText("VICTORY")).toBeInTheDocument();
    expect(screen.getAllByText(/Gained 45 XP and 18 gold/)).toHaveLength(2);
    expect(
      screen.getByRole("button", { name: "Return to archive" }),
    ).toBeInTheDocument();
  });

  it("presents engine-owned defeat without inventing rewards", async () => {
    installFetch(true, true, "DEFEAT");
    render(<App />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Begin combat" }),
    );
    fireEvent.click(await screen.findByRole("button", { name: "Attack" }));

    expect(await screen.findByText("DEFEAT")).toBeInTheDocument();
    expect(
      screen.getByText(
        "The party was defeated. The character returns with 1 HP.",
      ),
    ).toBeInTheDocument();
  });

  it("restores an active canonical encounter after refresh", async () => {
    installFetch(true);
    window.localStorage.setItem(
      "yggdrasil-active-combat:character-1",
      "combat-1",
    );
    render(<App />);

    expect(
      await screen.findByRole("heading", {
        name: "Slime on the Verge",
        level: 2,
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Attack" })).toBeInTheDocument();
  });

  it("discards a stale stored combat and keeps the archive usable", async () => {
    installFetch(true, true, "VICTORY", { restoreSucceeds: false });
    window.localStorage.setItem(
      "yggdrasil-active-combat:character-1",
      "combat-1",
    );
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: "Known world" }),
    ).toBeInTheDocument();
    expect(
      window.localStorage.getItem("yggdrasil-active-combat:character-1"),
    ).toBeNull();
  });

  it("shows a stable empty state where no encounters exist", async () => {
    installFetch(true, true, "VICTORY", { encountersAvailable: false });
    render(<App />);

    expect(
      await screen.findByText("No combat encounters at this location."),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Begin combat" }),
    ).not.toBeInTheDocument();
  });

  it("escapes combat and returns to a refreshed archive", async () => {
    installFetch(true);
    render(<App />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Begin combat" }),
    );
    fireEvent.click(await screen.findByRole("button", { name: "Escape" }));
    expect(
      await screen.findByText("The party escaped the encounter."),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Return to archive" }));

    expect(
      await screen.findByRole("heading", { name: "Known world" }),
    ).toBeInTheDocument();
  });

  it("reports a rejected combat action without losing the encounter", async () => {
    installFetch(true, true, "VICTORY", { actionSucceeds: false });
    render(<App />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Begin combat" }),
    );
    fireEvent.click(await screen.findByRole("button", { name: "Attack" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Action rejected",
    );
    expect(
      screen.getByRole("heading", { name: "Slime on the Verge", level: 2 }),
    ).toBeInTheDocument();
  });

  it("reports a rejected encounter start while preserving the archive", async () => {
    installFetch(true, true, "VICTORY", { startSucceeds: false });
    render(<App />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Begin combat" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Encounter unavailable",
    );
    expect(
      screen.getByRole("heading", { name: "Known world" }),
    ).toBeInTheDocument();
  });

  it("reports a failed escape and retains active combat", async () => {
    installFetch(true, true, "VICTORY", { fleeSucceeds: false });
    render(<App />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Begin combat" }),
    );
    fireEvent.click(await screen.findByRole("button", { name: "Escape" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Escape blocked",
    );
    expect(screen.getByRole("button", { name: "Attack" })).toBeInTheDocument();
  });

  it("runs deterministic quest, NPC, faction, and dungeon actions", async () => {
    const calls = installFetch(true, true, "VICTORY", {
      worldAvailable: true,
    });
    render(<App />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Accept quest" }),
    );
    await waitFor(() => {
      expect(calls).toContain("POST /api/v1/quests/quest-1/accept");
    });
    fireEvent.click(await screen.findByRole("button", { name: "Offer help" }));
    await waitFor(() => {
      expect(calls).toContain("POST /api/v1/npcs/npc-1/interact");
    });
    fireEvent.click(
      await screen.findByRole("button", { name: "Join faction" }),
    );
    await waitFor(() => {
      expect(calls).toContain("POST /api/v1/factions/faction-1/join");
    });
    fireEvent.click(
      await screen.findByRole("button", { name: "Enter dungeon" }),
    );
    await waitFor(() => {
      expect(calls).toContain("POST /api/v1/dungeons/dungeon-1/enter");
    });
    expect(screen.getByRole("status")).toHaveTextContent("Aid recorded.");
  });

  it("reports rejected quest and NPC actions without losing world controls", async () => {
    installFetch(true, true, "VICTORY", {
      worldAvailable: true,
      questSucceeds: false,
      npcSucceeds: false,
    });
    render(<App />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Accept quest" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Quest unavailable",
    );
    fireEvent.click(screen.getByRole("button", { name: "Offer help" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "NPC unavailable",
    );
    expect(
      screen.getByRole("button", { name: "Join faction" }),
    ).toBeInTheDocument();
  });

  it("presents bounded narrative choices without a chat input", async () => {
    const calls = installFetch(true, true, "VICTORY", {
      worldAvailable: true,
    });
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Speak" }));

    expect(await screen.findByText(narrative.text)).toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(calls).toContain("POST /api/v1/npcs/npc-1/dialogue");

    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(screen.queryByText(narrative.text)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Hear story" }));
    expect(
      await screen.findByText("A watch must be kept beneath the old boughs."),
    ).toBeInTheDocument();
  });

  it("describes the current location and reports narrative failures", async () => {
    const calls = installFetch(true, true, "VICTORY", {
      worldAvailable: true,
      narrativeSucceeds: false,
      framingSucceeds: false,
    });
    render(<App />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Observe surroundings" }),
    );
    expect(
      await screen.findByText("Lanterns hold back the green dusk."),
    ).toBeInTheDocument();
    expect(calls).toContain("POST /api/v1/locations/location-1/description");
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));

    fireEvent.click(screen.getByRole("button", { name: "Speak" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Dialogue unavailable",
    );

    fireEvent.click(screen.getByRole("button", { name: "Hear story" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Story unavailable",
    );
  });

  it("keeps world controls after description and world-action failures", async () => {
    installFetch(true, true, "VICTORY", {
      worldAvailable: true,
      descriptionSucceeds: false,
      factionSucceeds: false,
      dungeonSucceeds: false,
    });
    render(<App />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Observe surroundings" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Description unavailable",
    );

    fireEvent.click(screen.getByRole("button", { name: "Join faction" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Faction unavailable",
    );

    fireEvent.click(screen.getByRole("button", { name: "Enter dungeon" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Dungeon unavailable",
    );
  });
});
