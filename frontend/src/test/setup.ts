/* eslint-disable @typescript-eslint/no-explicit-any */
import "@testing-library/jest-dom/vitest";

if (typeof window.crypto.randomUUID !== "function") {
  window.crypto.randomUUID = () =>
    "test-uuid" as `${string}-${string}-${string}-${string}-${string}`;
}

if (typeof window.crypto.getRandomValues !== "function") {
  Object.defineProperty(window.crypto, "getRandomValues", {
    value: <T extends ArrayBufferView | null>(array: T): T => {
      if (array) {
        const view = new Uint8Array(
          array.buffer,
          array.byteOffset,
          array.byteLength,
        );
        for (let i = 0; i < view.length; i++)
          view[i] = Math.floor(Math.random() * 256);
      }
      return array;
    },
    configurable: true,
  });
}

import { vi } from "vitest";

(globalThis as any).Phaser = {
  Math: {
    Distance: {
      Between: (x1: number, y1: number, x2: number, y2: number) =>
        Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2),
    },
  },
  Input: {
    Keyboard: {
      JustDown: vi.fn(() => false),
    },
  },
};

vi.mock("phaser", () => ({
  Game: class MockGame {
    destroy = vi.fn();
    scene = {
      start: vi.fn(),
      stop: vi.fn(),
      isActive: vi.fn(() => false),
    };
    registry = {
      set: vi.fn(),
      get: vi.fn(),
      events: {
        on: vi.fn(),
      },
    };
    events = {
      on: vi.fn(),
      off: vi.fn(),
    };
  },
  Scene: class MockScene {
    public key: string;
    public registry: any;
    public cameras: any;
    public tweens: any;
    public anims: any;
    public physics: any;
    public time: any;
    public game: any;

    constructor(key: string) {
      this.key = key;
      this.anims = {
        create: vi.fn(),
        generateFrameNumbers: vi.fn(() => []),
      };
      this.physics = {
        world: {
          setBounds: vi.fn(),
        },
        add: {
          sprite: vi.fn((x, y, texture, frame) => {
            const s = (this.add as any).sprite(x, y, texture, frame);
            return s;
          }),
        },
      };
      this.time = {
        delayedCall: vi.fn(),
      };
      this.game = {
        events: {
          emit: vi.fn(),
        },
      };
      this.registry = {
        get: vi.fn(),
        events: {
          on: vi.fn(),
        },
      };
      this.cameras = {
        main: {
          width: 800,
          height: 600,
          flash: vi.fn(),
          shake: vi.fn(),
          setBackgroundColor: vi.fn(),
          setBounds: vi.fn(),
          startFollow: vi.fn(),
        },
      };
      this.tweens = {
        add: vi.fn(),
      };
    }
    load = {
      image: vi.fn(),
      spritesheet: vi.fn(),
    };
    add = {
      text: vi.fn(() => ({
        setOrigin: vi.fn().mockReturnThis(),
        setText: vi.fn().mockReturnThis(),
        setScrollFactor: vi.fn().mockReturnThis(),
        setVisible: vi.fn().mockReturnThis(),
        setDepth: vi.fn().mockReturnThis(),
        destroy: vi.fn(),
      })),
      sprite: vi.fn(() => ({
        setScale: vi.fn().mockReturnThis(),
        setFlipX: vi.fn().mockReturnThis(),
        setTexture: vi.fn().mockReturnThis(),
        setCollideWorldBounds: vi.fn().mockReturnThis(),
        setTint: vi.fn().mockReturnThis(),
        setDepth: vi.fn().mockReturnThis(),
        setPosition: vi.fn().mockReturnThis(),
        play: vi.fn().mockReturnThis(),
        stop: vi.fn().mockReturnThis(),
        texture: { key: "mock" },
        x: 0,
        y: 0,
        alpha: 1,
        body: {
          setVelocity: vi.fn().mockReturnThis(),
          setVelocityX: vi.fn().mockReturnThis(),
          setVelocityY: vi.fn().mockReturnThis(),
          velocity: {
            normalize: vi.fn().mockReturnThis(),
            scale: vi.fn().mockReturnThis(),
          },
        },
      })),
      graphics: vi.fn(() => ({
        fillGradientStyle: vi.fn().mockReturnThis(),
        fillRect: vi.fn().mockReturnThis(),
        clear: vi.fn().mockReturnThis(),
        fillStyle: vi.fn().mockReturnThis(),
        lineStyle: vi.fn().mockReturnThis(),
        strokeRect: vi.fn().mockReturnThis(),
      })),
      tileSprite: vi.fn(() => ({
        setOrigin: vi.fn().mockReturnThis(),
        setTileScale: vi.fn().mockReturnThis(),
        setAlpha: vi.fn().mockReturnThis(),
        setTint: vi.fn().mockReturnThis(),
        setDepth: vi.fn().mockReturnThis(),
      })),
      group: vi.fn(() => ({
        clear: vi.fn().mockReturnThis(),
        add: vi.fn().mockReturnThis(),
        getChildren: vi.fn(() => []),
      })),
    };
    input = {
      keyboard: {
        on: vi.fn(),
        createCursorKeys: vi.fn(() => ({
          left: { isDown: false },
          right: { isDown: false },
          up: { isDown: false },
          down: { isDown: false },
        })),
        addKeys: vi.fn(() => ({
          W: { isDown: false },
          A: { isDown: false },
          S: { isDown: false },
          D: { isDown: false },
          E: { isDown: false },
        })),
      },
    };
  },
  AUTO: "AUTO",
  Scale: {
    RESIZE: "RESIZE",
    CENTER_BOTH: "CENTER_BOTH",
  },
}));
