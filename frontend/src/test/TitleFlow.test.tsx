import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import App from "../App";
import {
  installFetch,
  response,
  definitions,
  sheet,
  narrative,
} from "./fixtures";
import {
  createCharacterFromTitleFlow,
  continueExistingGame,
  startNewGame,
} from "./helpers";

describe("Title Flow and Character Creation", () => {
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

  it("renders title screen first", async () => {
    installFetch(false);
    render(<App />);
    expect(await screen.findByText("Yggdrasil Chronicles")).toBeInTheDocument();
    expect(screen.getByText("v1.1 JRPG Polish Release")).toBeInTheDocument();
  });

  it("creates and presents an authoritative character sheet", async () => {
    const calls = installFetch(false);
    render(<App />);

    await createCharacterFromTitleFlow("Aster Vale");

    expect(await screen.findByText("Aster Vale")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Status" }));
    expect(await screen.findByText("Power Strike")).toBeInTheDocument();
    expect(calls).toContain("POST /api/v1/characters");
  });

  it("loads an existing character from title screen", async () => {
    installFetch(true);
    render(<App />);

    await continueExistingGame("Aster Vale");
    expect(screen.getByText("📍 Frontier Gate")).toBeInTheDocument();
  });

  it("keeps creation available when the server rejects it", async () => {
    installFetch(false);
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockImplementationOnce(() => response(definitions));
    fetchMock.mockImplementationOnce(() => response([]));
    fetchMock.mockImplementationOnce(() => response("Name unavailable", false));
    render(<App />);

    await startNewGame();
    fireEvent.change(screen.getByLabelText("Character name"), {
      target: { value: "Aster Vale" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create character" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Name unavailable",
    );
    expect(
      screen.getByRole("heading", { name: "Create your character" }),
    ).toBeInTheDocument();
  });

  it("can trigger ending and return to game", async () => {
    installFetch(true);
    render(<App />);

    await continueExistingGame("Aster Vale");
    expect(screen.getByText("📍 Frontier Gate")).toBeInTheDocument();

    const confirmSpy = vi
      .spyOn(window, "confirm")
      .mockImplementation(() => true);

    fireEvent.click(screen.getByText("Conclude"));
    expect(confirmSpy).toHaveBeenCalled();
    expect(screen.getByText("The End")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Return to Game"));
    expect(screen.queryByText("The End")).not.toBeInTheDocument();
    expect(screen.getByText("📍 Frontier Gate")).toBeInTheDocument();

    confirmSpy.mockRestore();
  });
});
