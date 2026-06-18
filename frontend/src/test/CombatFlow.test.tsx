import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import App from "../App";
import { installFetch, combatState } from "./fixtures";
import { continueExistingGame } from "./helpers";

describe("Combat Flow", () => {
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

  it("completes and presents a canonical victory flow", async () => {
    installFetch(true);
    render(<App />);

    await continueExistingGame("Aster Vale");
    fireEvent.click(screen.getByRole("button", { name: "Encounters" }));
    fireEvent.click(
      await screen.findByRole("button", { name: "Begin combat" }),
    );
    expect(await screen.findByText(/Slime on the Verge/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Attack" }));

    expect(await screen.findByText("VICTORY")).toBeInTheDocument();
    expect(screen.getByText(/Gained 45 XP and 18 gold/)).toBeInTheDocument();
    expect(screen.getByText(/Victory! \+45 XP/)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Continue/i }),
    ).toBeInTheDocument();
  });

  it("restores an active canonical encounter after refresh", async () => {
    installFetch(true);
    window.localStorage.setItem(
      "yggdrasil-active-combat:character-1",
      "combat-1",
    );
    render(<App />);

    await continueExistingGame("Aster Vale");
    expect(await screen.findByText(/Slime on the Verge/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Attack" })).toBeInTheDocument();
  });

  it("escapes combat and returns to a refreshed archive", async () => {
    installFetch(true);
    render(<App />);

    await continueExistingGame("Aster Vale");
    fireEvent.click(screen.getByRole("button", { name: "Encounters" }));
    fireEvent.click(
      await screen.findByRole("button", { name: "Begin combat" }),
    );
    fireEvent.click(await screen.findByRole("button", { name: "Flee" }));
    expect(await screen.findByText("Escaped!")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Continue/i }));

    await screen.findByText("Aster Vale");
    fireEvent.click(screen.getByRole("button", { name: "Travel" }));
    expect(
      await screen.findByRole("heading", { name: "Known world" }),
    ).toBeInTheDocument();
  });

  it("can use skill and item in combat", async () => {
    installFetch(true);
    render(<App />);

    await continueExistingGame("Aster Vale");
    fireEvent.click(screen.getByRole("button", { name: "Encounters" }));
    fireEvent.click(
      await screen.findByRole("button", { name: "Begin combat" }),
    );

    // Use Skill
    const skillBtn = await screen.findByText(/Power Strike/i);
    fireEvent.click(skillBtn);

    // Use Item
    const itemBtn = await screen.findByText(/Item/i);
    fireEvent.click(itemBtn);

    const continueBtn = await screen.findByRole("button", {
      name: /Continue/i,
    });
    fireEvent.click(continueBtn);
    expect(await screen.findByText(/Frontier Gate/i)).toBeInTheDocument();
  });
});
