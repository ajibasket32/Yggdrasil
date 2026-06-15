import { gameApi, getPlayerId } from "./gameApi";

afterEach(() => {
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

describe("gameApi", () => {
  it("creates and reuses a local player boundary", () => {
    vi.stubGlobal("crypto", { randomUUID: () => "generated-player" });

    expect(getPlayerId()).toBe("generated-player");
    expect(getPlayerId()).toBe("generated-player");
  });

  it("uses a stable player fallback without UUID generation", () => {
    vi.stubGlobal("crypto", {});

    expect(getPlayerId()).toBe("9d463696-4daf-4f3c-bb8c-f21389acb991");
  });

  it("sends identity, idempotency, and JSON headers", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      void input;
      void init;
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ success: true, data: { id: "new" } }),
      } as Response);
    });
    vi.stubGlobal("fetch", fetchMock);

    await gameApi.createCharacter(
      "player-1",
      {
        name: "Mira Ash",
        race_id: "race-1",
        gender: "Female",
        alignment: "GOOD",
        starting_job_id: "job-1",
      },
      "create-1",
    );

    const call = fetchMock.mock.calls[0];
    expect(call).toBeDefined();
    const options = call?.[1];
    expect(options).toBeDefined();
    if (options === undefined) {
      throw new Error("Request options were not captured");
    }
    const headers = options.headers as Headers;
    expect(options.method).toBe("POST");
    expect(headers.get("X-Player-ID")).toBe("player-1");
    expect(headers.get("Idempotency-Key")).toBe("create-1");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("surfaces the server's stable error message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          json: () =>
            Promise.resolve({ error: { message: "Route is not reachable" } }),
        } as Response),
      ),
    );

    await expect(gameApi.characters("player-1")).rejects.toThrow(
      "Route is not reachable",
    );
  });

  it("falls back to a generic message for a malformed response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: false }),
        } as Response),
      ),
    );

    await expect(gameApi.definitions()).rejects.toThrow("Request failed");
  });

  it("reports non-JSON responses as proxy or backend configuration failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.reject(new SyntaxError("Unexpected token '<'")),
        } as Response),
      ),
    );

    await expect(gameApi.definitions()).rejects.toThrow(
      "API returned an invalid response. Check backend/proxy configuration.",
    );
  });

  it("handles malformed error response without message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          json: () => Promise.resolve({ error: {} }),
        } as Response),
      ),
    );

    await expect(gameApi.characters("player-1")).rejects.toThrow(
      "Request failed",
    );
  });

  it("sends deterministic world mutation contracts", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      void input;
      void init;
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ success: true, data: {} }),
      } as Response);
    });
    vi.stubGlobal("fetch", fetchMock);

    await gameApi.questMutation(
      "player-1",
      "character-1",
      "quest-1",
      "accept",
      "quest-key",
    );
    await gameApi.interact(
      "player-1",
      "character-1",
      "npc-1",
      "OFFER_HELP",
      "npc-key",
    );
    await gameApi.joinFaction(
      "player-1",
      "character-1",
      "faction-1",
      "faction-key",
    );
    await gameApi.dungeonMutation(
      "player-1",
      "character-1",
      "dungeon-1",
      "clear",
      "dungeon-key",
    );

    expect(fetchMock).toHaveBeenCalledTimes(4);
    for (const call of fetchMock.mock.calls) {
      const options = call[1];
      if (options === undefined) {
        throw new Error("World mutation request options were not captured");
      }
      expect(options.method).toBe("POST");
      expect((options.headers as Headers).get("X-Player-ID")).toBe("player-1");
      expect((options.headers as Headers).get("Idempotency-Key")).toBeTruthy();
    }
  });

  it("sends bounded narrative requests with fixed menu topics", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      void input;
      void init;
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ success: true, data: {} }),
      } as Response);
    });
    vi.stubGlobal("fetch", fetchMock);

    await gameApi.dialogue(
      "player-1",
      "character-1",
      "npc-1",
      "LOCAL_NEWS",
      "dialogue-key",
    );
    await gameApi.questFraming(
      "player-1",
      "character-1",
      "quest-1",
      "framing-key",
    );
    await gameApi.locationDescription(
      "player-1",
      "character-1",
      "location-1",
      "location-key",
    );

    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/v1/npcs/npc-1/dialogue");
    expect(fetchMock.mock.calls[0]?.[1]?.body).toBe(
      JSON.stringify({
        character_id: "character-1",
        topic_id: "LOCAL_NEWS",
      }),
    );
    for (const call of fetchMock.mock.calls) {
      const options = call[1];
      expect(options?.method).toBe("POST");
      expect((options?.headers as Headers).get("X-Player-ID")).toBe("player-1");
      expect((options?.headers as Headers).get("Idempotency-Key")).toBeTruthy();
    }
  });
});
