import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import ShopOverlay from "./ShopOverlay";
import type { Shop } from "../types/gameplay";

const mockShop: Shop = {
  id: "shop-1",
  name: "Test Shop",
  description: "A shop for testing",
  owner_npc_id: "npc-1",
  items: [
    {
      item_id: "item-1",
      name: "Potion",
      description: "Heals you",
      price: 10,
      rarity: "COMMON",
      item_type: "CONSUMABLE",
    },
    {
      item_id: "item-2",
      name: "Sword",
      description: "Hits things",
      price: 100,
      rarity: "UNCOMMON",
      item_type: "WEAPON",
    },
  ],
};

describe("ShopOverlay", () => {
  it("renders shop details and items", () => {
    render(
      <ShopOverlay
        shop={mockShop}
        characterGold={50}
        busy={false}
        onPurchase={vi.fn()}
        onClose={vi.fn()}
      />,
    );

    expect(screen.getByText("Test Shop")).toBeDefined();
    expect(screen.getByText("A shop for testing")).toBeDefined();
    expect(screen.getByText("Potion")).toBeDefined();
    expect(screen.getByText("Sword")).toBeDefined();
    expect(screen.getByText("💰 10g")).toBeDefined();
    expect(screen.getByText("💰 100g")).toBeDefined();
  });

  it("calls onPurchase when buy button is clicked", () => {
    const onPurchase = vi.fn();
    render(
      <ShopOverlay
        shop={mockShop}
        characterGold={50}
        busy={false}
        onPurchase={onPurchase}
        onClose={vi.fn()}
      />,
    );

    const buyButtons = screen.getAllByRole("button", { name: "Buy" });
    fireEvent.click(buyButtons[0]!);

    expect(onPurchase).toHaveBeenCalledWith(mockShop.items[0]);
  });

  it("disables buy button if insufficient gold", () => {
    render(
      <ShopOverlay
        shop={mockShop}
        characterGold={5}
        busy={false}
        onPurchase={vi.fn()}
        onClose={vi.fn()}
      />,
    );

    const potionButtons = screen.getAllByRole("button", {
      name: "Insufficient Gold",
    });
    expect(potionButtons[0]).toBeDefined();
    expect((potionButtons[0] as HTMLButtonElement).disabled).toBe(true);
  });

  it("calls onClose when close button is clicked", () => {
    const onClose = vi.fn();
    render(
      <ShopOverlay
        shop={mockShop}
        characterGold={50}
        busy={false}
        onPurchase={vi.fn()}
        onClose={onClose}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    expect(onClose).toHaveBeenCalled();
  });

  it("renders success and error banners", () => {
    const { rerender } = render(
      <ShopOverlay
        shop={mockShop}
        characterGold={50}
        busy={false}
        onPurchase={vi.fn()}
        onClose={vi.fn()}
        lastPurchase="Potion"
      />,
    );
    expect(screen.getByText("✓ Purchased Potion!")).toBeDefined();

    rerender(
      <ShopOverlay
        shop={mockShop}
        characterGold={50}
        busy={false}
        onPurchase={vi.fn()}
        onClose={vi.fn()}
        error="Something went wrong"
      />,
    );
    expect(screen.getByText("⚠ Something went wrong")).toBeDefined();
  });
});
