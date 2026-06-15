import { Scene } from "phaser";
import type { CombatState } from "../types/gameplay";

export default class CombatScene extends Scene {
  private playerSprite!: Phaser.GameObjects.Sprite;
  private enemySprite!: Phaser.GameObjects.Sprite;
  private enemyNameText!: Phaser.GameObjects.Text;
  private enemyHpBar!: Phaser.GameObjects.Graphics;
  
  private lastEnemyHp: number = 0;
  private lastPlayerHp: number = 0;

  constructor() {
    super("CombatScene");
  }

  preload() {
    this.load.image("slime", "assets/monsters/slime.png");
    this.load.image("goblin", "assets/monsters/goblin.png");
    this.load.image("boss", "assets/monsters/goblin.png"); // Fallback for missing boss sprite
    this.load.spritesheet("player", "assets/characters/RPG_assets.png", {
      frameWidth: 16,
      frameHeight: 16,
    });
  }

  create() {
    // Dynamic JRPG battle background
    const bg = this.add.graphics();
    bg.fillGradientStyle(0x1e1b4b, 0x1e1b4b, 0x0f172a, 0x0f172a, 1);
    bg.fillRect(0, 0, this.cameras.main.width, this.cameras.main.height);

    const centerX = this.cameras.main.width / 2;
    const centerY = this.cameras.main.height / 2;

    this.playerSprite = this.add.sprite(centerX + 200, centerY, "player", 0);
    this.playerSprite.setScale(5);
    this.playerSprite.setFlipX(true);

    this.enemySprite = this.add.sprite(centerX - 200, centerY, "slime");
    this.enemySprite.setScale(5);
    
    this.enemyNameText = this.add.text(centerX - 200, centerY - 120, "Enemy", {
      fontFamily: "'Press Start 2P', monospace",
      fontSize: "16px",
      color: "#f87171"
    }).setOrigin(0.5);

    this.enemyHpBar = this.add.graphics();

    // Idle animations
    this.tweens.add({
      targets: this.enemySprite,
      y: centerY - 10,
      duration: 1200,
      yoyo: true,
      repeat: -1,
      ease: "Sine.easeInOut",
    });

    this.tweens.add({
      targets: this.playerSprite,
      x: centerX + 195,
      duration: 1000,
      yoyo: true,
      repeat: -1,
      ease: "Sine.easeInOut",
    });

    // Initial sync
    this.syncState();

    // Listen to React state changes
    this.registry.events.on("changedata-combatState", this.syncState, this);
  }

  private syncState() {
    const combat = this.registry.get("combatState") as CombatState | undefined;
    if (!combat) return;

    const player = combat.participants.find((p) => p.side === "PLAYER");
    const enemy = combat.participants.find((p) => p.side === "ENEMY");

    if (!player || !enemy) return;

    // Update enemy sprite based on name (simple mapping)
    const nameLower = enemy.name.toLowerCase();
    let spriteKey = "slime";
    if (nameLower.includes("goblin")) spriteKey = "goblin";
    if (nameLower.includes("dragon") || nameLower.includes("boss")) spriteKey = "boss";
    
    if (this.enemySprite.texture.key !== spriteKey) {
       this.enemySprite.setTexture(spriteKey);
    }

    this.enemyNameText.setText(`Lv ${enemy.level ?? '?'} ${enemy.name}`);
    
    // Draw HP Bar
    this.enemyHpBar.clear();
    const barWidth = 100;
    const barHeight = 8;
    const barX = this.cameras.main.width / 2 - 200 - barWidth / 2;
    const barY = this.cameras.main.height / 2 - 90;
    
    this.enemyHpBar.fillStyle(0x000000, 0.8);
    this.enemyHpBar.fillRect(barX, barY, barWidth, barHeight);
    
    const hpPercent = enemy.max_hp > 0 ? Math.max(0, enemy.current_hp / enemy.max_hp) : 0;
    this.enemyHpBar.fillStyle(0xef4444, 1);
    this.enemyHpBar.fillRect(barX, barY, barWidth * hpPercent, barHeight);

    // Check for damage animations
    if (this.lastEnemyHp > 0 && enemy.current_hp < this.lastEnemyHp) {
      this.playHitAnimation(this.enemySprite);
    }
    if (this.lastPlayerHp > 0 && player.current_hp < this.lastPlayerHp) {
      this.playHitAnimation(this.playerSprite);
    }

    this.lastEnemyHp = enemy.current_hp;
    this.lastPlayerHp = player.current_hp;
  }

  private playHitAnimation(target: Phaser.GameObjects.Sprite) {
    this.tweens.add({
      targets: target,
      x: target.x - 20,
      alpha: 0.5,
      duration: 50,
      yoyo: true,
      repeat: 3,
      onComplete: () => {
        target.alpha = 1;
      }
    });
    this.cameras.main.shake(100, 0.01);
  }
}
