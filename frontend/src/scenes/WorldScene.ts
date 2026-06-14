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
    this.add.text(10, 10, "Valeria Exploration", {
      fontSize: "18px",
      color: "#ffffff",
    });

    const player = this.add.sprite(400, 300, "player", 0);
    player.setScale(2);

    this.input.keyboard?.on("keydown", (event: KeyboardEvent) => {
      switch (event.key) {
        case "ArrowLeft":
          player.x -= 16;
          break;
        case "ArrowRight":
          player.x += 16;
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
