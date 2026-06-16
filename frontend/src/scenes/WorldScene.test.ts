/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call */
import { describe, it, expect, vi, beforeEach } from "vitest";
import WorldScene from "./WorldScene";

describe("WorldScene", () => {
  let scene: any;

  beforeEach(() => {
    scene = new WorldScene();
    scene.load = { image: vi.fn(), spritesheet: vi.fn() };
    scene.add = {
      graphics: vi.fn(() => ({
        fillGradientStyle: vi.fn(),
        fillRect: vi.fn(),
      })),
      sprite: vi.fn(() => ({
        setScale: vi.fn(),
      })),
      text: vi.fn(() => ({
        setOrigin: vi.fn(() => ({
          setText: vi.fn(),
        })),
        setText: vi.fn(),
      })),
    };
    scene.cameras = {
      main: { width: 800, height: 600, flash: vi.fn() },
    };
    scene.tweens = { add: vi.fn() };

    // Mock registry
    const registryCallbacks: any = {};
    scene.registry = {
      events: {
        on: vi.fn((event, callback, context) => {
          registryCallbacks[event] = callback.bind(context);
        }),
      },
      get: vi.fn(),
      _trigger: (event: string) => {
        if (registryCallbacks[event]) registryCallbacks[event]();
      },
    };
  });

  it("preloads and creates assets", () => {
    scene.preload();
    expect(scene.load.image).toHaveBeenCalled();
    expect(scene.load.spritesheet).toHaveBeenCalled();

    scene.create();
    expect(scene.add.graphics).toHaveBeenCalled();
    expect(scene.add.sprite).toHaveBeenCalled();

    // Test branch where location is null
    scene.registry.get.mockReturnValue(null);
    scene.registry._trigger("changedata-locationName");
    expect(scene.cameras.main.flash).not.toHaveBeenCalled();

    // Test branch where location is provided
    scene.registry.get.mockReturnValue("Aster Vale");
    // need to mock the text object since it was set locally
    scene.locationText = { setText: vi.fn() };
    scene.registry._trigger("changedata-locationName");
    expect(scene.locationText.setText).toHaveBeenCalledWith("Aster Vale");
    expect(scene.cameras.main.flash).toHaveBeenCalled();
  });
});
