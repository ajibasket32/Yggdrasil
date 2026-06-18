import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import App from "../App";
import { installFetch, response } from "./fixtures";
import { continueExistingGame } from "./helpers";

describe("Save and Load Flow", () => {
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

  it("persists the chronicle and handles save failures", async () => {
    const calls = installFetch(true);
    render(<App />);

    await continueExistingGame("Aster Vale");

    const saveButton = screen.getByRole("button", { name: "Save Chronicle" });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(calls).toContain("POST /api/v1/save");
    });
    expect(await screen.findByText("✓ Saved")).toBeInTheDocument();

    vi.stubGlobal(
      "fetch",
      vi.fn(() => response("Save failed", false)),
    );
    fireEvent.click(saveButton);
    expect(await screen.findByRole("alert")).toHaveTextContent("Save failed");
  });

  it("ends the chronicle after confirmation", async () => {
    const calls = installFetch(true);
    vi.stubGlobal(
      "confirm",
      vi.fn(() => true),
    );
    render(<App />);

    await continueExistingGame("Aster Vale");

    const concludeButton = await screen.findByRole("button", {
      name: "Conclude",
    });
    fireEvent.click(concludeButton);
    const endButton = await screen.findByRole("button", {
      name: "Finalize & Delete Save",
    });
    fireEvent.click(endButton);

    await waitFor(() => {
      expect(calls).toContain("DELETE /api/v1/save/character-1");
    });

    expect(await screen.findByText("Yggdrasil Chronicles")).toBeInTheDocument();
  });
});
