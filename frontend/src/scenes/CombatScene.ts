import { Scene } from "phaser";
import type { CombatState } from "../types/gameplay";
import tilesUrl from "../assets/tilesets/world.png";
import playerUrl from "../assets/characters/RPG_assets.png";
import slimeUrl from "../assets/monsters/slime.png";
import goblinUrl from "../assets/monsters/goblin.png";

const PLAYER_IDLE_FRAME = 10;
const COMBAT_PLAYER_TEXTURE = "combat-player";

export default class CombatScene extends Scene {
  private playerSprite!: Phaser.GameObjects.Sprite;
  private enemySprite!: Phaser.GameObjects.Sprite;
  private enemyNameText!: Phaser.GameObjects.Text;
  private enemyHpBar!: Phaser.GameObjects.Graphics;
  private playerHpBar!: Phaser.GameObjects.Graphics;
  private playerHpText!: Phaser.GameObjects.Text;

  private lastEnemyHp: number = 0;
  private lastPlayerHp: number = 0;
  private isAnimating: boolean = false;

  constructor() {
    super("CombatScene");
  }

  preload() {
    if (!this.textures.exists("slime")) this.load.image("slime", slimeUrl);
    if (!this.textures.exists("goblin")) this.load.image("goblin", goblinUrl);
    if (!this.textures.exists("boss")) this.load.image("boss", goblinUrl);
    if (!this.textures.exists("battle-bg")) {
      this.load.image("battle-bg", tilesUrl);
    }
    if (!this.textures.exists(COMBAT_PLAYER_TEXTURE)) {
      this.load.spritesheet(COMBAT_PLAYER_TEXTURE, playerUrl, {
        frameWidth: 16,
        frameHeight: 16,
      });
    }
  }

  create() {
    const bg = this.add.graphics();
    bg.fillGradientStyle(0x1e1b4b, 0x1e1b4b, 0x0f172a, 0x0f172a, 1);
    bg.fillRect(0, 0, this.cameras.main.width, this.cameras.main.height);

    const floor = this.add.tileSprite(
      0,
      this.cameras.main.height - 150,
      this.cameras.main.width,
      150,
      "battle-bg",
    );
    floor.setOrigin(0, 0);
    floor.setAlpha(0.3);
    floor.setTileScale(4);

    const centerX = this.cameras.main.width / 2;
    const centerY = this.cameras.main.height / 2;

    this.playerSprite = this.add.sprite(
      centerX + 250,
      centerY + 50,
      COMBAT_PLAYER_TEXTURE,
      PLAYER_IDLE_FRAME,
    );
    this.playerSprite.setScale(6);
    this.playerSprite.setFlipX(true);

    this.enemySprite = this.add.sprite(centerX - 250, centerY + 50, "slime");
    this.enemySprite.setScale(6);

    this.enemyNameText = this.add
      .text(centerX - 250, centerY - 150, "Enemy", {
        fontFamily: "'Press Start 2P', monospace",
        fontSize: "18px",
        color: "#f87171",
        stroke: "#000",
        strokeThickness: 4,
      })
      .setOrigin(0.5);

    this.enemyHpBar = this.add.graphics();
    this.playerHpBar = this.add.graphics();

    this.playerHpText = this.add
      .text(centerX + 250, centerY - 150, "HP: 100/100", {
        fontFamily: "'Press Start 2P', monospace",
        fontSize: "14px",
        color: "#4ade80",
        stroke: "#000",
        strokeThickness: 3,
      })
      .setOrigin(0.5);

    this.tweens.add({
      targets: this.enemySprite,
      y: centerY + 40,
      duration: 1500,
      yoyo: true,
      repeat: -1,
      ease: "Sine.easeInOut",
    });

    this.tweens.add({
      targets: this.playerSprite,
      x: centerX + 245,
      duration: 1200,
      yoyo: true,
      repeat: -1,
      ease: "Sine.easeInOut",
    });

    this.syncState();

    this.registry.events.on(
      "changedata-combatState",
      () => this.syncState(),
      this,
    );
  }

