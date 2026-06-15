import { fireEvent, render, screen } from "@testing-library/react";

import type { CombatState, Inventory, Skill } from "../types/gameplay";
import CombatPanel from "./CombatPanel";

const state: CombatState = {
  combat_id: "combat-1",
  encounter_name: "Trial Encounter",
  seed: 11,
  status: "ACTIVE",
  round_number: 1,
  action_sequence: 0,
  turn_order: ["player", "enemy"],
  participants: [
    {
      id: "player",
      source_id: "character",
      name: "Aster",
      side: "PLAYER",
      level: 1,
      current_hp: 40,
      max_hp: 100,
      current_mp: 2,
      max_mp: 20,
      current_stamina: 20,
      max_stamina: 20,
      guarding: false,
      defeated: false,
      statuses: [{ code: "BURN", duration: 2, potency: 3 }],
    },
    {
      id: "enemy",
      source_id: "monster",
      name: "Slime",
      side: "ENEMY",
      level: 1,
      current_hp: 30,
      max_hp: 50,
      current_mp: 0,
      max_mp: 0,
      current_stamina: 10,
      max_stamina: 10,
      guarding: false,
      defeated: false,
      statuses: [],
    },
  ],
  rewards: { experience: 0, gold: 0, items: [] },
  recent_log: [],
};

const skill: Skill = {
  id: "skill-1",
  name: "Ember",
  description: "A flame.",
  skill_type: "ACTIVE",
  skill_level: 1,
  mana_cost: 5,
  cooldown: 0,
  target_type: "ENEMY",
  effect_definitions: [{ effect: "fire", magnitude: 1 }],
};

const emptyInventory: Inventory = {
  slot_count: 30,
  used_slots: 0,
  total_weight: 0,
  max_weight: 100,
  items: [],
};

it("renders incomplete canonical state without action controls", () => {
  render(
    <CombatPanel
      combat={{ ...state, participants: [] }}
      skills={[]}
      inventory={null}
      busy={false}
      onAction={vi.fn()}
      onFlee={vi.fn()}
      onReturn={vi.fn()}
    />,
  );

  expect(screen.getByText("Combat state is incomplete.")).toBeInTheDocument();
  expect(screen.queryByRole("button")).not.toBeInTheDocument();
});

it("renders statuses and routes each available engine action", () => {
  const onAction = vi.fn();
  const onFlee = vi.fn();
  render(
    <CombatPanel
      combat={state}
      skills={[
        skill,
        { ...skill, id: "passive", name: "Focus", skill_type: "PASSIVE" },
      ]}
      inventory={emptyInventory}
      busy={false}
      onAction={onAction}
      onFlee={onFlee}
      onReturn={vi.fn()}
    />,
  );

  expect(screen.getByText("BURN (2)")).toBeInTheDocument();

  const emberBtn = screen.getByRole("button", { name: (content, element) => element.textContent?.includes("Ember") ?? false });
  expect(emberBtn).toBeDisabled();
  expect(
    screen.queryByRole("button", { name: /Focus/ }),
  ).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Attack" }));
  fireEvent.click(screen.getByRole("button", { name: "Guard" }));
  fireEvent.click(screen.getByRole("button", { name: "Wait" }));
  fireEvent.click(screen.getByRole("button", { name: "Flee" }));

  expect(onAction).toHaveBeenNthCalledWith(1, "ATTACK");
  expect(onAction).toHaveBeenNthCalledWith(2, "GUARD");
  expect(onAction).toHaveBeenNthCalledWith(3, "WAIT");
  expect(onFlee).toHaveBeenCalledOnce();
});

it("renders fled and loot-free victory outcomes", () => {
  const onReturn = vi.fn();
  const { rerender } = render(
    <CombatPanel
      combat={{ ...state, status: "FLED" }}
      skills={[]}
      inventory={emptyInventory}
      busy={false}
      onAction={vi.fn()}
      onFlee={vi.fn()}
      onReturn={onReturn}
    />,
  );
  expect(
    screen.getByText("Escaped!"),
  ).toBeInTheDocument();

  rerender(
    <CombatPanel
      combat={{
        ...state,
        status: "VICTORY",
        rewards: { experience: 10, gold: 4, items: [] },
      }}
      skills={[]}
      inventory={emptyInventory}
      busy={false}
      onAction={vi.fn()}
      onFlee={vi.fn()}
      onReturn={onReturn}
    />,
  );
  expect(screen.getByText(/Victory! \+10 XP, \+4 Gold/)).toBeInTheDocument();

  rerender(
    <CombatPanel
      combat={{
        ...state,
        status: "VICTORY",
        rewards: { experience: 10, gold: 4, items: ["Iron Sword"] },
      }}
      skills={[]}
      inventory={emptyInventory}
      busy={false}
      onAction={vi.fn()}
      onFlee={vi.fn()}
      onReturn={onReturn}
    />,
  );
  expect(screen.getByText(/Loot: Iron Sword/)).toBeInTheDocument();

  rerender(
    <CombatPanel
      combat={{ ...state, status: "DEFEAT" }}
      skills={[]}
      inventory={emptyInventory}
      busy={false}
      onAction={vi.fn()}
      onFlee={vi.fn()}
      onReturn={onReturn}
    />,
  );
  expect(
    screen.getByText(
      /Defeated/i,
    ),
  ).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /Continue/i }));
  expect(onReturn).toHaveBeenCalledOnce();
});

it("renders without potion in inventory", () => {
  render(
    <CombatPanel
      combat={state}
      skills={[]}
      inventory={emptyInventory}
      busy={false}
      onAction={vi.fn()}
      onFlee={vi.fn()}
      onReturn={vi.fn()}
    />,
  );
  expect(screen.queryByText(/Potion/)).not.toBeInTheDocument();
});
