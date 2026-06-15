import { Scene } from "phaser";

export default class WorldScene extends Scene {
  private locationText!: Phaser.GameObjects.Text;
  private player!: Phaser.GameObjects.Sprite;

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
    // A nice dark gradient background for exploration
    const bg = this.add.graphics();
    bg.fillGradientStyle(0x0a0c10, 0x0a0c10, 0x1e293b, 0x1e293b, 1);
    bg.fillRect(0, 0, this.cameras.main.width, this.cameras.main.height);

    // Center area
    const centerX = this.cameras.main.width / 2;
    const centerY = this.cameras.main.height / 2;

    this.player = this.add.sprite(centerX, centerY, "player", 0);
    this.player.setScale(4);

    this.locationText = this.add.text(centerX, centerY - 80, "Unknown Location", {
      fontFamily: "'Press Start 2P', monospace",
      fontSize: "24px",
      color: "#fef08a",
      align: "center"
    }).setOrigin(0.5);

    // Initial sync
    this.updateLocation();

    // Listen for changes from React
    this.registry.events.on("changedata-locationName", this.updateLocation, this);
    
    // Add simple breathing animation
    this.tweens.add({
      targets: this.player,
      y: centerY - 5,
      duration: 1500,
      yoyo: true,
      repeat: -1,
      ease: "Sine.easeInOut"
    });
  }

  private updateLocation() {
    const locName = this.registry.get("locationName");
    if (locName && this.locationText) {
      this.locationText.setText(locName);
      
      // Flash effect on entering new area
      this.cameras.main.flash(500, 255, 255, 255);
    }
  }
}
