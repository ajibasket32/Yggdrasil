import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import App from "../App";
import { installFetch, response } from "./fixtures";
import { continueExistingGame } from "./helpers";

vi.mock("../components/GameCanvas");

describe("Frontend Failure Modes and Edge Cases", () => {
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

  it("handles travel failure", async () => {
    installFetch(true);
    const fetchMock = vi.mocked(fetch);
    render(<App />);

    await continueExistingGame("Aster Vale");

    fetchMock.mockImplementationOnce(() =>
      response("Travel blocked by magic", false),
    );

    fireEvent.click(screen.getByText("Travel"));
    fireEvent.click(screen.getByText("Travel here"));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Travel blocked by magic",
    );
  });

  it("handles save failure", async () => {
    installFetch(true);
    const fetchMock = vi.mocked(fetch);
    render(<App />);

    await continueExistingGame("Aster Vale");

    fetchMock.mockImplementationOnce(() => response("Disk full", false));

    fireEvent.click(screen.getByText("Save Chronicle"));

    expect(await screen.findByRole("alert")).toHaveTextContent("Disk full");
  });

  it("handles NPC interaction failure", async () => {
    installFetch(true, true, "VICTORY", { worldAvailable: true });
    const fetchMock = vi.mocked(fetch);
    render(<App />);

    await continueExistingGame("Aster Vale");

    // The next call to interact should fail
    // Note: interact is called via gameApi.interact
    const originalMock = fetchMock.getMockImplementation();
    fetchMock.mockImplementation((url, init) => {
      if (url.toString().includes("/interact")) {
        return response("NPC is busy", false);
      }
      return originalMock!(url, init);
    });

    fireEvent.click(await screen.findByText("Canvas NPC Marker"));
    const greetBtn = await screen.findByText("Greet");
    fireEvent.click(greetBtn);

    expect(await screen.findByRole("alert")).toHaveTextContent("NPC is busy");
  });

  it("can close the narrative box", async () => {
    installFetch(true, true, "VICTORY", { worldAvailable: true });
    render(<App />);

    await continueExistingGame("Aster Vale");

    // Trigger narrative
    fireEvent.click(screen.getByText("Travel"));
    fireEvent.click(screen.getByText("Observe surroundings"));

    const closeBtn = await screen.findByText("Continue ▼");
    fireEvent.click(closeBtn);

    expect(screen.queryByText("Continue ▼")).not.toBeInTheDocument();
  });

  it("shows empty state when no dungeons are present", async () => {
    installFetch(true, true, "VICTORY", { worldAvailable: false });
    render(<App />);

    await continueExistingGame("Aster Vale");

    fireEvent.click(screen.getByText("Journal"));
    expect(
      await screen.findByText("No dungeon is visible here."),
    ).toBeInTheDocument();
  });

  it("handles character deletion failure", async () => {
    installFetch(true);
    const fetchMock = vi.mocked(fetch);
    render(<App />);

    await continueExistingGame("Aster Vale");

    const confirmSpy = vi
      .spyOn(window, "confirm")
      .mockImplementation(() => true);

    fireEvent.click(screen.getByText("Conclude"));

    // Mock delete failure
    fetchMock.mockImplementationOnce(() =>
      response("Immutable chronicle", false),
    );

    fireEvent.click(screen.getByText("Finalize & Delete Save"));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Immutable chronicle",
    );
    confirmSpy.mockRestore();
  });

  it("handles load failure", async () => {
    installFetch(false);
    const fetchMock = vi.mocked(fetch);

    // Mock definitions success but characters fail
    fetchMock.mockImplementationOnce(() =>
      Promise.resolve(
        response({
          races: [],
          starting_jobs: [],
          starting_location: { id: "loc" },
        }),
      ),
    );
    fetchMock.mockImplementationOnce(() =>
      Promise.resolve(response("Database offline", false)),
    );

    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Database offline",
    );
  });

  it("handles character creation failure with non-Error catch", async () => {
    installFetch(false);
    const fetchMock = vi.mocked(fetch);
    render(<App />);

    // Success for definitions and characters
    fetchMock.mockImplementationOnce(() =>
      Promise.resolve(
        response({
          races: [
            { id: "r1", name: "Race", description: "D", category: "Cat" },
          ],
          starting_jobs: [
            { id: "j1", name: "Job", description: "D", tier: "T" },
          ],
          starting_location: { id: "l1" },
        }),
      ),
    );
    fetchMock.mockImplementationOnce(() => Promise.resolve(response([])));

    // Trigger creation
    fireEvent.click(await screen.findByText("New Game"));
    fireEvent.change(screen.getByLabelText("Character name"), {
      target: { value: "New Hero" },
    });

    // Mock creation throws non-Error
    fetchMock.mockImplementationOnce(() => Promise.reject("string error"));

    fireEvent.click(screen.getByText("Create character"));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Character creation failed",
    );
  });

  it("handles combat restoration failure", async () => {
    // Need a setup where active combat is in localStorage
    installFetch(true);
    const fetchMock = vi.mocked(fetch);

    window.localStorage.setItem(
      "yggdrasil-active-combat:character-1",
      "combat-1",
    );

    // Override the specific combat call to fail
    const originalMock = fetchMock.getMockImplementation();
    fetchMock.mockImplementation((url, init) => {
      if (url.toString().includes("/combat/combat-1")) {
        return Promise.resolve(response("Combat expired", false));
      }
      return originalMock!(url, init);
    });

    render(<App />);

    await continueExistingGame("Aster Vale");
    expect(
      window.localStorage.getItem("yggdrasil-active-combat:character-1"),
    ).toBeNull();
  });

  it("handles combat start failure", async () => {
    installFetch(true, true, "VICTORY", { startSucceeds: false });
    render(<App />);
    await continueExistingGame("Aster Vale");
    fireEvent.click(screen.getByText("Encounters"));
    fireEvent.click(screen.getByText("Begin combat"));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Encounter unavailable",
    );
  });

  it("handles flee failure", async () => {
    installFetch(true, true, "VICTORY", { fleeSucceeds: false });
    render(<App />);
    await continueExistingGame("Aster Vale");
    fireEvent.click(screen.getByText("Encounters"));
    fireEvent.click(screen.getByText("Begin combat"));
    fireEvent.click(await screen.findByText("Flee"));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Escape blocked",
    );
  });

  it("handles combat action failure", async () => {
    installFetch(true, true, "VICTORY", { actionSucceeds: false });
    render(<App />);
    await continueExistingGame("Aster Vale");
    fireEvent.click(screen.getByText("Encounters"));
    fireEvent.click(screen.getByText("Begin combat"));
    fireEvent.click(await screen.findByText("Attack"));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Action rejected",
    );
  });
});
