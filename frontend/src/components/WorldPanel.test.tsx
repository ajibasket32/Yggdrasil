import { fireEvent, render, screen } from "@testing-library/react";

import WorldPanel from "./WorldPanel";

const quest = {
  id: "quest-1",
  title: "The Rootbound Watch",
  description: "Secure the frontier.",
  minimum_level: 1,
  status: "ACTIVE" as const,
  objectives_complete: true,
  rewards_claimed: false,
  current_step: 2,
  steps: [
    {
      id: "step-1",
      sequence: 0,
      objective_type: "NPC_HELP",
      target_id: "npc-1",
      description: "Offer aid.",
      required_count: 1,
      progress: 1,
      complete: true,
    },
  ],
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
  available_actions: ["GREET", "OFFER_HELP"] as ("GREET" | "OFFER_HELP")[],
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
  entered: true,
  cleared: false,
  boss_alive: true,
};

it("offers deterministic quest, NPC, faction, and dungeon actions", () => {
  const onQuestAction = vi.fn();
  const onNpcAction = vi.fn();
  const onDialogue = vi.fn();
  const onQuestFraming = vi.fn();
  const onJoinFaction = vi.fn();
  const onDungeonAction = vi.fn();
  render(
    <WorldPanel
      quests={[quest]}
      npcs={[npc]}
      factions={[faction]}
      dungeons={[dungeon]}
      journal={[]}
      busy={false}
      interactionText="Aid recorded."
      narrative={null}
      onQuestAction={onQuestAction}
      onNpcAction={onNpcAction}
      onDialogue={onDialogue}
      onQuestFraming={onQuestFraming}
      onCloseNarrative={vi.fn()}
      onJoinFaction={onJoinFaction}
      onDungeonAction={onDungeonAction}
    />,
  );

  fireEvent.click(screen.getByRole("button", { name: "Claim rewards" }));
  fireEvent.click(screen.getByRole("button", { name: "Offer help" }));
  fireEvent.click(screen.getByRole("button", { name: "Join faction" }));
  fireEvent.click(screen.getByRole("button", { name: "Secure dungeon" }));
  fireEvent.click(screen.getByRole("button", { name: "Hear story" }));
  fireEvent.click(screen.getByRole("button", { name: "Speak" }));
  fireEvent.click(screen.getByRole("button", { name: "Ask about quest" }));
  fireEvent.click(screen.getByRole("button", { name: "Ask local news" }));

  expect(onQuestAction).toHaveBeenCalledWith(quest, "submit");
  expect(onNpcAction).toHaveBeenCalledWith(npc, "OFFER_HELP");
  expect(onJoinFaction).toHaveBeenCalledWith(faction);
  expect(onDungeonAction).toHaveBeenCalledWith(dungeon, "clear");
  expect(onQuestFraming).toHaveBeenCalledWith(quest);
  expect(onDialogue).toHaveBeenNthCalledWith(1, npc, "GREETING");
  expect(onDialogue).toHaveBeenNthCalledWith(2, npc, "QUEST");
  expect(onDialogue).toHaveBeenNthCalledWith(3, npc, "LOCAL_NEWS");
  expect(screen.getByRole("status")).toHaveTextContent("Aid recorded.");
});

it("renders empty and permanent-state summaries", () => {
  render(
    <WorldPanel
      quests={[]}
      npcs={[]}
      factions={[{ ...faction, joined: true, rank: "INITIATE" }]}
      dungeons={[
        { ...dungeon, entered: true, cleared: true, boss_alive: false },
      ]}
      journal={[]}
      busy={false}
      interactionText={null}
      narrative={null}
      onQuestAction={vi.fn()}
      onNpcAction={vi.fn()}
      onDialogue={vi.fn()}
      onQuestFraming={vi.fn()}
      onCloseNarrative={vi.fn()}
      onJoinFaction={vi.fn()}
      onDungeonAction={vi.fn()}
    />,
  );

  expect(
    screen.getByText("No active or available quests. Explore to find more!"),
  ).toBeInTheDocument();
  expect(screen.getByText("No NPCs are present.")).toBeInTheDocument();
  expect(screen.getByText("Permanently cleared")).toBeInTheDocument();
  expect(
    screen.queryByRole("button", { name: "Join faction" }),
  ).not.toBeInTheDocument();
});

