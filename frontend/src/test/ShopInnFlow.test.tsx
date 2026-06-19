import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import App from "../App";
import { gameApi } from "../services/gameApi";
import { sheet, inventory, npc } from "./fixtures";

vi.mock("../services/gameApi");
vi.mock("../components/GameCanvas");

describe("Shop and Inn Flow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (gameApi.definitions as any).mockResolvedValue({ races: [], starting_jobs: [], starting_location: {} });
    (gameApi.characters as any).mockResolvedValue([sheet]);
    (gameApi.character as any).mockResolvedValue({ ...sheet, gold: 1000 });
    (gameApi.inventory as any).mockResolvedValue(inventory);
    (gameApi.equipment as any).mockResolvedValue({ slots: [], total_equipment_bonuses: {} });
    (gameApi.locations as any).mockResolvedValue([]);
    (gameApi.encounters as any).mockResolvedValue([]);
    (gameApi.quests as any).mockResolvedValue([]);
    (gameApi.factions as any).mockResolvedValue([]);
    (gameApi.dungeons as any).mockResolvedValue([]);
    (gameApi.journal as any).mockResolvedValue([]);

    const merchant = {
        ...npc,
        id: "merchant-1",
        name: "Merchant Silas",
        role: "MERCHANT",
        available_actions: ["GREET", "OFFER_HELP", "SHOP"],
        shop_id: "shop-1"
    };
    const innkeeper = {
        ...npc,
        id: "innkeeper-1",
        name: "Innkeeper Elena",
        role: "INNKEEPER",
        available_actions: ["GREET", "OFFER_HELP", "REST"]
    };
    (gameApi.npcs as any).mockResolvedValue([merchant, innkeeper]);
  });

  it("opens shop and completes a purchase", async () => {
    const mockShop = {
      id: "shop-1",
      name: "Silas's Sundries",
      description: "Test shop",
      owner_npc_id: "merchant-1",
      items: [{ item_id: "item-1", name: "Steel Sword", price: 100, rarity: "COMMON", item_type: "WEAPON", description: "A sword" }]
    };
    (gameApi.shop as any).mockResolvedValue(mockShop);
    (gameApi.purchase as any).mockResolvedValue({ gold_remaining: 900 });

    render(<App />);

    // Continue game
    fireEvent.click(await screen.findByText(/Continue:/));

    // Open World Panel (Quests button in UI)
    fireEvent.click(await screen.findByText("Quests"));

    // Open Shop
    fireEvent.click(await screen.findByText("Browse Shop"));

    expect(await screen.findByText("Silas's Sundries")).toBeDefined();

    // Buy item
    fireEvent.click(await screen.findByRole("button", { name: "Buy" }));

    expect(await screen.findByText(/Purchased Steel Sword/)).toBeDefined();

    // Close shop
    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    expect(screen.queryByText("Silas's Sundries")).toBeNull();
  });

  it("performs an inn rest", async () => {
    (gameApi.rest as any).mockResolvedValue({ hp_restored: 50, mp_restored: 20 });

    render(<App />);

    fireEvent.click(await screen.findByText(/Continue:/));
    fireEvent.click(await screen.findByText("Quests"));

    // Rest
    fireEvent.click(await screen.findByText("Rest (50g)"));

    expect(await screen.findByText(/Rested at the Inn. Restored 50 HP and 20 MP/)).toBeDefined();
  });

  it("handles shop api errors", async () => {
    (gameApi.shop as any).mockRejectedValue(new Error("Shop closed for inventory"));

    render(<App />);

    fireEvent.click(await screen.findByText(/Continue:/));
    fireEvent.click(await screen.findByText("Quests"));
    fireEvent.click(await screen.findByText("Browse Shop"));

    expect(await screen.findByText("Shop closed for inventory")).toBeDefined();
  });

  it("handles purchase api errors", async () => {
    const mockShop = {
      id: "shop-1",
      name: "Silas's Sundries",
      description: "Test shop",
      owner_npc_id: "merchant-1",
      items: [{ item_id: "item-1", name: "Steel Sword", price: 100, rarity: "COMMON", item_type: "WEAPON", description: "A sword" }]
    };
    (gameApi.shop as any).mockResolvedValue(mockShop);
    (gameApi.purchase as any).mockRejectedValue(new Error("Insufficient funds in bank"));

    render(<App />);

    fireEvent.click(await screen.findByText(/Continue:/));
    fireEvent.click(await screen.findByText("Quests"));
    fireEvent.click(await screen.findByText("Browse Shop"));

    // Wait for shop to appear
    await screen.findByText("Silas's Sundries");

    fireEvent.click(screen.getByRole("button", { name: "Buy" }));

    expect(await screen.findByText("⚠ Insufficient funds in bank")).toBeDefined();
  });
});