  private syncState() {
    const combat = this.registry.get("combatState") as CombatState | undefined;
    if (!combat) return;

    const player = combat.participants.find((p) => p.side === "PLAYER");
    const enemy = combat.participants.find((p) => p.side === "ENEMY");

    if (!player || !enemy) return;

    const nameLower = enemy.name.toLowerCase();
    let spriteKey = "slime";
    if (nameLower.includes("goblin")) spriteKey = "goblin";
    if (nameLower.includes("dragon") || nameLower.includes("boss"))
      spriteKey = "boss";

    if (this.enemySprite.texture.key !== spriteKey) {
      this.enemySprite.setTexture(spriteKey);
    }

    this.enemyNameText.setText(`Lv ${enemy.level ?? "?"} ${enemy.name}`);
    this.playerHpText.setText(`HP: ${player.current_hp}/${player.max_hp}`);

    this.drawHpBar(
      this.enemyHpBar,
      this.enemySprite.x - 75,
      this.enemySprite.y - 100,
      enemy.current_hp / enemy.max_hp,
      0xef4444,
    );
    this.drawHpBar(
      this.playerHpBar,
      this.playerSprite.x - 75,
      this.playerSprite.y - 100,
      player.current_hp / player.max_hp,
      0x4ade80,
    );

    if (this.lastEnemyHp > 0 && enemy.current_hp < this.lastEnemyHp) {
      this.playHitAnimation(
        this.enemySprite,
        this.lastEnemyHp - enemy.current_hp,
      );
    } else if (this.lastPlayerHp > 0 && player.current_hp < this.lastPlayerHp) {
      this.playHitAnimation(
        this.playerSprite,
        this.lastPlayerHp - player.current_hp,
      );
    } else if (combat.recent_log.length > 0 && !this.isAnimating) {
      const lastLog = combat.recent_log[combat.recent_log.length - 1];
      if (
        lastLog &&
        lastLog.text.includes(player.name) &&
        lastLog.text.includes("attack")
      ) {
        this.playAttackAnimation(this.playerSprite, this.enemySprite);
      }
    }

    this.lastEnemyHp = enemy.current_hp;
    this.lastPlayerHp = player.current_hp;
    this.updateAuditState(combat, player, enemy);
  }

  private updateAuditState(
    combat: CombatState,
    player: CombatState["participants"][number],
    enemy: CombatState["participants"][number],
  ) {
    if (!window.location.search.includes("audit=1")) return;
    window.__YGGDRASIL_AUDIT__ = {
      ...(window.__YGGDRASIL_AUDIT__ ?? {}),
      combat: {
        status: combat.status,
        playerHp: player.current_hp,
        enemyHp: enemy.current_hp,
        enemyTexture: this.enemySprite.texture.key,
        playerTexture: this.playerSprite.texture.key,
      },
    };
  }

  private drawHpBar(
    graphics: Phaser.GameObjects.Graphics,
    x: number,
    y: number,
    percent: number,
    color: number,
  ) {
    graphics.clear();
    const barWidth = 150;
    const barHeight = 12;

    graphics.fillStyle(0x000000, 0.8);
    graphics.fillRect(x, y, barWidth, barHeight);

    graphics.fillStyle(color, 1);
    graphics.fillRect(x, y, barWidth * Math.max(0, percent), barHeight);

    graphics.lineStyle(2, 0xffffff, 1);
    graphics.strokeRect(x, y, barWidth, barHeight);
  }

  private playAttackAnimation(
    attacker: Phaser.GameObjects.Sprite,
    target: Phaser.GameObjects.Sprite,
  ) {
    this.isAnimating = true;
    const startX = attacker.x;

    this.tweens.add({
      targets: attacker,
      x: target.x + (attacker.x > target.x ? 100 : -100),
      duration: 200,
      ease: "Power2",
      yoyo: true,
      onComplete: () => {
        attacker.x = startX;
        this.isAnimating = false;
      },
    });
  }

  private playHitAnimation(target: Phaser.GameObjects.Sprite, damage: number) {
    this.tweens.add({
      targets: target,
      alpha: 0,
      duration: 50,
      yoyo: true,
      repeat: 3,
      onComplete: () => {
        target.alpha = 1;
      },
    });

    this.cameras.main.shake(200, 0.02);
    this.showDamageText(target.x, target.y - 50, damage.toString());
  }

  private showDamageText(x: number, y: number, text: string) {
    const dmgText = this.add
      .text(x, y, text, {
        fontFamily: "'Press Start 2P', monospace",
        fontSize: "24px",
        color: "#ff0000",
        stroke: "#ffffff",
        strokeThickness: 4,
      })
      .setOrigin(0.5);

    this.tweens.add({
      targets: dmgText,
      y: y - 100,
      alpha: 0,
      duration: 1000,
      ease: "Cubic.out",
      onComplete: () => dmgText.destroy(),
    });
  }
}
