import { Scene } from "phaser";

export default class CombatScene extends Scene {
  constructor() {
    super("CombatScene");
  }

  preload() {
    this.load.image("slime", "assets/monsters/slime.png");
    this.load.image("goblin", "assets/monsters/goblin.png");
    this.load.spritesheet("player", "assets/characters/RPG_assets.png", {
      frameWidth: 16,
      frameHeight: 16,
    });
  }

  create() {
    this.add.text(10, 10, "Combat Encounter", {
      fontSize: "18px",
      color: "#ff0000",
    });

    const player = this.add.sprite(200, 300, "player", 0);
    player.setScale(3);

    const enemy = this.add.sprite(600, 300, "slime");
    enemy.setScale(3);
  }
}
