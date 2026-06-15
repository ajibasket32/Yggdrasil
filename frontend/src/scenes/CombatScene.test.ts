import { describe, it, expect } from "vitest";
import CombatScene from "./CombatScene";

describe("CombatScene", () => {
  it("preloads and creates assets", () => {
    const scene = new CombatScene();
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
  });
});
