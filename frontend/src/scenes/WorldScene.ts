import { Scene } from "phaser";

export default class WorldScene extends Scene {
  constructor() {
    super("WorldScene");
  }

  preload() {
    this.load.image("tiles", "assets/tilesets/world.png");
    this.load.spritesheet("player", "assets/characters/RPG_assets.png", {
      frameWidth: 16,
      frameHeight: 16,
    });
  }

  create() {
    this.cameras.main.setBackgroundColor("#485747");

    const player = this.add.sprite(400, 200, "player", 0);
    player.setScale(4);

    this.input.keyboard?.on("keydown", (event: KeyboardEvent) => {
      switch (event.key) {
        case "ArrowLeft":
          player.x -= 16;
          player.setFlipX(true);
          break;
        case "ArrowRight":
          player.x += 16;
          player.setFlipX(false);
          break;
        case "ArrowUp":
          player.y -= 16;
          break;
        case "ArrowDown":
          player.y += 16;
          break;
      }
    });
  }
}
