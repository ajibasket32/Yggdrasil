import { beforeEach, describe, expect, it, vi } from "vitest";
import { BgmManager, bgmKeyForScene, type BgmKey } from "./bgm";

class FakeAudio {
  static instances: FakeAudio[] = [];
  static shouldReject = false;

  loop = false;
  muted = false;
  volume = 1;
  paused = false;
  play = vi.fn(async () => {
    if (FakeAudio.shouldReject) throw new Error("blocked");
  });
  pause = vi.fn(() => {
    this.paused = true;
  });

  constructor(public readonly src: string) {
    FakeAudio.instances.push(this);
  }
}

describe("BGM manager", () => {
  const tracks: Record<BgmKey, string> = {
    title_theme: "/title.wav",
    valeris_city: "/city.wav",
    valeris_outskirts: "/outskirts.wav",
    sylvan_branch: "/forest.wav",
    battle_theme: "/battle.wav",
  };

  beforeEach(() => {
    FakeAudio.instances = [];
    FakeAudio.shouldReject = false;
    vi.stubGlobal("Audio", FakeAudio);
  });

  it("selects area music and combat music", () => {
    expect(bgmKeyForScene("Valeris City", false)).toBe("valeris_city");
    expect(bgmKeyForScene("Valeris Outskirts", false)).toBe(
      "valeris_outskirts",
    );
    expect(bgmKeyForScene("Sylvan Branch", false)).toBe("sylvan_branch");
    expect(bgmKeyForScene("Valeris City", true)).toBe("battle_theme");
  });

  it("switches combat music and restores area music", async () => {
    const manager = new BgmManager(tracks);

    await manager.play("valeris_city");
    await manager.play("battle_theme");
    await manager.play("valeris_city");

    expect(FakeAudio.instances.map((audio) => audio.src)).toEqual([
      "/city.wav",
      "/battle.wav",
      "/city.wav",
    ]);
    expect(manager.getCurrentKey()).toBe("valeris_city");
  });

  it("muted mode prevents playback calls", async () => {
    const manager = new BgmManager(tracks);

    manager.setMuted(true);
    await manager.play("battle_theme");

    expect(FakeAudio.instances).toEqual([]);
  });

  it("missing track fails safely", async () => {
    const manager = new BgmManager({ ...tracks, battle_theme: "" });

    await manager.play("battle_theme");

    expect(FakeAudio.instances).toEqual([]);
  });

  it("autoplay rejection fails safely", async () => {
    const manager = new BgmManager(tracks);
    FakeAudio.shouldReject = true;

    await manager.play("title_theme");

    expect(FakeAudio.instances[0]?.pause).toHaveBeenCalled();
    expect(manager.getCurrentKey()).toBe("title_theme");
  });

  it("unmuting retries the current track", async () => {
    const manager = new BgmManager(tracks);

    await manager.play("valeris_outskirts");
    manager.setMuted(true);
    manager.setMuted(false);
    await manager.play("valeris_outskirts");

    expect(FakeAudio.instances).toHaveLength(1);
    expect(FakeAudio.instances[0]?.play).toHaveBeenCalledTimes(2);
    expect(manager.getStatus()).toBe("playing");
  });
});
