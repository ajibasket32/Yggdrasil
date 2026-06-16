/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/unbound-method */
import { describe, it, expect, vi, beforeEach } from "vitest";
import WorldScene from "./WorldScene";

describe("WorldScene", () => {
  let scene: any;

  beforeEach(() => {
    scene = new WorldScene();
    scene.load = { image: vi.fn(), spritesheet: vi.fn() };
    scene.add = {
      tileSprite: vi.fn(function (this: any) {
        return {
          setOrigin: vi.fn(function (this: any) {
            return this;
          }),
          setTileScale: vi.fn(function (this: any) {
            return this;
          }),
        };
      }),
      graphics: vi.fn(() => ({
        fillGradientStyle: vi.fn(),
        fillRect: vi.fn(),
      })),
      sprite: vi.fn(function (this: any) {
        return {
          setScale: vi.fn(function (this: any) {
            return this;
          }),
          setCollideWorldBounds: vi.fn(function (this: any) {
            return this;
          }),
          body: {
            velocity: {
              clone: vi.fn(() => ({
                normalize: vi.fn(() => ({ scale: vi.fn() })),
              })),
              normalize: vi.fn(() => ({ scale: vi.fn() })),
            },
            setVelocity: vi.fn(),
            setVelocityX: vi.fn(),
            setVelocityY: vi.fn(),
          },
          setFlipX: vi.fn(),
          x: 0,
          y: 0,
        };
      }),
      text: vi.fn(function (this: any) {
        return {
          setOrigin: vi.fn(function (this: any) {
            return this;
          }),
          setScrollFactor: vi.fn(function (this: any) {
            return this;
          }),
          setVisible: vi.fn(function (this: any) {
            return this;
          }),
          setText: vi.fn(function (this: any) {
            return this;
          }),
        };
      }),
      group: vi.fn(() => ({
        add: vi.fn(),
        clear: vi.fn(),
        getChildren: vi.fn(() => []),
      })),
    };
    scene.physics = {
      world: { setBounds: vi.fn() },
      add: {
        sprite: vi.fn(function (this: any) {
          return {
            setScale: vi.fn(function (this: any) {
              return this;
            }),
            setCollideWorldBounds: vi.fn(function (this: any) {
              return this;
            }),
            body: {
              velocity: {
                clone: vi.fn(() => ({
                  normalize: vi.fn(() => ({ scale: vi.fn() })),
                })),
                normalize: vi.fn(() => ({ scale: vi.fn() })),
              },
              setVelocity: vi.fn(),
              setVelocityX: vi.fn(),
              setVelocityY: vi.fn(),
            },
            setFlipX: vi.fn(),
            x: 0,
            y: 0,
          };
        }),
      },
    };
    scene.input = {
      keyboard: {
        createCursorKeys: vi.fn(() => ({
          left: { isDown: false },
          right: { isDown: false },
          up: { isDown: false },
          down: { isDown: false },
          space: { isDown: false },
          shift: { isDown: false },
        })),
        addKeys: vi.fn(() => ({
          W: { isDown: false },
          A: { isDown: false },
          S: { isDown: false },
          D: { isDown: false },
          E: { isDown: false },
        })),
        JustDown: vi.fn(() => false),
      },
    };
    scene.cameras = {
      main: {
        width: 800,
        height: 600,
        flash: vi.fn(),
        setBounds: vi.fn(),
        startFollow: vi.fn(),
      },
    };
    scene.tweens = { add: vi.fn() };
    scene.game = { events: { emit: vi.fn() } };

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
    expect(scene.physics.world.setBounds).toHaveBeenCalled();
    expect(scene.add.tileSprite).toHaveBeenCalled();
    expect(scene.physics.add.sprite).toHaveBeenCalled();

    // Test branch where location is null
    scene.registry.get.mockReturnValue(null);
    scene.registry._trigger("changedata-locationName");

    // Test branch where location is provided
    scene.registry.get.mockReturnValue("Aster Vale");
    scene.registry._trigger("changedata-locationName");
    expect(scene.locationText.setText).toHaveBeenCalledWith("Aster Vale");
  });

  it("handles movement and updates", () => {
    scene.create();
    scene.update();
    expect(scene.player.body.setVelocity).toHaveBeenCalledWith(0);
    expect(scene.player.body.velocity.normalize).toHaveBeenCalled();
  });

  it("refreshes markers when data changes", () => {
    scene.create();
    scene.registry.get.mockImplementation((key: string) => {
      if (key === "npcs") return [{ id: "1", name: "NPC 1" }];
      if (key === "encounters") return [{ id: "1", name: "Enc 1" }];
      if (key === "reachableLocations") return [{ id: "1", name: "Loc 1" }];
      return [];
    });
    scene.registry._trigger("changedata-npcs");
    scene.registry._trigger("changedata-encounters");
    scene.registry._trigger("changedata-reachableLocations");
    expect(scene.markers.add).toHaveBeenCalled();
  });

  it("handles interactions with markers", () => {
    scene.create();
    const mockMarker = {
      texture: { key: "player" },
      x: 100,
      y: 100,
      markerType: "NPC",
      markerData: { name: "TestNPC" },
    };
    scene.markers.getChildren.mockReturnValue([mockMarker]);
    scene.player.x = 105;
    scene.player.y = 105;
    scene.wasd.E.isDown = true;
    vi.mocked(Phaser.Input.Keyboard.JustDown).mockReturnValue(true);

    scene.update();
    expect(scene.interactionHint.setVisible).toHaveBeenCalledWith(true);
    expect(scene.game.events.emit).toHaveBeenCalledWith(
      "phaser-interact",
      expect.anything(),
    );
  });

  it("handles travel and encounter interactions", () => {
    scene.create();
    const markers = [
      {
        texture: { key: "player" },
        x: 100,
        y: 100,
        markerType: "TRAVEL",
        markerData: { name: "TestLoc" },
      },
      {
        texture: { key: "player" },
        x: 200,
        y: 200,
        markerType: "ENCOUNTER",
        markerData: { name: "TestEnc" },
      },
    ];
    scene.markers.getChildren.mockReturnValue(markers);
    vi.mocked(Phaser.Input.Keyboard.JustDown).mockReturnValue(true);

    // Travel
    scene.player.x = 101;
    scene.player.y = 101;
    scene.update();
    expect(scene.game.events.emit).toHaveBeenCalledWith(
      "phaser-travel",
      expect.anything(),
    );

    // Encounter
    scene.player.x = 201;
    scene.player.y = 201;
    scene.update();
    expect(scene.game.events.emit).toHaveBeenCalledWith(
      "phaser-encounter",
      expect.anything(),
    );
  });
});
