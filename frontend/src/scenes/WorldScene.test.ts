import { describe, it, expect, vi } from "vitest";
import WorldScene from "./WorldScene";

describe("WorldScene", () => {
  it("preloads and creates assets", () => {
    const scene = new WorldScene();
    scene.preload();
    expect(scene.load.image).toHaveBeenCalled();
    expect(scene.load.spritesheet).toHaveBeenCalled();

    scene.create();
    expect(scene.add.graphics).toHaveBeenCalled();
    expect(scene.add.sprite).toHaveBeenCalled();
  });
});
