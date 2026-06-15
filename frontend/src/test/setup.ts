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
  },
  Scene: class MockScene {
    public key: string;
    public registry: any;
    public cameras: any;
    public tweens: any;

    constructor(key: string) {
      this.key = key;
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
        setOrigin: vi.fn(() => ({})),
        setText: vi.fn(),
      })),
      sprite: vi.fn(() => ({
        setScale: vi.fn(),
        setFlipX: vi.fn(),
        setTexture: vi.fn(),
        texture: { key: "mock" },
        x: 0,
        y: 0,
        alpha: 1,
      })),
      graphics: vi.fn(() => ({
        fillGradientStyle: vi.fn(),
        fillRect: vi.fn(),
        clear: vi.fn(),
        fillStyle: vi.fn(),
      })),
    };
    input = {
      keyboard: {
        on: vi.fn(),
      },
    };
  },
  AUTO: "AUTO",
  Scale: {
    RESIZE: "RESIZE",
    CENTER_BOTH: "CENTER_BOTH",
  },
}));
