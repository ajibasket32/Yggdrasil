import { describe, it, expect, vi } from "vitest";
import CombatScene from "./CombatScene";

describe("CombatScene", () => {
  it("preloads and creates assets", () => {
    const scene = new CombatScene();
    scene.preload();
    expect(scene.load.image).toHaveBeenCalled();
    expect(scene.load.spritesheet).toHaveBeenCalled();

    scene.create();
    expect(scene.add.text).toHaveBeenCalled();
    expect(scene.add.sprite).toHaveBeenCalled();
  });
});