it("covers accept, abandon, archive, journal, and unopened dungeon states", () => {
  const onQuestAction = vi.fn();
  const onDungeonAction = vi.fn();
  render(
    <WorldPanel
      quests={[
        { ...quest, id: "available", status: "NOT_STARTED" },
        {
          ...quest,
          id: "active",
          status: "ACTIVE",
          objectives_complete: false,
          steps: quest.steps.map((step) => ({
            ...step,
            progress: 0,
            complete: false,
          })),
        },
        { ...quest, id: "failed", status: "FAILED" },
      ]}
      npcs={[]}
      factions={[]}
      dungeons={[{ ...dungeon, entered: false }]}
      journal={[
        {
          id: "journal-1",
          category: "QUEST_ACCEPTED",
          title: quest.title,
          body: "Quest accepted.",
          quest_id: quest.id,
          created_at: "2026-06-14T00:00:00Z",
        },
      ]}
      busy={false}
      interactionText={null}
      narrative={null}
      onQuestAction={onQuestAction}
      onNpcAction={vi.fn()}
      onDialogue={vi.fn()}
      onQuestFraming={vi.fn()}
      onCloseNarrative={vi.fn()}
      onJoinFaction={vi.fn()}
      onDungeonAction={onDungeonAction}
    />,
  );

  fireEvent.click(screen.getByRole("button", { name: "Accept quest" }));
  fireEvent.click(screen.getByRole("button", { name: "Abandon quest" }));
  fireEvent.click(screen.getByRole("button", { name: "Archive" }));
  fireEvent.click(screen.getByRole("button", { name: "Enter dungeon" }));

  expect(onQuestAction).toHaveBeenCalledTimes(3);
  expect(onDungeonAction).toHaveBeenCalledWith(
    expect.objectContaining({ id: dungeon.id }),
    "enter",
  );
  expect(screen.getByText(/Quest accepted/)).toBeInTheDocument();
});

it("renders completed quest state", () => {
  render(
    <WorldPanel
      quests={[
        { ...quest, status: "COMPLETED" as const, objectives_complete: true },
      ]}
      npcs={[]}
      factions={[]}
      dungeons={[]}
      journal={[]}
      busy={false}
      interactionText={null}
      narrative={null}
      onQuestAction={vi.fn()}
      onNpcAction={vi.fn()}
      onDialogue={vi.fn()}
      onQuestFraming={vi.fn()}
      onCloseNarrative={vi.fn()}
      onJoinFaction={vi.fn()}
      onDungeonAction={vi.fn()}
    />,
  );

  expect(screen.getByText("COMPLETED")).toBeInTheDocument();
  expect(screen.getByText("Archive")).toBeInTheDocument();
  expect(screen.getByText("☑")).toBeInTheDocument();
});

it("renders failed quest state", () => {
  render(
    <WorldPanel
      quests={[{ ...quest, status: "FAILED" as const }]}
      npcs={[]}
      factions={[]}
      dungeons={[]}
      journal={[]}
      busy={false}
      interactionText={null}
      narrative={null}
      onQuestAction={vi.fn()}
      onNpcAction={vi.fn()}
      onDialogue={vi.fn()}
      onQuestFraming={vi.fn()}
      onCloseNarrative={vi.fn()}
      onJoinFaction={vi.fn()}
      onDungeonAction={vi.fn()}
    />,
  );

  expect(screen.getByText("FAILED")).toBeInTheDocument();
  expect(screen.getByText("Archive")).toBeInTheDocument();
});

it("handles busy state on buttons", () => {
  render(
    <WorldPanel
      quests={[quest]}
      npcs={[]}
      factions={[]}
      dungeons={[]}
      journal={[]}
      busy={true}
      interactionText={null}
      narrative={null}
      onQuestAction={vi.fn()}
      onNpcAction={vi.fn()}
      onDialogue={vi.fn()}
      onQuestFraming={vi.fn()}
      onCloseNarrative={vi.fn()}
      onJoinFaction={vi.fn()}
      onDungeonAction={vi.fn()}
    />,
  );

  expect(screen.getByRole("button", { name: "Hear story" })).toBeDisabled();
});
