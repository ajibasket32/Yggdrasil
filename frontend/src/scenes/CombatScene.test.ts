/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call */
import { describe, it, expect, vi, beforeEach } from "vitest";
import CombatScene from "./CombatScene";
import type { CombatState, CombatParticipant } from "../types/gameplay";

describe("CombatScene", () => {
  let scene: any;

  beforeEach(() => {
    scene = new CombatScene();
    scene.load = { image: vi.fn(), spritesheet: vi.fn() };
    scene.add = {
      graphics: vi.fn(() => ({
        fillGradientStyle: vi.fn(),
        fillRect: vi.fn(),
        clear: vi.fn(),
        fillStyle: vi.fn(),
      })),
      sprite: vi.fn(() => ({
        setScale: vi.fn(),
        setFlipX: vi.fn(),
        texture: { key: "slime" },
        setTexture: vi.fn(),
        x: 100,
      })),
      text: vi.fn(() => ({
        setOrigin: vi.fn(() => ({
          setText: vi.fn(),
        })),
        setText: vi.fn(),
      })),
    };
    scene.cameras = {
      main: { width: 800, height: 600, shake: vi.fn() },
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
      }
    };
  });

  it("preloads assets", () => {
    scene.preload();
    expect(scene.load.image).toHaveBeenCalled();
    expect(scene.load.spritesheet).toHaveBeenCalled();
  });

  it("creates scene and handles various combat states", () => {
    scene.create();
    expect(scene.add.graphics).toHaveBeenCalled();
    expect(scene.tweens.add).toHaveBeenCalled();
    expect(scene.registry.events.on).toHaveBeenCalledWith("changedata-combatState", expect.any(Function), scene);

    // Test syncState with no combat
    scene.registry.get.mockReturnValue(undefined);
    scene.registry._trigger("changedata-combatState");

    // Test syncState with valid combat
    const mockCombat = {
      combat_id: "c1",

      encounter_name: "Goblin Ambush",
      status: "ACTIVE",
      round_number: 1,
      participants: [
        { id: "p1", name: "Player", side: "PLAYER", current_hp: 100, max_hp: 100, current_mp: 50, max_mp: 50, level: 1 } as CombatParticipant,
        { id: "e1", name: "Goblin", side: "ENEMY", current_hp: 50, max_hp: 50, current_mp: 0, max_mp: 0, level: 1 } as CombatParticipant,
      ],
      turn_order: ["p1", "e1"],

      rewards: { experience: 0, gold: 0, items: [] }
    } as unknown as CombatState;

    scene.registry.get.mockReturnValue(mockCombat);
    scene.registry._trigger("changedata-combatState");
    expect(scene.enemySprite.setTexture).toHaveBeenCalledWith("goblin");

    // Test damage animation
    const mockCombatDamage = {
      ...mockCombat,
      participants: [
        { id: "p1", name: "Player", side: "PLAYER", current_hp: 80, max_hp: 100, current_mp: 50, max_mp: 50, level: 1 } as CombatParticipant,
        { id: "e1", name: "Goblin", side: "ENEMY", current_hp: 20, max_hp: 50, current_mp: 0, max_mp: 0, level: 1 } as CombatParticipant,
      ],
    };
    scene.registry.get.mockReturnValue(mockCombatDamage);
    scene.registry._trigger("changedata-combatState");
    expect(scene.tweens.add).toHaveBeenCalled(); // Hit animation

    // Test boss sprite
    const mockCombatBoss = {
      ...mockCombat,
      participants: [
        { id: "p1", name: "Player", side: "PLAYER", current_hp: 80, max_hp: 100, current_mp: 50, max_mp: 50, level: 1, properties: {}, active_effects: [] },
        { id: "e1", name: "Dragon Boss", side: "ENEMY", current_hp: 500, max_hp: 500, current_mp: 0, max_mp: 0, level: 10, properties: {}, active_effects: [] },
      ],
    };
    scene.registry.get.mockReturnValue(mockCombatBoss);
    scene.registry._trigger("changedata-combatState");
    expect(scene.enemySprite.setTexture).toHaveBeenCalledWith("boss");
  });
});
