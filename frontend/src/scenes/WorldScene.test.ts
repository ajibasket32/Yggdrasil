import { describe, it, expect } from "vitest";
import WorldScene from "./WorldScene";

describe("WorldScene", () => {
  it("preloads and creates assets", () => {
    const scene = new WorldScene();
    scene.preload();
    // eslint-disable-next-line @typescript-eslint/unbound-method
    expect(scene.load.image).toHaveBeenCalled();
    // eslint-disable-next-line @typescript-eslint/unbound-method
    expect(scene.load.spritesheet).toHaveBeenCalled();

    scene.create();
    // eslint-disable-next-line @typescript-eslint/unbound-method
    expect(scene.add.text).toHaveBeenCalled();
    // eslint-disable-next-line @typescript-eslint/unbound-method
    expect(scene.add.sprite).toHaveBeenCalled();

    // Trigger keyboard events
    // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access
    const onHandler = (scene.input.keyboard?.on as any).mock.calls[0][1];
    // eslint-disable-next-line @typescript-eslint/no-unsafe-call
    onHandler({ key: "ArrowLeft" });
    // eslint-disable-next-line @typescript-eslint/no-unsafe-call
    onHandler({ key: "ArrowRight" });
    // eslint-disable-next-line @typescript-eslint/no-unsafe-call
    onHandler({ key: "ArrowUp" });
    // eslint-disable-next-line @typescript-eslint/no-unsafe-call
    onHandler({ key: "ArrowDown" });
    // eslint-disable-next-line @typescript-eslint/no-unsafe-call
    onHandler({ key: "Other" });
  });
});
