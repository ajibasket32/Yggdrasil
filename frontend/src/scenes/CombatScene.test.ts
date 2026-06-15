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

    // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-member-access
    (scene as any).cameras = { main: { setBackgroundColor: vi.fn() } };
    // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-member-access
    (scene as any).tweens = { add: vi.fn() };
    
    // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-member-access
    (scene as any).add = { sprite: vi.fn().mockReturnValue({ setScale: vi.fn(), setFlipX: vi.fn() }) };
    scene.create();
    // eslint-disable-next-line @typescript-eslint/unbound-method
    expect(scene.cameras.main.setBackgroundColor).toHaveBeenCalled();
    // eslint-disable-next-line @typescript-eslint/unbound-method
    expect(scene.tweens.add).toHaveBeenCalled();
    // eslint-disable-next-line @typescript-eslint/unbound-method
    expect(scene.add.sprite).toHaveBeenCalled();
  });
});
