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
    };
  },
  Scene: class MockScene {
    public key: string;
    constructor(key: string) {
      this.key = key;
    }
    load = {
      image: vi.fn(),
      spritesheet: vi.fn(),
    };
    add = {
      text: vi.fn(),
      sprite: vi.fn(() => ({
        setScale: vi.fn(),
      })),
    };
    input = {
      keyboard: {
        on: vi.fn(),
      },
    };
  },
  AUTO: "AUTO",
}));
