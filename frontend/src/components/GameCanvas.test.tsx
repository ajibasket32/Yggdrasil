import { render } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import GameCanvas from "./GameCanvas";

describe("GameCanvas", () => {
  it("initializes Phaser Game", () => {
    const { container } = render(<GameCanvas mode="EXPLORATION" />);
    expect(container.querySelector(".game-canvas-container")).toBeInTheDocument();
  });

  it("switches between exploration and combat modes", () => {
    const { rerender } = render(<GameCanvas mode="EXPLORATION" />);
    rerender(<GameCanvas mode="COMBAT" />);
  });
});
