import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import App from "../App";
import { installFetch, sheet } from "./fixtures";
import { continueExistingGame } from "./helpers";

vi.mock("../components/GameCanvas");

describe("World Flow and Exploration", () => {
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

  it("loads an existing character and follows only a valid route", async () => {
    const calls = installFetch(true);
    render(<App />);

    await continueExistingGame("Aster Vale");
    fireEvent.click(screen.getByRole("button", { name: "Travel" }));
    expect(
      await screen.findByRole("heading", { name: "Known world" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Travel here" }));

    await waitFor(() => {
      expect(calls).toContain("POST /api/v1/characters/character-1/travel");
    });
  });

  it("reports a rejected route without losing the character sheet", async () => {
    installFetch(true, false);
    render(<App />);

    await continueExistingGame("Aster Vale");
    fireEvent.click(screen.getByRole("button", { name: "Travel" }));
    fireEvent.click(await screen.findByRole("button", { name: "Travel here" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Route closed");
    expect(screen.getByText("Aster Vale")).toBeInTheDocument();
  });

  it("handles travel events emitted by the game canvas", async () => {
    const calls = installFetch(true);
    render(<App />);

    await continueExistingGame("Aster Vale");
    fireEvent.click(
      await screen.findByRole("button", { name: "Canvas Travel Marker" }),
    );

    await waitFor(() => {
      expect(calls).toContain("POST /api/v1/characters/character-1/travel");
    });
  });

  it("handles NPC interaction events emitted by the game canvas", async () => {
    const calls = installFetch(true, true, "VICTORY", {
      worldAvailable: true,
    });
    render(<App />);

    await continueExistingGame("Aster Vale");
    fireEvent.click(
      await screen.findByRole("button", { name: "Canvas NPC Marker" }),
    );

    expect(
      await screen.findByText("The roots remember who keeps watch."),
    ).toBeInTheDocument();
    expect(calls).toContain("POST /api/v1/npcs/npc-1/dialogue");
  });

  it("handles encounter events emitted by the game canvas", async () => {
    installFetch(true);
    render(<App />);

    await continueExistingGame("Aster Vale");
    fireEvent.click(
      await screen.findByRole("button", { name: "Canvas Encounter Marker" }),
    );

    expect(await screen.findByText(/Slime on the Verge/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Attack" })).toBeInTheDocument();
  });

  it("describes the current location and reports narrative failures", async () => {
    const calls = installFetch(true, true, "VICTORY", {
      worldAvailable: true,
      narrativeSucceeds: false,
      framingSucceeds: false,
    });
    render(<App />);

    await continueExistingGame("Aster Vale");
    fireEvent.click(screen.getByRole("button", { name: "Travel" }));
    fireEvent.click(
      await screen.findByRole("button", { name: "Observe surroundings" }),
    );
    expect(
      await screen.findByText("Lanterns hold back the green dusk."),
    ).toBeInTheDocument();
    expect(calls).toContain("POST /api/v1/locations/location-1/description");

    // Test continuing after observation
    fireEvent.click(screen.getByRole("button", { name: "Continue ▼" }));
  });
});
