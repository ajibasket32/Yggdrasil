import { describe, it, expect, vi } from "vitest";
import WorldScene from "./WorldScene";

describe("WorldScene", () => {
  it("preloads and creates assets", () => {
    const scene = new WorldScene();
    scene.preload();
    expect(scene.load.image).toHaveBeenCalled();
    expect(scene.load.spritesheet).toHaveBeenCalled();

    scene.create();
    expect(scene.add.text).toHaveBeenCalled();
    expect(scene.add.sprite).toHaveBeenCalled();

    // Trigger keyboard events
    const onHandler = (scene.input.keyboard?.on as any).mock.calls[0][1];
    onHandler({ key: "ArrowLeft" });
    onHandler({ key: "ArrowRight" });
    onHandler({ key: "ArrowUp" });
    onHandler({ key: "ArrowDown" });
    onHandler({ key: "Other" });
  });
});
