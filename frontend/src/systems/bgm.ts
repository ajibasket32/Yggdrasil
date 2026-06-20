import battleThemeUrl from "../assets/audio/battle_theme.wav";
import sylvanBranchUrl from "../assets/audio/sylvan_branch.wav";
import titleThemeUrl from "../assets/audio/title_theme.wav";
import valerisCityUrl from "../assets/audio/valeris_city.wav";
import valerisOutskirtsUrl from "../assets/audio/valeris_outskirts.wav";
import { musicKeyForLocation, type WorldMusicKey } from "./worldMaps";

export type BgmKey = WorldMusicKey;

const TRACKS: Record<BgmKey, string> = {
  title_theme: titleThemeUrl,
  valeris_city: valerisCityUrl,
  valeris_outskirts: valerisOutskirtsUrl,
  sylvan_branch: sylvanBranchUrl,
  battle_theme: battleThemeUrl,
};

export const bgmKeyForScene = (
  locationName: string | undefined,
  inCombat: boolean,
): BgmKey => (inCombat ? "battle_theme" : musicKeyForLocation(locationName));

export class BgmManager {
  private currentKey: BgmKey | null = null;
  private currentAudio: HTMLAudioElement | null = null;
  private readonly tracks: Record<BgmKey, string>;
  private muted = false;
  private volume = 0.45;
  private status: "idle" | "missing" | "muted" | "playing" | "blocked" = "idle";

  constructor(tracks: Record<BgmKey, string> = TRACKS) {
    this.tracks = tracks;
  }

  setMuted(muted: boolean): void {
    this.muted = muted;
    if (this.currentAudio) {
      this.currentAudio.muted = muted;
      if (muted) this.currentAudio.pause();
    }
    if (muted) this.status = "muted";
    this.updateAudit();
  }

  setVolume(volume: number): void {
    this.volume = Math.max(0, Math.min(1, volume));
    if (this.currentAudio) this.currentAudio.volume = this.volume;
    this.updateAudit();
  }

  async play(key: BgmKey): Promise<void> {
    if (this.muted) {
      this.status = "muted";
      this.updateAudit();
      return;
    }
    const source = this.tracks[key];
    if (!source) {
      this.status = "missing";
      this.updateAudit();
      return;
    }
    if (this.currentKey === key && this.currentAudio) {
      this.currentAudio.muted = this.muted;
      this.currentAudio.volume = this.volume;
      try {
        await this.currentAudio.play();
        this.status = "playing";
      } catch {
        this.currentAudio.pause();
        this.status = "blocked";
      }
      this.updateAudit();
      return;
    }

    this.currentAudio?.pause();
    const audio = new Audio(source);
    audio.loop = true;
    audio.volume = this.volume;
    audio.muted = this.muted;
    this.currentKey = key;
    this.currentAudio = audio;

    try {
      await audio.play();
      this.status = "playing";
    } catch {
      audio.pause();
      this.status = "blocked";
    }
    this.updateAudit();
  }

  stop(): void {
    this.currentAudio?.pause();
    this.currentAudio = null;
    this.currentKey = null;
    this.status = "idle";
    this.updateAudit();
  }

  getCurrentKey(): BgmKey | null {
    return this.currentKey;
  }

  getStatus(): string {
    return this.status;
  }

  private updateAudit(): void {
    if (!window.location.search.includes("audit=1")) return;
    const auditWindow = window as Window & {
      __YGGDRASIL_AUDIT__?: Record<string, unknown>;
    };
    auditWindow.__YGGDRASIL_AUDIT__ = {
      ...(auditWindow.__YGGDRASIL_AUDIT__ ?? {}),
      bgm: {
        currentKey: this.currentKey,
        muted: this.muted,
        volume: this.volume,
        status: this.status,
      },
    };
  }
}

export const bgm = new BgmManager();
