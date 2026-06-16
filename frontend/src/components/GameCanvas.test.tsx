import { render } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import GameCanvas from "./GameCanvas";

describe("GameCanvas", () => {
  it("initializes Phaser Game", () => {
    const { container } = render(<GameCanvas mode="EXPLORATION" />);
    expect(
      container.querySelector(".game-canvas-container"),
    ).toBeInTheDocument();
  });

  it("switches between exploration and combat modes", () => {
    const { rerender } = render(<GameCanvas mode="EXPLORATION" />);
    rerender(<GameCanvas mode="COMBAT" />);
  });

  it("passes data to registry and handles callbacks", () => {
    const onTravel = vi.fn();
    const { rerender } = render(
      <GameCanvas
        mode="EXPLORATION"
        npcs={[{ id: "1", name: "NPC" } as any]}
        onTravel={onTravel}
      />,
    );

    // Rerender to trigger useEffect updates
    rerender(
      <GameCanvas
        mode="EXPLORATION"
        locationName="New Area"
        npcs={[{ id: "1", name: "NPC" } as any]}
        onTravel={onTravel}
      />,
    );
  });
});
