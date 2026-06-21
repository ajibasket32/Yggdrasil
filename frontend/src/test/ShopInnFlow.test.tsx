import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import App from "../App";
import { gameApi } from "../services/gameApi";
import { sheet, inventory, npc, narrative } from "./fixtures";

vi.mock("../services/gameApi");
vi.mock("../components/GameCanvas");

describe("Shop and Inn Flow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (gameApi.definitions as any).mockResolvedValue({
      races: [],
      starting_jobs: [],
      starting_location: {},
    });
    (gameApi.characters as any).mockResolvedValue([sheet]);
    (gameApi.character as any).mockResolvedValue({ ...sheet, gold: 1000 });
    (gameApi.inventory as any).mockResolvedValue(inventory);
    (gameApi.equipment as any).mockResolvedValue({
      slots: [],
      total_equipment_bonuses: {},
    });
    (gameApi.locations as any).mockResolvedValue([]);
    (gameApi.encounters as any).mockResolvedValue([]);
    (gameApi.quests as any).mockResolvedValue([]);
    (gameApi.factions as any).mockResolvedValue([]);
    (gameApi.dungeons as any).mockResolvedValue([]);
    (gameApi.journal as any).mockResolvedValue([]);

    const hagar = {
      ...npc,
      id: "hagar-1",
      name: "Blacksmith Hagar",
      occupation: "Royal Blacksmith",
      role: "QUEST_GIVER",
      available_actions: ["GREET", "OFFER_HELP", "SHOP"],
      shop_id: "shop-1",
    };
    const innkeeper = {
      ...npc,
      id: "innkeeper-1",
      name: "Innkeeper Elena",
      role: "INNKEEPER",
      available_actions: ["GREET", "OFFER_HELP", "REST"],
    };
    (gameApi.npcs as any).mockResolvedValue([hagar, innkeeper]);
    (gameApi.dialogue as any).mockResolvedValue(narrative);
  });

  it("opens shop and completes a purchase", async () => {
    const mockShop = {
      id: "shop-1",
      name: "Hagar's Forge",
      description: "Test shop",
      owner_npc_id: "hagar-1",
      items: [
        {
          item_id: "item-1",
          name: "Steel Sword",
          price: 100,
          rarity: "COMMON",
          item_type: "WEAPON",
          description: "A sword",
        },
      ],
    };
    (gameApi.shop as any).mockResolvedValue(mockShop);
    (gameApi.purchase as any).mockResolvedValue({ gold_remaining: 900 });

    render(<App />);

    // Continue game
    fireEvent.click(await screen.findByText(/Continue:/));

    fireEvent.click(
      await screen.findByRole("button", {
        name: "Canvas NPC Marker: Blacksmith Hagar",
      }),
    );

    // Open Shop
    fireEvent.click(await screen.findByText("Browse Shop"));

    expect(await screen.findByText("Hagar's Forge")).toBeDefined();

    // Buy item
    fireEvent.click(await screen.findByRole("button", { name: "Buy" }));

    expect(await screen.findByText(/Purchased Steel Sword/)).toBeDefined();

    // Close shop
    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    expect(screen.queryByText("Hagar's Forge")).toBeNull();
  });

  it("performs an inn rest", async () => {
    (gameApi.rest as any).mockResolvedValue({
      hp_restored: 50,
      mp_restored: 20,
    });

    render(<App />);

    fireEvent.click(await screen.findByText(/Continue:/));
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Canvas NPC Marker: Innkeeper Elena",
      }),
    );

    // Rest
    fireEvent.click(await screen.findByText("Rest (50g)"));

    expect(
      await screen.findByText(/Rested at the Inn. Restored 50 HP and 20 MP/),
    ).toBeDefined();
  });

  it("keeps inn rest unavailable when the character cannot afford it", async () => {
    (gameApi.character as any).mockResolvedValue({ ...sheet, gold: 25 });

    render(<App />);

    fireEvent.click(await screen.findByText(/Continue:/));
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Canvas NPC Marker: Innkeeper Elena",
      }),
    );

    const restButton = await screen.findByRole("button", {
      name: "Rest (Needs 50g)",
    });
    expect(restButton).toBeDisabled();
    fireEvent.click(restButton);

    expect(gameApi.rest).not.toHaveBeenCalled();
  });

  it("reports inn rest errors without hiding the world", async () => {
    (gameApi.rest as any).mockRejectedValue(new Error("The rooms are full"));

    render(<App />);

    fireEvent.click(await screen.findByText(/Continue:/));
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Canvas NPC Marker: Innkeeper Elena",
      }),
    );
    fireEvent.click(await screen.findByText("Rest (50g)"));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The rooms are full",
    );
    expect(await screen.findByText("Aster Vale")).toBeInTheDocument();
  });

  it("handles shop api errors", async () => {
    (gameApi.shop as any).mockRejectedValue(
      new Error("Shop closed for inventory"),
    );

    render(<App />);

    fireEvent.click(await screen.findByText(/Continue:/));
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Canvas NPC Marker: Blacksmith Hagar",
      }),
    );
    fireEvent.click(await screen.findByText("Browse Shop"));

    expect(await screen.findByText("Shop closed for inventory")).toBeDefined();
  });

  it("handles purchase api errors", async () => {
    const mockShop = {
      id: "shop-1",
      name: "Hagar's Forge",
      description: "Test shop",
      owner_npc_id: "hagar-1",
      items: [
        {
          item_id: "item-1",
          name: "Steel Sword",
          price: 100,
          rarity: "COMMON",
          item_type: "WEAPON",
          description: "A sword",
        },
      ],
    };
    (gameApi.shop as any).mockResolvedValue(mockShop);
    (gameApi.purchase as any).mockRejectedValue(
      new Error("Insufficient funds in bank"),
    );

    render(<App />);

    fireEvent.click(await screen.findByText(/Continue:/));
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Canvas NPC Marker: Blacksmith Hagar",
      }),
    );
    fireEvent.click(await screen.findByText("Browse Shop"));

    // Wait for shop to appear
    await screen.findByText("Hagar's Forge");

    fireEvent.click(screen.getByRole("button", { name: "Buy" }));

    expect(
      await screen.findByText("⚠ Insufficient funds in bank"),
    ).toBeDefined();
  });

  it("scopes map interaction services to the active NPC", async () => {
    render(<App />);

    fireEvent.click(await screen.findByText(/Continue:/));
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Canvas NPC Marker: Blacksmith Hagar",
      }),
    );

    expect(await screen.findByText("Blacksmith Hagar")).toBeInTheDocument();
    expect(screen.queryByText(/Rest \(/)).toBeNull();
    expect(screen.getByText("Browse Shop")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "×" }));
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Canvas NPC Marker: Innkeeper Elena",
      }),
    );

    expect(await screen.findByText("Innkeeper Elena")).toBeInTheDocument();
    expect(screen.getByText("Rest (50g)")).toBeInTheDocument();
    expect(screen.queryByText("Browse Shop")).toBeNull();
  });
});
