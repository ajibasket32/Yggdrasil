import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import App from "../App";
import { installFetch, narrative } from "./fixtures";
import { continueExistingGame } from "./helpers";

describe("Quest and NPC Interaction", () => {
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

  it("runs deterministic quest, NPC, faction, and dungeon actions", async () => {
    const calls = installFetch(true, true, "VICTORY", {
      worldAvailable: true,
    });
    render(<App />);

    await continueExistingGame("Aster Vale");
    fireEvent.click(screen.getByRole("button", { name: "Quests" }));

    // Accept quest
    fireEvent.click(
      await screen.findByRole("button", { name: "Accept quest" }),
    );
    await waitFor(() => {
      expect(calls).toContain("POST /api/v1/quests/quest-1/accept");
    });

    // NPC Interaction
    fireEvent.click(await screen.findByRole("button", { name: "Offer help" }));
    await waitFor(() => {
      expect(calls).toContain("POST /api/v1/npcs/npc-1/interact");
    });
    expect(screen.getByRole("status")).toHaveTextContent("Aid recorded.");

    // Join faction
    fireEvent.click(
      await screen.findByRole("button", { name: "Join faction" }),
    );
    await waitFor(() => {
      expect(calls).toContain("POST /api/v1/factions/faction-1/join");
    });

    // Enter dungeon
    fireEvent.click(
      await screen.findByRole("button", { name: "Enter dungeon" }),
    );
    await waitFor(() => {
      expect(calls).toContain("POST /api/v1/dungeons/dungeon-1/enter");
    });
  });

  it("presents bounded narrative choices without a chat input", async () => {
    const calls = installFetch(true, true, "VICTORY", {
      worldAvailable: true,
    });
    render(<App />);

    await continueExistingGame("Aster Vale");
    fireEvent.click(screen.getByRole("button", { name: "Quests" }));
    fireEvent.click(await screen.findByRole("button", { name: "Speak" }));

    expect(await screen.findByText(narrative.text)).toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(calls).toContain("POST /api/v1/npcs/npc-1/dialogue");

    fireEvent.click(screen.getByRole("button", { name: "Continue ▼" }));
    expect(screen.queryByText(narrative.text)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Quests" }));
    fireEvent.click(await screen.findByRole("button", { name: "Hear story" }));
    expect(
      await screen.findByText("A watch must be kept beneath the old boughs."),
    ).toBeInTheDocument();
    expect(calls).toContain("POST /api/v1/quests/quest-1/framing");
  });
});
