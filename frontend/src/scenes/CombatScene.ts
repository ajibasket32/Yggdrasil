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
    this.cameras.main.setBackgroundColor("#111813");

    const player = this.add.sprite(600, 200, "player", 0);
    player.setScale(5);
    player.setFlipX(true);

    const enemy = this.add.sprite(200, 200, "slime");
    enemy.setScale(5);

    this.tweens.add({
      targets: enemy,
      y: 190,
      duration: 1500,
      yoyo: true,
      repeat: -1,
      ease: "Sine.easeInOut",
    });
  }
}
